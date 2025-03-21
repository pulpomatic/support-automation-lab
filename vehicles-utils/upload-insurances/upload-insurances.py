import os
import requests
import time
from datetime import datetime

import pandas as pd
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
    Convierte una fecha al formato ISO 8601 'YYYY-MM-DDTHH:MM:SS.sssZ'.
    """
    # Convertimos al formato ISO 8601
    return date.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def str_to_bool(value):
    return str(value).strip().lower() in {"true", "1"}


def is_not_empty(str: str) -> bool:
    return bool(str) or str != ""


def clean_registration_number(registration_number):
    import re

    return re.sub(r"[^a-zA-Z0-9]", "", registration_number)


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
            "property_type": vehicle["property"],
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

    insurance_types = api.get_all_catalogs("INSURANCE_TYPES")
    logging.info(f"All insurance types loaded {len(insurance_types)}")

    vehicle_types = api.get_all_catalogs("VEHICLES_TYPES")
    logging.info(f"All vehicle types loaded {len(vehicle_types)}")

    vehicle_property_types = api.get_all_catalogs("PROPERTIES_TYPES")
    logging.info(f"All vehicle property types loaded {len(vehicle_property_types)}")

    vehicle_fuel_types = api.get_all_catalogs("FUEL_TYPES")
    logging.info(f"All vehicle fuel types loaded {len(vehicle_fuel_types)}")

    return (
        vehicles,
        suppliers,
        insurance_types,
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
        insurance_types,
        vehicle_types,
        vehicle_property_types,
        vehicle_fuel_types,
    ) = get_all_entities()

    for file in os.listdir(PENDING_DIR):
        if file.endswith(".xlsx"):
            try:
                file_path = os.path.join(PENDING_DIR, file)
                logging.info(f"Procesando archivo: {file}")
                df = pd.ExcelFile(file_path).parse("INSURANCES")
                processed_rows, error_rows = [], []
                total_rows = len(df)

                for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
                    try:
                        vehicle_id, mapped_data = try_to_map(
                            row,
                            vehicles,
                            suppliers,
                            insurance_types,
                            vehicle_types,
                            vehicle_property_types,
                            vehicle_fuel_types,
                        )

                        if running_type == "T":
                            logging.info(
                                "Procesando en modo test, omitiendo envío del vehículo"
                            )
                            print(vehicle_id, mapped_data)
                        else:
                            update_vehicle(vehicle_id, mapped_data)

                        processed_rows.append(mapped_data)

                        logging.info(
                            f"({row_idx}/{total_rows}) Vehículo {vehicle_id} actualizado. Esperando {MAX_SECONDS_TO_SLEEP} segundos para continuar."
                        )

                        if running_type == "P":
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
    insurance_types,
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
            "propertyTypeId": get_catalog_id(
                vehicle["property_type"], vehicle_property_types
            ),
            "fuelTypeId": get_catalog_id(vehicle["fuel_type"], vehicle_fuel_types),
            "segments": [
                segment.get("id") for segment in vehicle["segments"] if "id" in segment
            ],
            # Insurance
            "insurancePolicyNumber": str(row["Número de Poliza"]),
            "insuranceSupplierId": get_supplier_id(row["Proveedor"], suppliers),
            "insuranceStartDate": convert_date_to_iso_format(
                pd.to_datetime(row["Fecha inicio"], format="%d %m %Y").date()
            ),
            "insuranceEndDate": convert_date_to_iso_format(
                pd.to_datetime(row["Fecha fin"], format="%d %m %Y").date()
            ),
            "insuranceSubtotal": float(row["Prima Subtotal"]),
            "insuranceTaxType": TAX_TYPES.get(
                row.get("Tipo de Impuesto"), "PERCENTAGE"
            ),
            "insuranceTax": float(row["% impuesto"]),
            "insuranceTotalAmount": float(row["Prima Total"]),
            "insuranceTypeId": get_catalog_id(row["Tipo De Seguro"], insurance_types),
            "insurancePaymentFrequency": PAYMENT_FREQUENCIES[row["Frecuencia de Pago"]],
            "createInsuranceScheduledExpense": str_to_bool(
                row.get("Crear Gasto Programado", "FALSE")
            ),
        }

        total_calculated = mapped_data["insuranceSubtotal"]
        if mapped_data["insuranceTaxType"] == "PERCENTAGE":
            total_calculated *= 1 + mapped_data["insuranceTax"] / 100
        elif mapped_data["insuranceTaxType"] == "CURRENCY":
            total_calculated += mapped_data["insuranceTax"]

        if round(total_calculated, 4) != round(mapped_data["insuranceTotalAmount"], 4):
            raise ValueError("Diferencia en el cálculo del total de prima")

        return vehicle["id"], mapped_data
    except Exception as e:
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
