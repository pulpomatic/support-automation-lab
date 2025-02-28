import math
import os
import time

# import traceback
from datetime import datetime
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

api = pulpo_api.PulpoApi(BEARER_TOKEN, BASE_URL)

LOG_DIR = "./logs"
PENDING_DIR = "./pending"
PROCESSED_DIR = "./processed"
ERROR_DIR = "./error"

MAX_SECONDS_TO_SLEEP = 1

logging = logger.setup_logger()

# Listas de referencia
TAX_TYPES = {"Porcentaje": "PERCENTAGE", "Moneda": "CURRENCY"}
PAYMENT_FREQUENCIES = {
    "Diario": "day",
    "Semanal": "week",
    "Mensual": "month",
    "Anual": "year",
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
    return str(value).strip().lower() in {"true", "1"}


def is_not_empty(str: str) -> bool:
    return bool(str) or str != ""


def parse_percentage(value):
    """
    Si value es un valor decimal, es decir que es menor que 1 y mayor que 0
    entonces que lo multiplique por 100, de lo contrario que no haga nada

    Ejemplo: 0,21 -> 21
    """
    if value is None:
        return 0

    value = float(value)
    if value is not None and 0 < value < 1:
        return value * 100

    return value


def normalize_value(value):
    if value is None:
        return None
    try:
        if math.isnan(float(value)):  # Convierte a float y verifica NaN
            return None
    except (
        ValueError,
        TypeError,
    ):  # Si no se puede convertir, no es un número (ej. strings)
        pass
    return value  # Retorna el valor original si no es None o NaN


def clean_registration_number(registration_number):
    import re

    return re.sub(r"[^a-zA-Z0-9]", "", registration_number)


def validate_total_calculations(subtotal, tax_type, tax, total):
    if subtotal is None:
        return

    total_calculated = subtotal

    if tax_type == "PERCENTAGE":
        total_calculated *= 1 + tax / 100
    elif tax_type == "CURRENCY":
        total_calculated += tax

    check_difference = total_calculated - total
    if abs(check_difference) > Decimal("0.0001"):
        raise ValueError(
            f"Diferencia en el cálculo del total. Calculado {total_calculated}, Total {total}."
        )


def get_all_vehicles():
    vehicles = api.get_all_vehicles()

    return [
        {
            "id": vehicle["id"],
            "registration_number_v1": vehicle["registrationNumber"],
            "registration_number": clean_registration_number(
                vehicle["registrationNumber"]
            ),
            "name": vehicle["name"],
            "vehicle_status_id": vehicle["statusId"],
            "vehicle_type": vehicle["type"],
            "fuel_type": vehicle["fuel"],
            "segments": vehicle["segments"],
        }
        for vehicle in vehicles
    ]


def get_all_entities():
    vehicles = get_all_vehicles()
    logging.info(f"All vehicles loaded {len(vehicles)}")

    suppliers = api.get_all_suppliers()
    logging.info(f"All suppliers loaded {len(suppliers)}")

    vehicle_types = api.get_all_catalogs("VEHICLES_TYPES")
    logging.info(f"All vehicle types loaded {len(vehicle_types)}")

    vehicle_property_types = api.get_all_catalogs("PROPERTIES_TYPES")
    logging.info(f"All vehicle property types loaded {len(vehicle_property_types)}")

    vehicle_fuel_types = api.get_all_catalogs("FUEL_TYPES")
    logging.info(f"All vehicle fuel types loaded {len(vehicle_fuel_types)}")

    expense_types = api.get_all_catalogs("EXPENSES_TYPES")
    logging.info(f"All expense types loaded {len(expense_types)}")

    return (
        vehicles,
        suppliers,
        vehicle_types,
        vehicle_property_types,
        vehicle_fuel_types,
        expense_types,
    )


# Función para procesar archivos
def process_excel_files():
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
        logging.info("Opción incorrecta, operación cancelada.")
        return

    logging.info("Modo Prueba" if running_type == "T" else "Modo Persistir")
    # Obtenemos los catálogos
    (
        vehicles,
        suppliers,
        vehicle_types,
        vehicle_property_types,
        vehicle_fuel_types,
        expense_types,
    ) = get_all_entities()

    for idx, file_name in enumerate(files, start=1):
        logging.info(f"({idx}/{len(files)}) Procesando archivo: {file_name}")
        file_path = os.path.join(PENDING_DIR, file_name)
        df = pd.read_excel(
            file_path, sheet_name=0, dtype=str, keep_default_na=False, skiprows=1
        )
        df = df.replace("", None)
        # Ordenar el DataFrame por `Fecha fin` de forma ascendente
        # La importancia es debido a que debemos procesar de primero los más antiguos
        df["Fecha fin"] = pd.to_datetime(
            df["Fecha fin"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
        )
        df = df.sort_values(by="Fecha fin", ascending=True)
        processed_rows, error_rows = [], []
        total_rows = len(df)

        for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
            try:
                (
                    vehicle_id,
                    vehicle_renting_mapped_data,
                    scheduled_expense_mapped_data,
                ) = try_to_map(
                    row.to_dict(),
                    vehicles,
                    suppliers,
                    vehicle_types,
                    vehicle_property_types,
                    vehicle_fuel_types,
                    expense_types,
                )

                if running_type == "T":
                    logging.info(
                        "Procesando en modo test, omitiendo envío del vehículo"
                    )
                    print(vehicle_id, vehicle_renting_mapped_data)
                else:
                    update_vehicle(vehicle_id, vehicle_renting_mapped_data)

                logging.info(
                    f"({row_idx}/{total_rows}) Vehículo {vehicle_id} actualizado. Esperando {MAX_SECONDS_TO_SLEEP} segundos para continuar."
                )

                if scheduled_expense_mapped_data is not None:
                    if running_type == "T":
                        logging.info(
                            "Procesando en modo test, omitiendo envío del gasto programado"
                        )
                        print(scheduled_expense_mapped_data)
                    else:
                        create_scheduled_expense(scheduled_expense_mapped_data)

                    logging.info(f"({row_idx}/{total_rows}) Gasto programado creado.")

                if running_type == "P":
                    logging.info(
                        f"Esperando {MAX_SECONDS_TO_SLEEP} segundos para continuar."
                    )
                    time.sleep(MAX_SECONDS_TO_SLEEP)
                processed_rows.append(vehicle_renting_mapped_data)
            except Exception as e:
                row["map_error"] = str(e)
                logging.error(f"Error encontrado, {str(e)}")
                error_rows.append(row)

        save_results(file, processed_rows, error_rows)


# Función de mapeo
def try_to_map(
    row,
    vehicles,
    suppliers,
    vehicle_types,
    vehicle_property_types,
    vehicle_fuel_types,
    expense_types,
):
    vehicle = get_vehicle(row["Matrícula"], vehicles)

    if row.get("Fecha inicio") is None or str(row.get("Fecha inicio")) == "NaT":
        raise ValueError("Fecha inicio es obligatorio o tiene un formato incorrecto")

    start_date = pd.to_datetime(row["Fecha inicio"], format="%Y-%m-%d %H:%M:%S")

    if str(row.get("Fecha fin")) == "NaT":
        raise ValueError("Fecha fin es obligatorio o tiene un formato incorrecto")

    end_date = row["Fecha fin"]

    subtotalScheduledFee = None
    if row["Cuota recurrente de empresa €"] is not None:
        if row["Cuota recurrente de empleado €"] is not None:
            subtotalScheduledFee = float(row["Cuota recurrente de empleado €"]) + float(
                row["Cuota recurrente de empresa €"]
            )
        else:
            subtotalScheduledFee = float(row["Cuota recurrente de empresa €"])

    scheduledFeeTaxType = TAX_TYPES.get(
        row.get("Cuota recurrente tipo de impuesto"), "PERCENTAGE"
    )

    initialFeeTaxType = TAX_TYPES.get(
        row.get("Cuota inicial tipo de impuesto"), "PERCENTAGE"
    )
    vehicle_renting_mapped_data = {
        # Vehicle
        "name": vehicle["name"],
        "registrationNumber": vehicle["registration_number_v1"],
        "vehicleStatusId": vehicle["vehicle_status_id"],
        "vehicleTypeId": get_catalog_id(vehicle["vehicle_type"], vehicle_types),
        "propertyTypeId": get_catalog_id(row["Propiedad"], vehicle_property_types),
        "fuelTypeId": get_catalog_id(vehicle["fuel_type"], vehicle_fuel_types),
        "segments": [
            segment.get("id") for segment in vehicle["segments"] if "id" in segment
        ],
        # Renting y Leasing
        "vehicleProperties": {
            "referenceCode": row.get("Referencia"),
            "supplierId": get_supplier_id(row["Proveedor"], suppliers),
            "startDate": convert_date_to_iso_format(start_date),
            "endDate": convert_date_to_iso_format(end_date),
            "initialOdometer": (
                float(row["Odómetro inicial"])
                if row["Odómetro inicial"] is not None
                else None
            ),
            "odometerContracted": (
                float(row["Kilometraje contratado"])
                if row["Kilometraje contratado"] is not None
                else None
            ),
            "odometerPerYear": (
                float(row["Kilometraje por año"])
                if row["Kilometraje por año"] is not None
                else None
            ),
            # Cuota Inicial
            "subtotalInitialFee": (
                float(row["Cuota inicial subtotal €"])
                if row.get("Cuota inicial subtotal €") is not None
                else None
            ),
            "initialFeeTaxType": initialFeeTaxType,
            "initialFeeTax": (
                parse_percentage(row["Cuota inicial impuesto"])
                if row.get("Cuota inicial impuesto") is not None
                and initialFeeTaxType == "PERCENTAGE"
                else row.get("Cuota inicial impuesto")
            ),
            "initialFeeTotalAmount": (
                float(row["Cuota inicial total €"])
                if row.get("Cuota inicial total €") is not None
                else None
            ),
            # Cuota Recurrente
            "employeeFee": (
                float(row["Cuota recurrente de empleado €"])
                if row["Cuota recurrente de empleado €"] is not None
                else None
            ),
            "subtotalScheduledFee": subtotalScheduledFee,
            "scheduledFeeTaxType": scheduledFeeTaxType,
            "scheduledFeeTax": (
                parse_percentage(row["Cuota recurrente impuesto"])
                if row.get("Cuota recurrente impuesto") is not None
                and scheduledFeeTaxType == "PERCENTAGE"
                else row.get("Cuota recurrente impuesto")
            ),
            "scheduledFeeTotalAmount": (
                float(row["Cuota recurrente total €"])
                if row.get("Cuota recurrente total €") is not None
                else None
            ),
            "bonificationByOdometer": (
                float(row["Bonificación por km no recorrido"])
                if row.get("Bonificación por km no recorrido") is not None
                else None
            ),
            "penaltyByOdometer": (
                float(row["Penalización por km excedido"])
                if row.get("Penalización por km excedido") is not None
                else None
            ),
            "customFieldsData": {
                "cf_property_permanencia_minima": (
                    convert_date_to_iso_format(
                        pd.to_datetime(
                            row["Permanencia mínima"], format="%Y-%m-%d %H:%M:%S"
                        )
                    )
                    if row.get("Permanencia mínima") is not None
                    else None
                ),
                "cf_property_tipo_de_contrato": (
                    row["Tipo de contrato"].capitalize()
                    if row["Tipo de contrato"] is not None
                    else None
                ),
                "cf_property_tipo_de_pago": (
                    row["Tipo de pago"].capitalize()
                    if row["Tipo de pago"] is not None
                    else None
                ),
                "cf_property_valor_del_vehiculo": (
                    float(row["Valor del vehículo"])
                    if row.get("Valor del vehículo") is not None
                    else None
                ),
                "cf_property_valor_residual": (
                    float(row["Valor residual"])
                    if row.get("Valor residual") is not None
                    else None
                ),
                "cf_property_vehiculo_de_sustitucion": str_to_bool(
                    row.get("Vehículo de sustitución", "FALSE")
                ),
                "cf_property_seguro": str_to_bool(row.get("Seguro", "FALSE")),
                "cf_property_servicio_de_telemetria": str_to_bool(
                    row.get("Servicio de telemetría", "FALSE")
                ),
                "cf_property_mantenimiento_preventivo": str_to_bool(
                    row.get("Mantenimiento preventivo", "FALSE")
                ),
                "cf_property_mantenimiento_correctivo": str_to_bool(
                    row.get("Mantenimiento correctivo", "FALSE")
                ),
                "cf_property_asistencia_de_carretera": str_to_bool(
                    row.get("Asistencia de carretera", "FALSE")
                ),
                "cf_property_gestion_de_tramites": str_to_bool(
                    row.get("Gestión de trámites", "FALSE")
                ),
                "cf_property_gestion_de_multas": str_to_bool(
                    row.get("Gestión de multas", "FALSE")
                ),
                "cf_property_rotulacion": str_to_bool(row.get("Rotulación", "FALSE")),
                "cf_property_equipamiento": str_to_bool(
                    row.get("Equipamiento", "FALSE")
                ),
            },
        },
    }

    vehicleProperties = vehicle_renting_mapped_data["vehicleProperties"]

    validate_total_calculations(
        vehicleProperties["subtotalInitialFee"],
        vehicleProperties["initialFeeTaxType"],
        vehicleProperties["initialFeeTax"],
        vehicleProperties["initialFeeTotalAmount"],
    )

    validate_total_calculations(
        subtotalScheduledFee,
        vehicleProperties["scheduledFeeTaxType"],
        vehicleProperties["scheduledFeeTax"],
        vehicleProperties["scheduledFeeTotalAmount"],
    )

    scheduled_expense_mapped_data = None

    if str_to_bool(row.get("crear gasto programado", "FALSE")):
        scheduled_expense_mapped_data = {
            "name": f"{row['Matrícula']} - Renting",
            "expenseTypeId": get_catalog_id("Renting", expense_types),
            "subtotal": vehicleProperties["subtotalScheduledFee"],
            "taxType": vehicleProperties["scheduledFeeTaxType"],
            "tax": vehicleProperties["scheduledFeeTax"],
            "discountType": "PERCENTAGE",
            "discount": 0,
            "total": vehicleProperties["scheduledFeeTotalAmount"],
            "segments": [],
            "userId": None,
            "vehicleId": vehicle["id"],
            "paymentMethodId": None,
            "supplierId": vehicleProperties["supplierId"],
            "locationId": None,
            "startDate": convert_date_to_iso_format(
                start_date + pd.Timedelta(hours=12)
            ),
            "endDate": convert_date_to_iso_format(end_date + pd.Timedelta(hours=12)),
            "frecuency": PAYMENT_FREQUENCIES[row["Tipo de pago"]],
            "customFieldsMetadata": {},
        }

    return vehicle["id"], vehicle_renting_mapped_data, scheduled_expense_mapped_data


# Función para obtener vehicle ID
def get_vehicle(registration_number, vehicles):
    cleaned_registration_number = (
        clean_registration_number(registration_number)
        if is_not_empty(registration_number)
        else None
    )

    vehicle = next(
        (
            item
            for item in vehicles
            if cleaned_registration_number is not None
            and item["registration_number"] == cleaned_registration_number
        ),
        None,
    )

    if vehicle is None:
        raise ValueError(f"Vehículo '{registration_number}' no encontrado")

    return vehicle


# Función para obtener supplier ID
def get_supplier_id(supplier_name, suppliers):
    supplier = next(
        (
            item
            for item in suppliers
            if supplier_name is not None
            and item["name"].lower() == supplier_name.lower()
        ),
        None,
    )

    if supplier is None:
        raise ValueError(f"Proveedor '{supplier_name}' no encontrado")

    return supplier["id"]


# Función para obtener catálogo ID
def get_catalog_id(catalog_name, catalogs):
    catalog = next(
        (
            item
            for item in catalogs
            if catalog_name is not None and item["name"].lower() == catalog_name.lower()
        ),
        None,
    )

    if catalog is None:
        raise ValueError(f"Catálogo '{catalog_name}' no encontrado")

    return catalog["id"]


# Función para actualizar el vehículo por su ID
def update_vehicle(vehicle_id, data):
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
    }
    params = {}
    response = requests.put(
        f"{BASE_URL}/vehicles/{vehicle_id}", json=data, headers=headers, params=params
    )
    if response.status_code != 200:
        logging.info(
            f"Actualizar vehículo, error code {response.status_code}, {response.text}"
        )
        raise ValueError(f"Error: {response.status_code} {response.text}")


# Función para crear el gasto programado
def create_scheduled_expense(data):
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
    }
    params = {}
    response = requests.post(
        f"{BASE_URL}/scheduled-expenses", json=data, headers=headers, params=params
    )
    if response.status_code != 201:
        logging.info(
            f"Crear gasto programado, error code {response.status_code}, {response.text}"
        )
        raise ValueError(f"Error: {response.status_code} {response.text}")


# Función para guardar resultados
def save_results(file, processed_rows, error_rows):
    file_name, _ = os.path.splitext(file)

    if processed_rows:
        processed_path = os.path.join(PROCESSED_DIR, f"{file_name}_processed.xlsx")
        pd.DataFrame(processed_rows).to_excel(processed_path, index=False)
        logging.info(f"Archivo procesado guardado en {processed_path}")

    if error_rows:
        error_path = os.path.join(ERROR_DIR, f"{file_name}_map_error.xlsx")
        pd.DataFrame(error_rows).to_excel(error_path, index=False)
        logging.warning(f"Errores guardados en {error_path}")


# Función principal
if __name__ == "__main__":
    process_excel_files()
