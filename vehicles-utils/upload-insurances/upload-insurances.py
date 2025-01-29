import logging
import os
import requests
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
    filename=os.path.join(LOG_DIR, f"process_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Listas de referencia
TAX_TYPES = {"Porcentaje": "PERCENTAGE", "Moneda": "CURRENCY"}
PAYMENT_FREQUENCIES = {"Diario": "day", "Semanal": "week", "Mensual": "month", "Anual": "year"}


def is_not_empty(str: str) -> bool:
    return bool(str) or str != ""


def clean_registration_number(registration_number):
    import re

    return re.sub(r"[^a-zA-Z0-9]", "", registration_number)


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
            "registration_number": clean_registration_number(
                vehicle["registrationNumber"]
            ),
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

    insurance_types = get_all_catalogs("INSURANCE_TYPES")
    logging.info(f"All insurance types loaded {len(insurance_types)}")

    return vehicles, suppliers, insurance_types


# Función para procesar archivos
def process_excel_files():
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
    if not os.path.exists(ERROR_DIR):
        os.makedirs(ERROR_DIR)

    # Obtenemos los catálogos
    vehicles, suppliers, insurance_types = get_all_entities()

    for file in os.listdir(PENDING_DIR):
        if file.endswith(".xlsx"):
            try:
                file_path = os.path.join(PENDING_DIR, file)
                logging.info(f"Procesando archivo: {file}")
                df = pd.ExcelFile(file_path).parse("INSURANCES")
                processed_rows, error_rows = [], []

                for index, row in df.iterrows():
                    try:
                        vehicle_id = get_vehicle_id(row["Matrícula"], vehicles)

                        mapped_data = try_to_map(row, suppliers, insurance_types)

                        update_vehicle(vehicle_id, mapped_data)

                        processed_rows.append(mapped_data)

                        logging.info(
                            f"Esperando {MAX_SECONDS_TO_SLEEP} segundos antes de seguir con el siguiente registro."
                        )
                        time.sleep(MAX_SECONDS_TO_SLEEP)
                    except Exception as e:
                        row["map_error"] = str(e)
                        error_rows.append(row)

                save_results(file, processed_rows, error_rows)
            except Exception as e:
                logging.error(f"Error procesando archivo {file}: {str(e)}")


# Función de mapeo
def try_to_map(row, suppliers, insurance_types):
    try:
        mapped_data = {
            "insurancePolicyNumber": row["Número de Poliza"],
            "insuranceSupplierId": get_supplier_id(row["Proveedor"], suppliers),
            "insuranceStartDate": pd.to_datetime(row["Fecha inicio"], format="%d %m %Y").date(),
            "insuranceEndDate": pd.to_datetime(row["Fecha fin"], format="%d %m %Y").date(),
            "insuranceSubtotal": float(row["Prima Subtotal"].strip()),
            "insuranceTaxType": TAX_TYPES[row["Tipo de Impuesto"]] if row["Tipo de Impuesto"] else "PERCENTAGE",
            "insuranceTax": float(row["Valor de Impuesto"].replace("%", "")),
            "insuranceTotalAmount": float(row["Prima Total"].strip()),
            "insuranceTypeId": get_catalog_id(row["Tipo de Seguro"], insurance_types),
            "insurancePaymentFrequency": PAYMENT_FREQUENCIES[row["Frecuencia de Pago"]],
            "createInsuranceScheduledExpense": bool(row["Crear Gasto Programado"]),
        }

        total_calculated = mapped_data["insuranceSubtotal"]
        if mapped_data["insuranceTaxType"] == "PERCENTAGE":
            total_calculated *= (1 + mapped_data["insuranceTax"] / 100)
        elif mapped_data["insuranceTaxType"] == "CURRENCY":
            total_calculated += mapped_data["insuranceTax"]

        if round(total_calculated, 4) != round(mapped_data["insuranceTotalAmount"], 4):
            raise ValueError("Diferencia en el cálculo del total de prima")

        return mapped_data
    except Exception as e:
        raise ValueError(f"Error al mapear fila: {str(e)}")


# Función para obtener vehicle ID
def get_vehicle_id(registration_number, vehicles):
    cleaned_registration_number = clean_registration_number(registration_number) if is_not_empty(registration_number) else None

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

    return vehicle["id"]


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
            if catalog_name is not None
            and item["name"].lower() == catalog_name.lower()
        ),
        None,
    )

    if catalog is None:
        raise ValueError(f"Catálogo '{catalog_name}' no encontrado")

    return catalog["id"]


# Función para actualizar el vehículo por su ID
def update_vehicle(vehicle_id, data):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    params = {}
    response = requests.put(
        f"{BASE_URL}/vehicles/{vehicle_id}", data=data, headers=headers, params=params
    )
    if response.status_code != 201:
        logger.info(
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
