import math
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytz
import requests
from dotenv import load_dotenv

from libs import pulpo_api, logger

# Cargar variables de entorno
load_dotenv()
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
BASE_URL = os.getenv("BASE_URL")
BASE_URL_V2 = os.getenv("BASE_URL_V2")

api = pulpo_api.PulpoApi(BEARER_TOKEN, BASE_URL)

LOG_DIR = "./logs"
PENDING_DIR = "./pending"
PROCESSED_DIR = "./processed"
ERROR_DIR = "./error"

MAX_SECONDS_TO_SLEEP = 1

logging = logger.setup_logger()

# Mapeos para campos específicos
PRIORITY_LEVELS = {
    "Alta": "high",
    "Media": "medium",
    "Baja": "low"
}

ENTITY_TYPES = {
    "Conductores": "drivers",
    "Vehículos": "vehicles"
}

TIME_UNITS = {
    "minutos": "minutes",
    "horas": "hours",
    "días": "days"
}

def convert_date_to_iso_format(date: datetime) -> str:
    """
    Convierte una fecha en la zona horaria de Madrid al formato UTC ISO 8601 'YYYY-MM-DDTHH:MM:SS.sssZ'.
    """
    # Zona horaria de Madrid
    madrid_tz = pytz.timezone("Europe/Madrid")

    # Asegurarnos de que la fecha esté en la zona horaria de Madrid
    date_madrid = madrid_tz.localize(date)

    # Convertir la fecha a UTC
    date_utc = date_madrid.astimezone(pytz.utc)

    # Convertimos al formato ISO 8601 en UTC
    return date_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def str_to_bool(value):
    return str(value).strip().lower() in {"true", "1", "si", "sí", "s", "yes", "y"}


def is_not_empty(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def normalize_value(value):
    """
    Normaliza un valor, convirtiendo None y NaN a None.
    """
    if value is None:
        return None
    try:
        if isinstance(value, float) and math.isnan(value):
            return None
    except (ValueError, TypeError):
        pass
    
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    
    return value


def get_all_drivers():
    """
    Obtiene todos los conductores y los devuelve como una lista de diccionarios.
    """
    drivers = api.get_all_drivers()

    return [
        {
            "id": driver["id"],
            "name": driver["name"],
            "email": driver.get("email"),
            "identifier": driver.get("identifier"),
            "phone": driver.get("phone"),
            "status": driver.get("status")
        }
        for driver in drivers
    ]


def get_all_vehicles():
    """
    Obtiene todos los vehículos y los devuelve como una lista de diccionarios.
    """
    vehicles = api.get_all_vehicles()

    return [
        {
            "id": vehicle["id"],
            "registration_number": vehicle["registrationNumber"],
            "name": vehicle["name"],
            "vehicle_status_id": vehicle.get("statusId"),
            "vehicle_type": vehicle.get("type"),
            "fuel_type": vehicle.get("fuel")
        }
        for vehicle in vehicles
    ]


def get_all_entities():
    """
    Obtiene todas las entidades necesarias para el mapeo de datos.
    """
    drivers = get_all_drivers()
    logging.info(f"All drivers loaded: {len(drivers)}")

    vehicles = get_all_vehicles()
    logging.info(f"All vehicles loaded: {len(vehicles)}")

    return drivers, vehicles


def process_excel_files():
    """
    Procesa los archivos Excel en el directorio de pendientes.
    """
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
    if not os.path.exists(ERROR_DIR):
        os.makedirs(ERROR_DIR)

    files = [
        f for f in os.listdir(PENDING_DIR) if f.endswith(".xls") or f.endswith(".xlsx")
    ]
    if len(files) == 0:
        logging.info(
            "No hay archivos que procesar, verifique que hayan en la carpeta de /pending"
        )
        return

    logging.info("Archivos encontrados para procesar:")
    for idx, file in enumerate(files, start=1):
        logging.info(f"{idx} - {file}")

    logging.info("¿Deseas procesar estos archivos? (Y/N): ")
    confirmation = input().strip().upper()
    if confirmation != "Y":
        logging.info("Operación cancelada.")
        return

    logging.info(
        "¿En que modo vas a ejecutar, T: Testear para verificar posibles errores de mapeo *Recomendado si es primera vez*, P: Persistir? (T/P):"
    )
    running_type = input().strip().upper()
    if running_type not in ["T", "P"]:
        logging.info("Operación cancelada. Tipo de ejecución inválido.")
        return

    persist_data = running_type == "P"

    for file in files:
        try:
            file_path = os.path.join(PENDING_DIR, file)
            
            # Leer todas las hojas disponibles en el archivo Excel
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            logging.info(f"\nArchivo: {file}")
            logging.info(f"El archivo contiene {len(sheet_names)} hoja(s): {', '.join(sheet_names)}")
            
            # Obtener todas las entidades necesarias (una sola vez por archivo)
            drivers, vehicles = get_all_entities()
            
            # Procesar cada hoja del archivo
            for sheet_index, sheet_name in enumerate(sheet_names):
                logging.info(f"\n{'=' * 50}")
                logging.info(f"Hoja {sheet_index + 1}/{len(sheet_names)}: {sheet_name}")
                
                # Preguntar al usuario si desea procesar esta hoja
                logging.info(f"¿Deseas procesar la hoja '{sheet_name}'? (Y/N): ")
                sheet_confirmation = input().strip().upper()
                if sheet_confirmation != "Y":
                    logging.info(f"Omitiendo hoja '{sheet_name}'.")
                    continue
                
                # Cargar la hoja específica
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                logging.info(f"Procesando hoja: {sheet_name} ({len(df)} filas)")
                
                # Comprobar si la hoja está vacía o no tiene las columnas esperadas
                if df.empty:
                    logging.info(f"La hoja '{sheet_name}' está vacía. Omitiendo.")
                    continue

                # Procesar cada fila del archivo
                processed_rows = []
                mapping_error_rows = []  # Errores durante el mapeo
                processing_error_rows = []  # Errores durante el procesamiento con el endpoint

                for index, row in df.iterrows():
                    try:
                        # Mapear los datos de la fila a un objeto de recordatorio
                        reminder_data = try_to_map(row, drivers, vehicles)

                        if persist_data:
                            try:
                                # Crear el recordatorio
                                reminder_id = create_reminder(reminder_data)
                                reminder_data["id"] = reminder_id
                                logging.info(
                                    f"Recordatorio creado correctamente: {reminder_id}"
                                )
                                
                                processed_rows.append(
                                    {
                                        "id": index + 2,  # +2 para compensar el encabezado y que excel comienza en 1
                                        "data": reminder_data,
                                        "original_data": row.to_dict(),  # Guardar datos originales para el reporte
                                        "sheet_name": sheet_name  # Guardar el nombre de la hoja
                                    }
                                )
                            except Exception as endpoint_error:
                                # Error al procesar con el endpoint
                                logging.error(
                                    f"Error al crear el recordatorio para la fila {index + 2}: {str(endpoint_error)}"
                                )
                                processing_error_rows.append(
                                    {
                                        "id": index + 2,
                                        "error": str(endpoint_error),
                                        "data": row.to_dict(),
                                        "mapped_data": reminder_data,
                                        "sheet_name": sheet_name
                                    }
                                )
                        else:
                            logging.info(
                                f"Datos del recordatorio mapeados correctamente (modo prueba): {reminder_data}"
                            )
                            processed_rows.append(
                                {
                                    "id": index + 2,
                                    "data": reminder_data,
                                    "original_data": row.to_dict(),  # Guardar datos originales para el reporte
                                    "sheet_name": sheet_name
                                }
                            )

                        time.sleep(MAX_SECONDS_TO_SLEEP)

                    except Exception as mapping_error:
                        # Error durante el mapeo
                        logging.error(
                            f"Error al mapear la fila {index + 2}: {str(mapping_error)}"
                        )
                        mapping_error_rows.append(
                            {
                                "id": index + 2,
                                "error": str(mapping_error),
                                "data": row.to_dict(),
                                "sheet_name": sheet_name
                            }
                        )

                # Guardar los resultados para esta hoja
                sheet_suffix = f"_{sheet_name}"
                save_results(file + sheet_suffix, processed_rows, mapping_error_rows, processing_error_rows)
                
                logging.info(f"Hoja '{sheet_name}' procesada.")
                logging.info(f"{'=' * 50}")
                
                # Preguntar si el usuario desea continuar con la siguiente hoja
                if sheet_index < len(sheet_names) - 1:
                    logging.info("¿Deseas continuar con la siguiente hoja? (Y/N): ")
                    continue_confirmation = input().strip().upper()
                    if continue_confirmation != "Y":
                        logging.info("Procesamiento de hojas detenido por el usuario.")
                        break

            # Ya no se mueve el archivo original, permanece en la carpeta pending
            logging.info(f"Archivo {file} procesado. El archivo original permanece en la carpeta pending.")

        except Exception as e:
            logging.error(f"Error al procesar el archivo {file}: {str(e)}")


def try_to_map(row, drivers, vehicles):
    """
    Mapea una fila de datos a un objeto de recordatorio según la estructura requerida.
    """
    if not any(row.to_dict().values()):
        raise ValueError("Fila vacía.")

    # Obtener el nombre de la tarea
    name = normalize_value(row.get("Nombre de la Tarea*"))
    if not is_not_empty(name):
        raise ValueError("Nombre de la tarea no especificado.")

    # Obtener la descripción
    description = normalize_value(row.get("Descripción", ""))

    # Obtener la fecha límite combinando fecha y hora
    date_str = normalize_value(row.get("Fecha Vto Tarea*"))
    if not is_not_empty(date_str):
        raise ValueError("Fecha de tarea no especificada.")
    
    time_str = normalize_value(row.get("Hora*", "00:00"))
    
    try:
        if isinstance(date_str, datetime):
            task_date = date_str
        else:
            # Primero intentar formato DD/MM/YYYY
            try:
                task_date = datetime.strptime(str(date_str), "%d/%m/%Y")
            except ValueError:
                # Si falla, intentar formato YYYY-MM-DD
                task_date = datetime.strptime(str(date_str), "%Y-%m-%d")
        
        # Añadir la hora
        if time_str:
            if isinstance(time_str, str):
                hours, minutes = map(int, time_str.split(':'))
                task_date = task_date.replace(hour=hours, minute=minutes)
            elif isinstance(time_str, datetime):
                task_date = task_date.replace(hour=time_str.hour, minute=time_str.minute)
        
        limit_date_iso = convert_date_to_iso_format(task_date)
    except Exception as e:
        raise ValueError(f"Formato de fecha o hora inválido: {str(e)}")
    
    # Obtener la prioridad
    priority_name = normalize_value(row.get("Prioridad*", "Media"))
    priority_id = PRIORITY_LEVELS.get(priority_name, "medium")
    
    # Determinar el tipo de entidad
    entity_type_name = normalize_value(row.get("Opciones", ""))
    entity_type = ENTITY_TYPES.get(entity_type_name, "drivers")
    
    # Obtener la entidad (conductor o vehículo)
    entity_name = normalize_value(row.get("Opciones", ""))
    if not is_not_empty(entity_name):
        raise ValueError("Opciones no especificado.")
    
    if entity_type == "drivers":
        entity = get_driver_by_name(entity_name, drivers)
        if not entity:
            raise ValueError(f"No se encontró el conductor: {entity_name}")
    else:
        entity = get_vehicle_by_name(entity_name, vehicles)
        if not entity:
            raise ValueError(f"No se encontró el vehículo: {entity_name}")
    
    entity_id = entity["id"]
    
    # Obtener el responsable
    responsible_name = normalize_value(row.get("Responsable de la Tarea", entity_name))
    responsible = get_driver_by_name(responsible_name, drivers)
    if not responsible:
        raise ValueError(f"No se encontró el responsable: {responsible_name}")
    
    responsible_id = responsible["id"]
    
    # Configurar las notificaciones
    notifications = []
    
    reminder_type = normalize_value(row.get("Recordatorio", ""))
    if is_not_empty(reminder_type):
        notification_value = normalize_value(row.get("valor*", 1))
        notification_unit_name = normalize_value(row.get("Unidad de tiempo de notificación", "horas"))
        notification_unit = TIME_UNITS.get(notification_unit_name, "hours")
        
        # Crear notificaciones según el tipo
        if "Email" in reminder_type or "email" in reminder_type.lower():
            notifications.append({
                "typeId": "email",
                "amount": notification_value,
                "unit": notification_unit
            })
        
        if "Notificación" in reminder_type or "notificacion" in reminder_type.lower() or "push" in reminder_type.lower():
            notifications.append({
                "typeId": "push",
                "amount": notification_value,
                "unit": notification_unit
            })
    
    # Construir el objeto de recordatorio
    reminder_data = {
        "name": name,
        "description": description,
        "limitDate": limit_date_iso,
        "priorityId": priority_id,
        "notifications": notifications,
        "userIds": [responsible_id],
        "entityType": entity_type,
        "entityId": entity_id,
        "responsibleId": responsible_id
    }
    
    return reminder_data


def get_driver_by_name(name, drivers):
    """
    Busca un conductor por su nombre.
    """
    if not name:
        return None
    
    name_lower = name.lower()
    
    # Búsqueda exacta
    for driver in drivers:
        if driver["name"].lower() == name_lower:
            return driver
    
    # Búsqueda parcial
    for driver in drivers:
        if name_lower in driver["name"].lower():
            return driver
    
    return None


def get_vehicle_by_name(name, vehicles):
    """
    Busca un vehículo por su nombre o matrícula.
    """
    if not name:
        return None
    
    name_lower = name.lower()
    
    # Búsqueda por nombre exacto
    for vehicle in vehicles:
        if vehicle["name"].lower() == name_lower:
            return vehicle
    
    # Búsqueda por matrícula
    for vehicle in vehicles:
        if vehicle["registration_number"].lower() == name_lower:
            return vehicle
    
    # Búsqueda parcial
    for vehicle in vehicles:
        if name_lower in vehicle["name"].lower() or name_lower in vehicle["registration_number"].lower():
            return vehicle
    
    return None


def create_reminder(data):
    """
    Crea un recordatorio con los datos proporcionados.
    """
    # Construir la URL del endpoint
    url = f"{BASE_URL_V2}/reminders"
    
    # Configurar los headers con el token de autenticación
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Realizar la petición POST al endpoint
    response = requests.post(url, json=data, headers=headers)
    
    # Verificar la respuesta
    if response.status_code != 201 and response.status_code != 200:
        raise ValueError(f"Error al crear el recordatorio: {response.text}")
    
    # Devolver el ID del recordatorio creado
    response_data = response.json()
    if "id" not in response_data:
        raise ValueError(f"Error al crear el recordatorio: el ID no está en la respuesta")
    
    return response_data["id"]


def export_errors_to_excel(file_name, error_rows, error_type):
    """
    Exporta los errores a un archivo Excel.
    
    Args:
        file_name: Nombre del archivo original
        error_rows: Lista de filas con errores
        error_type: Tipo de error ('mapping' o 'processing')
    
    Returns:
        Nombre del archivo generado o None si no hay errores
    """
    if not error_rows:
        return None  # No hay errores para exportar
    
    # Asegurarse de que el directorio de errores existe
    if not os.path.exists(ERROR_DIR):
        os.makedirs(ERROR_DIR)
    
    # Generar nombre de archivo para el reporte de errores
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Determinar el sufijo según el tipo de error
    suffix = "_mapeo.xlsx" if error_type == "mapping" else "_errors.xlsx"
    
    error_file_name = os.path.join(ERROR_DIR, f"{timestamp}_{os.path.splitext(file_name)[0]}{suffix}")
    
    # Preparar los datos para el archivo Excel - Usar los datos originales
    error_data = []
    for error_row in error_rows:
        # Usar los datos originales de la fila del Excel
        row_data = error_row["data"].copy()  # Los datos originales están en "data"
        
        # Añadir información sobre el error
        row_data["Error"] = error_row["error"]
        row_data["Fila"] = error_row["id"]
        
        # Añadir el nombre de la hoja si está disponible
        if "sheet_name" in error_row:
            row_data["Hoja"] = error_row["sheet_name"]
        
        # Si es un error de procesamiento y queremos añadir alguna info del JSON mapeado
        if error_type == "processing" and "mapped_data" in error_row:
            # Añadir solo el ID del recordatorio si existe (para referencia)
            if "id" in error_row["mapped_data"]:
                row_data["ID_Recordatorio"] = error_row["mapped_data"]["id"]
            
            # Opcionalmente podríamos añadir otra info clave del mapeo
            # row_data["JSON_Procesado"] = str(error_row["mapped_data"])
                
        error_data.append(row_data)
    
    # Crear el DataFrame y guardar como Excel
    error_df = pd.DataFrame(error_data)
    error_df.to_excel(error_file_name, index=False)
    
    logging.info(f"Archivo de errores {'de mapeo' if error_type == 'mapping' else 'de procesamiento'} creado: {error_file_name}")
    return error_file_name


def export_processed_to_excel(file_name, processed_rows):
    """
    Exporta las filas procesadas exitosamente a un archivo Excel en la carpeta processed.
    
    Args:
        file_name: Nombre del archivo original
        processed_rows: Lista de filas procesadas exitosamente
    
    Returns:
        Nombre del archivo generado o None si no hay filas procesadas
    """
    if not processed_rows:
        return None  # No hay filas procesadas para exportar
    
    # Asegurarse de que el directorio processed existe
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
    
    # Generar nombre de archivo para el reporte de filas procesadas
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    processed_file_name = os.path.join(PROCESSED_DIR, f"{timestamp}_{os.path.splitext(file_name)[0]}_processed.xlsx")
    
    # Preparar los datos para el archivo Excel - Usar los datos originales
    processed_data = []
    for row in processed_rows:
        # Usar los datos originales de la fila del Excel
        if "original_data" in row and row["original_data"]:
            row_data = row["original_data"].copy()
        else:
            # Fallback a los datos procesados si no hay originales
            row_data = {}
            
        # Añadir información adicional
        row_data["Fila_Original"] = row["id"]
        
        # Añadir el ID del recordatorio creado (si existe)
        if "data" in row and "id" in row["data"]:
            row_data["ID_Recordatorio"] = row["data"]["id"]
        
        # Añadir el nombre de la hoja si está disponible
        if "sheet_name" in row:
            row_data["Hoja"] = row["sheet_name"]
            
        processed_data.append(row_data)
    
    # Crear el DataFrame y guardar como Excel
    processed_df = pd.DataFrame(processed_data)
    processed_df.to_excel(processed_file_name, index=False)
    
    logging.info(f"Archivo de registros procesados creado: {processed_file_name}")
    return processed_file_name


def save_results(file, processed_rows, mapping_error_rows, processing_error_rows=None):
    """
    Guarda los resultados del procesamiento en un archivo JSON y exporta los errores a archivos Excel.
    """
    import json
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    results = {
        "file": file,
        "timestamp": timestamp,
        "processed": len(processed_rows),
        "mapping_errors": len(mapping_error_rows),
        "processing_errors": len(processing_error_rows) if processing_error_rows else 0,
        "processed_rows": processed_rows,
        "mapping_error_rows": mapping_error_rows,
        "processing_error_rows": processing_error_rows if processing_error_rows else [],
    }
    
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Guardar resultados en JSON
    with open(os.path.join(LOG_DIR, f"{timestamp}_{file}.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Exportar errores de mapeo a Excel si hay errores
    mapping_error_file = None
    if mapping_error_rows:
        mapping_error_file = export_errors_to_excel(file, mapping_error_rows, "mapping")
    
    # Exportar errores de procesamiento a Excel si hay errores
    processing_error_file = None
    if processing_error_rows and len(processing_error_rows) > 0:
        processing_error_file = export_errors_to_excel(file, processing_error_rows, "processing")
    
    # Exportar filas procesadas exitosamente a Excel
    processed_file = None
    if processed_rows:
        processed_file = export_processed_to_excel(file, processed_rows)
    
    logging.info(
        f"Procesamiento completado. Procesados: {len(processed_rows)}, "
        f"Errores de mapeo: {len(mapping_error_rows)}, "
        f"Errores de procesamiento: {len(processing_error_rows) if processing_error_rows else 0}"
    )
    
    if mapping_error_file:
        logging.info(f"Los errores de mapeo se han exportado a: {mapping_error_file}")
    
    if processing_error_file:
        logging.info(f"Los errores de procesamiento se han exportado a: {processing_error_file}")
    
    if processed_file:
        logging.info(f"Los registros procesados se han exportado a: {processed_file}")


if __name__ == "__main__":
    process_excel_files()