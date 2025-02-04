import logging
import math
import os
import requests
import time

# import traceback
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
BASE_URL = os.getenv("BASE_URL")

LOG_DIR = "./logs"
PENDING_DIR = "./pending"
PROCESSED_DIR = "./processed"
ERROR_DIR = "./error"

MAX_SECONDS_TO_SLEEP = 2

# Configuración de logging
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logging.basicConfig(
    filename=os.path.join(
        LOG_DIR, f"process_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    ),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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
    Convierte una fecha al formato ISO 8601 'YYYY-MM-DDTHH:MM:SS.sssZ'.
    """
    # Convertimos al formato ISO 8601
    return date.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def str_to_bool(value):
    return str(value).strip().lower() == "true"


def is_not_empty(str: str) -> bool:
    return bool(str) or str != ""


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


def normalize_dict(data):
    return {key: normalize_value(value) for key, value in data.items()}


def clean_registration_number(registration_number):
    import re

    return re.sub(r"[^a-zA-Z0-9]", "", registration_number)


def validate_total_calculations(subtotal, tax_type, tax, total):
    if subtotal is not None:
        total_calculated = subtotal

        if tax_type == "PERCENTAGE":
            total_calculated *= 1 + tax / 100
        elif tax_type == "CURRENCY":
            total_calculated += tax

        if round(total_calculated, 4) != round(total, 4):
            raise ValueError(
                f"Diferencia en el cálculo del total. Calculado {total_calculated}, Total {total}."
            )


def get_all_vehicles():
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {
        "skip": 0,
        "take": 0,
    }
    response = requests.get(f"{BASE_URL}/vehicles", headers=headers, params=params)
    if response.status_code != 200:
        raise ValueError(
            f"Error al obtener vehículos, el estatus devuelto {response.status_code}"
        )
    response_json = response.json()
    vehicles = response_json["vehicles"]
    if len(vehicles) == 0:
        raise ValueError("No hay vehículos asociados a la cuenta")

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
        }
        for vehicle in vehicles
    ]


def get_all_suppliers():
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    params = {
        "collectionType": "supplier",
        "skip": 0,
        "take": 0,
    }
    response = requests.get(f"{BASE_URL}/suppliers", headers=headers, params=params)
    if response.status_code != 200:
        raise ValueError(
            f"Error al obtener proveedores, el estatus devuelto {response.status_code}"
        )
    response_json = response.json()
    suppliers = response_json["suppliers"]
    if len(suppliers) == 0:
        raise ValueError("No hay proveedores asociados a la cuenta")

    return [
        {
            "id": supplier["id"],
            "name": supplier["name"],
        }
        for supplier in suppliers
    ]


def get_all_catalogs(catalog_type):
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    response = requests.get(f"{BASE_URL}/catalogs/{catalog_type}", headers=headers)
    if response.status_code != 200:
        raise ValueError(
            f"Error al obtener catálogos, el estatus devuelto {response.status_code}"
        )
    catalogs = response.json()
    if len(catalogs) == 0:
        raise ValueError(f"No hay catálogos {catalog_type} asociados a la cuenta")

    return [
        {
            "id": catalog["id"],
            "name": catalog["name"],
            "referenceCode": catalog["referenceCode"],
        }
        for catalog in catalogs
    ]


def get_all_entities():
    vehicles = get_all_vehicles()
    logging.info(f"All vehicles loaded {len(vehicles)}")

    suppliers = get_all_suppliers()
    logging.info(f"All suppliers loaded {len(suppliers)}")

    vehicle_types = get_all_catalogs("VEHICLES_TYPES")
    logging.info(f"All vehicle types loaded {len(vehicle_types)}")

    vehicle_property_types = get_all_catalogs("PROPERTIES_TYPES")
    logging.info(f"All vehicle property types loaded {len(vehicle_property_types)}")

    vehicle_fuel_types = get_all_catalogs("FUEL_TYPES")
    logging.info(f"All vehicle fuel types loaded {len(vehicle_fuel_types)}")

    return (
        vehicles,
        suppliers,
        vehicle_types,
        vehicle_property_types,
        vehicle_fuel_types,
    )


# Función para procesar archivos
def process_excel_files():
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
    if not os.path.exists(ERROR_DIR):
        os.makedirs(ERROR_DIR)

    # Obtenemos los catálogos
    (
        vehicles,
        suppliers,
        vehicle_types,
        vehicle_property_types,
        vehicle_fuel_types,
    ) = get_all_entities()

    for file in os.listdir(PENDING_DIR):
        if file.endswith(".xlsx"):
            try:
                file_path = os.path.join(PENDING_DIR, file)
                logging.info(f"Procesando archivo: {file}")
                df = pd.ExcelFile(file_path).parse("RENTINGS")
                processed_rows, error_rows = [], []

                for index, row in df.iterrows():
                    try:
                        vehicle_id, mapped_data = try_to_map(
                            normalize_dict(row),
                            vehicles,
                            suppliers,
                            vehicle_types,
                            vehicle_property_types,
                            vehicle_fuel_types,
                        )

                        update_vehicle(vehicle_id, mapped_data)

                        processed_rows.append(mapped_data)

                        logging.info(
                            f"Vehículo {vehicle_id} actualizado. Esperando {MAX_SECONDS_TO_SLEEP} segundos para continuar."
                        )
                        time.sleep(MAX_SECONDS_TO_SLEEP)
                    except Exception as e:
                        row["map_error"] = str(e)
                        error_rows.append(row)

                save_results(file, processed_rows, error_rows)
            except Exception as e:
                logging.error(f"Error procesando archivo {file}: {str(e)}")


# Función de mapeo
def try_to_map(
    row,
    vehicles,
    suppliers,
    vehicle_types,
    vehicle_property_types,
    vehicle_fuel_types,
):
    try:
        vehicle = get_vehicle(row["Matrícula"], vehicles)

        mapped_data = {
            # Vehicle
            "name": vehicle["name"],
            "registrationNumber": vehicle["registration_number_v1"],
            "vehicleStatusId": vehicle["vehicle_status_id"],
            "vehicleTypeId": get_catalog_id(vehicle["vehicle_type"], vehicle_types),
            "propertyTypeId": get_catalog_id(row["Propiedad"], vehicle_property_types),
            "fuelTypeId": get_catalog_id(vehicle["fuel_type"], vehicle_fuel_types),
            # Renting y Leasing
            "vehicleProperties": {
                "referenceCode": None,
                "supplierId": get_supplier_id(row["Proveedor"], suppliers),
                "startDate": convert_date_to_iso_format(
                    pd.to_datetime(row["Fecha inicio"], format="%d %m %Y").date()
                ),
                "endDate": convert_date_to_iso_format(
                    pd.to_datetime(row["Fecha fin"], format="%d %m %Y").date()
                ),
                "initialOdometer": float(row["Odónetro inicial"]),
                "odometerContracted": float(row["Kilometraje contratado"]),
                "odometerPerYear": float(row["Kilometraje por año"]),
                "subtotalInitialFee": (
                    float(row["Cuota inicial subtotal €"])
                    if row.get("Cuota inicial subtotal €") is not None
                    else None
                ),
                "initialFeeTaxType": TAX_TYPES.get(
                    row.get("Tipo de Impuesto"), "PERCENTAGE"
                ),
                "initialFeeTax": float(row["% impuestos"]),
                "initialFeeTotalAmount": (
                    float(row["Cuota inicial total €"])
                    if row.get("Cuota inicial total €") is not None
                    else None
                ),
                "subtotalScheduledFee": float(row["Cuota de empresa €"]),
                "scheduledFeeTaxType": TAX_TYPES.get(
                    row.get("Tipo de Impuesto"), "PERCENTAGE"
                ),
                "scheduledFeeTax": float(row["% impuestos"]),
                "employeeFee": float(row["Cuota de empleado €"]),
                "scheduledFeeTotalAmount": float(row["Cuota recurrente total €"]),
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
                                row["Permanencia mínima"], format="%d %m %Y"
                            ).date()
                        )
                        if row.get("Permanencia mínima") is not None
                        else None
                    ),
                    "cf_property_tipo_de_contrato": row["Tipo de contrato"],
                    "cf_property_tipo_de_pago": row["Tipo de pago"],
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
                    "cf_property_rotulacion": str_to_bool(
                        row.get("Rotulación", "FALSE")
                    ),
                    "cf_property_equipamiento": str_to_bool(
                        row.get("Equipamiento", "FALSE")
                    ),
                },
            },
        }

        vehicleProperties = mapped_data["vehicleProperties"]

        validate_total_calculations(
            vehicleProperties["subtotalInitialFee"],
            vehicleProperties["initialFeeTaxType"],
            vehicleProperties["initialFeeTax"],
            vehicleProperties["initialFeeTotalAmount"],
        )

        validate_total_calculations(
            vehicleProperties["subtotalScheduledFee"],
            vehicleProperties["scheduledFeeTaxType"],
            vehicleProperties["scheduledFeeTax"],
            vehicleProperties["scheduledFeeTotalAmount"],
        )

        return vehicle["id"], mapped_data
    except Exception as e:
        # traceback.print_exc()
        raise ValueError(f"Error al mapear fila: {str(e)}")


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
            f"Registrar combustible, error code {response.status_code}, {response.text}"
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
