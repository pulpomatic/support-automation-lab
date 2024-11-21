import json
import logging
import os
import time
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from functools import partial
from typing import Any

import pandas as pd
import pytz
import requests

# Directorios
PENDING_DIR = os.path.join(os.path.dirname(__file__), "pending")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "processed")
ERROR_DIR = os.path.join(os.path.dirname(__file__), "error")

# Configuración de ThreadPoolExecutor
MAX_WORKERS = 5
MAX_SECONDS_TO_SLEEP = 1

# URL de la API de ejemplo
BASE_URL = "https://eu1.getpulpo.com/api/v1"

CUSTOM_FIELD_DEFAULT_SECTION_NAME = "Campos de Repsol"
EXPENSES_CUSTOM_FIELDS_DEFINITION = [
    {
        "name": "cf_repsolv2_raw_filename",
        "label": "Nombre del Archivo de Origen (Crudo)",
        "controlType": "text",
        "sectionName": CUSTOM_FIELD_DEFAULT_SECTION_NAME,
        "isRequired": False,
        "hidden": True,
    },
    {
        "name": "cf_repsolv2_product_description",
        "label": "Descripción del Producto",
        "controlType": "text",
        "sectionName": CUSTOM_FIELD_DEFAULT_SECTION_NAME,
        "isRequired": False,
        "hidden": False,
    },
    {
        "name": "cf_repsolv2_original_odometer",
        "label": "Odómetro Fuente",
        "controlType": "text",
        "sectionName": CUSTOM_FIELD_DEFAULT_SECTION_NAME,
        "isRequired": False,
        "hidden": False,
    },
    {
        "name": "cf_repsolv2_fiscal_code",
        "label": "Código del establecimiento",
        "controlType": "text",
        "sectionName": CUSTOM_FIELD_DEFAULT_SECTION_NAME,
        "isRequired": False,
        "hidden": True,
    },
    {
        "name": "cf_repsolv2_id_cuenta",
        "label": "Id de Cuenta",
        "controlType": "text",
        "sectionName": CUSTOM_FIELD_DEFAULT_SECTION_NAME,
        "isRequired": False,
        "hidden": False,
    },
]
FUELS_CUSTOM_FIELDS_DEFINITION = EXPENSES_CUSTOM_FIELDS_DEFINITION + [
    {
        "name": "cf_repsolv2_discount_per_unit",
        "label": "Descuento por Unidad",
        "controlType": "currency",
        "sectionName": CUSTOM_FIELD_DEFAULT_SECTION_NAME,
        "isRequired": False,
        "hidden": False,
    },
    {
        "name": "cf_repsolv2_price_per_unit_final",
        "label": "Precio por Unidad Final",
        "controlType": "currency",
        "sectionName": CUSTOM_FIELD_DEFAULT_SECTION_NAME,
        "isRequired": False,
        "hidden": False,
    },
]


# Configuración del logger
def setup_logger():
    # Asegura que la carpeta 'logs' exista
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Configura el nombre del archivo de log con la fecha y hora actual
    log_filename = datetime.now().strftime("logs/log_%Y%m%d_%H%M%S.log")

    # Configuración del logger
    logger = logging.getLogger("process_logger")
    logger.setLevel(logging.DEBUG)  # Nivel de log mínimo a capturar

    # Formato del log
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Handler para escribir en archivo
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Handler para mostrar en consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Añade los handlers al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Inicializa el logger
logger = setup_logger()


def clean_registration_number(registration_number):
    import re

    return re.sub(r"[^a-zA-Z0-9]", "", registration_number)


def get_all_vehicles(token):
    headers = {"Authorization": f"Bearer {token}"}
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


def get_all_catalogs(token, catalog_type):
    headers = {"Authorization": f"Bearer {token}"}
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


def get_all_payment_methods(token):
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "skip": 0,
        "take": 0,
    }
    response = requests.get(
        f"{BASE_URL}/payment-methods", headers=headers, params=params
    )
    if response.status_code != 200:
        raise ValueError(
            f"Error al obtener medios de pago, el estatus devuelto {response.status_code}"
        )
    response_json = response.json()
    payment_methods = response_json["paymentMethods"]
    if len(payment_methods) == 0:
        raise ValueError("No hay medios de pago asociados a la cuenta")

    return [
        {
            "id": payment_method["id"],
            "name": payment_method["name"],
            "slug": payment_method["slug"],
        }
        for payment_method in payment_methods
    ]


def get_all_entities(token: str):
    vehicles = get_all_vehicles(token)
    logger.info(f"All vehicles loaded {len(vehicles)}")
    payment_methods = get_all_payment_methods(token)
    logger.info(f"All payment methods loaded {len(payment_methods)}")
    fuel_type_of_fuels = get_all_catalogs(token, "FUEL-TYPES-OF-FUELS")
    expense_types = get_all_catalogs(token, "EXPENSES-TYPES")
    logger.info(f"All catalogs loaded")
    return vehicles, payment_methods, fuel_type_of_fuels, expense_types


def try_to_map_data(
    index,
    row_dict,
    filename: str,
    vehicles: list,
    payment_methods: list,
    locations: list,
    product_to_fuel_types: list,
    fuel_type_of_fuels: list,
    product_to_expense_types: list,
    expense_types: list,
):
    try:
        data = map_data(
            row_dict,
            filename,
            vehicles,
            payment_methods,
            locations,
            product_to_fuel_types,
            fuel_type_of_fuels,
            product_to_expense_types,
            expense_types,
        )
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error mapeando registro en el indice {index}, {str(e)}")
        return {"success": False, "error": str(e)}


# Función para mapear los gastos y combustibles
def map_data(
    row_dict,
    filename: str,
    vehicles: list,
    payment_methods: list,
    locations: list,
    product_to_fuel_types: list,
    fuel_type_of_fuels: list,
    product_to_expense_types: list,
    expense_types: list,
):
    cleaned_matricula = clean_registration_number(row_dict["MATRICULA"])
    vehicle = next(
        (
            item
            for item in vehicles
            if cleaned_matricula is not None
            and item["registration_number"] == cleaned_matricula
        ),
        None,
    )
    if vehicle is None:
        raise ValueError(f"El vehículo con la placa {row_dict['MATRICULA']} no existe")

    num_tarjeta = int(row_dict["NUM_TARJET"])

    payment_method = next(
        (
            item
            for item in payment_methods
            if row_dict["NUM_TARJET"] is not None
            and item["slug"] == f"{num_tarjeta}"
        ),
        None,
    )
    if payment_method is None:
        raise ValueError(
            f"El medio de pago con el número {num_tarjeta} no existe"
        )

    location = next(
        (
            item
            for item in locations
            if row_dict["COD_ESTABL"] is not None
            and int(item["fiscal_code"]) == int(row_dict["COD_ESTABL"])
        ),
        None,
    )
    if location is None:
        raise ValueError(
            f"El proveedor con el codigo {row_dict['COD_ESTABL']} no existe"
        )

    # Unir fecha y hora, convertir a ISO8601 UTC
    fec_operac = row_dict["FEC_OPERAC"]
    hor_operac = row_dict["HOR_OPERAC"]
    local_dt = datetime.strptime(f"{fec_operac} {hor_operac}", "%Y%m%d %H%M")
    madrid_tz = pytz.timezone("Europe/Madrid")
    local_dt = madrid_tz.localize(local_dt)
    date = local_dt.astimezone(pytz.UTC).isoformat()

    kilometers = (
        int(row_dict["KILOMETROS"]) if int(row_dict["KILOMETROS"]) > 0 else None
    )

    operation_info = get_operation_type_info(
        row_dict["COD_PRODU"], product_to_fuel_types, product_to_expense_types
    )

    totals = calculate_totals(
        row_dict["IVA"], row_dict["IMPORTE"], row_dict["IMP_TOTAL"]
    )

    if operation_info["is_fuel"]:
        # map fuel
        fuel_type_of_fuel = next(
            (
                item
                for item in fuel_type_of_fuels
                if item["referenceCode"] is not None and operation_info["info"]["reference_code"]
                == int(item["referenceCode"])
            ),
            None,
        )
        price_per_unit = totals.get("subtotal") / float(row_dict["NUM_LITROS"])

        discount_per_unit = (
            float(row_dict["IMPORTE"]) - float(row_dict["IMP_TOTAL"])
        ) / float(row_dict["NUM_LITROS"])

        price_per_unit_final = float(totals.get("total")) / float(
            row_dict["NUM_LITROS"]
        )

        return {
            "is_fuel": True,
            "mapped": {
                "volume": float(row_dict["NUM_LITROS"]),
                "pricePerUnit": price_per_unit,
                "taxType": "PERCENTAGE",
                "tax": float(row_dict["IVA"]),
                "discountType": "PERCENTAGE",
                "discount": totals.get("discount_percentage"),
                "total": totals.get("total"),
                "date": date,
                "fuelTypeId": fuel_type_of_fuel["id"],
                "vehicleId": vehicle["id"],
                "driverId": None,
                "supplierId": 1,  # Supplier Repsol
                "locationId": location["id"],
                "reference": None,
                "paymentMethodId": payment_method["id"],
                "odometer": kilometers,
                "customFieldsMetadata": json.dumps(
                    {
                        "cf_repsolv2_raw_filename": filename,
                        "cf_repsolv2_product_description": operation_info["info"][
                            "product_description"
                        ],
                        "cf_repsolv2_id_cuenta": row_dict["COD_CLI"],
                        "cf_repsolv2_original_odometer": row_dict["KILOMETROS"],
                        "cf_repsolv2_fiscal_code": row_dict["COD_ESTABL"],
                        "cf_repsolv2_discount_per_unit": discount_per_unit,
                        "cf_repsolv2_price_per_unit_final": price_per_unit_final,
                    }
                ),
            },
        }
    else:
        # map expense
        expense_type = next(
            (
                item
                for item in expense_types
                if item["referenceCode"] is not None and operation_info["info"]["reference_code"]
                == int(item["referenceCode"])
            ),
            None,
        )
        return {
            "is_fuel": False,
            "mapped": {
                "name": operation_info["info"]["product_description"],
                "taxType": "PERCENTAGE",
                "tax": float(row_dict["IVA"]),
                "discountType": "PERCENTAGE",
                "discount": totals.get("discount_percentage"),
                "total": totals.get("total"),
                "subtotal": totals.get("subtotal"),
                "date": date,
                "expenseTypeId": expense_type["id"],
                "vehicleId": vehicle["id"],
                "driverId": None,
                "supplierId": 1,  # Supplier Repsol
                "locationId": location["id"],
                "paymentMethodId": payment_method["id"],
                "odometer": kilometers,
                "customFieldsMetadata": {
                    "cf_repsolv2_raw_filename": filename,
                    "cf_repsolv2_product_description": operation_info["info"][
                        "product_description"
                    ],
                    "cf_repsolv2_id_cuenta": row_dict["COD_CLI"],
                    "cf_repsolv2_original_odometer": row_dict["KILOMETROS"],
                    "cf_repsolv2_fiscal_code": row_dict["COD_ESTABL"],
                },
            },
        }


def calculate_totals(percentage_tax: str, importe: str, importe_total: str):
    percentage_tax = Decimal(percentage_tax)
    importe = Decimal(importe)
    importe_total = Decimal(importe_total)

    tax_subtraction = 1 + percentage_tax / 100
    subtotal = importe / tax_subtraction  # Subtotal sin impuesto
    calculated_discount = Decimal(0)
    percentage_discount = Decimal(0)

    if abs(importe) > abs(importe_total):  # La operacion tiene descuento
        calculated_discount = (importe_total - importe) / tax_subtraction
        percentage_discount = ((importe - importe_total) / abs(importe)) * 100

    calculated_tax = (subtotal + calculated_discount) * (percentage_tax / 100)
    calculated_total = subtotal + calculated_discount + calculated_tax

    totals = {
        "subtotal": float(subtotal),
        "discount": float(calculated_discount),
        "discount_percentage": float(percentage_discount),
        "tax": float(calculated_tax),
        "total": float(calculated_total),
    }

    check_difference = importe_total - calculated_total
    if abs(check_difference) > Decimal("0.0001"):
        evidence = {
            "message": f"El total de operación {importe_total} no iguala al total calculado {calculated_total}, con impuesto {percentage_tax}, {importe}",
            "difference": float(calculated_total - importe_total),
            "params": {
                "percentage_tax": percentage_tax,
                "importe": importe,
                "importe_total": importe_total,
            },
        }
        raise ValueError({**totals, **evidence})

    return totals


def process_data(data: list[dict], file_name: str, token: str, is_fuel: bool):
    total_rows = len(data)
    if total_rows == 0:
        logger.info("No hay nada que procesar")
        return

    processed_successfully = []
    processed_with_errors = []

    # Enumerar todos los datos una vez para evitar reiniciar row_idx
    indexed_data = list(enumerate(data, start=1))

    # Dividimos la cantidad de filas en batches para que sean procesados en paralelo y no perder tiempo uno a uno
    for idx in range(0, total_rows, MAX_WORKERS):
        batch = indexed_data[idx : idx + MAX_WORKERS]
        futures: list[tuple[Future, Any]] = []
        # Inicializamos el ThreadPoolExecutor para que ejecute tantas {MAX_WORKERS} veces peticiones en paralelo
        # Es necesario inicializar el ThreadPoolExecutor con with para garantizar el shutdown
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for row_idx, row in batch:
                future = executor.submit(
                    process_and_send,
                    row["mapped"],
                    row_idx,
                    total_rows,
                    file_name,
                    token,
                    is_fuel,
                )
                raw_row = row["raw"]
                futures.append((future, raw_row))
            # Esto es importante por que debemos esperar hasta que respondan todos los llamados
            for future, raw_row in futures:
                result = future.result()
                if result["success"]:
                    processed_successfully.append(raw_row)
                else:
                    raw_row["error"] = result["error"]
                    processed_with_errors.append(raw_row)
        logger.info(
            f"Esperando {MAX_SECONDS_TO_SLEEP} segundos antes de seguir con el siguiente batch"
        )
        time.sleep(MAX_SECONDS_TO_SLEEP)

    return processed_successfully, processed_with_errors


# Función para procesar y transformar una fila
def process_and_send(
    row, row_idx: int, total_rows: int, file_name: str, token: str, is_fuel: bool
):
    send_request = (
        partial(send_to_fuel_api, row, token)
        if is_fuel
        else partial(send_to_expense_api, row, token)
    )
    try:
        logger.info(
            f"Enviando {'Combustible' if is_fuel else 'Gasto'} ({row_idx}/{total_rows}) del archivo {file_name}"
        )
        time.sleep(
            MAX_SECONDS_TO_SLEEP
        )  # Descomentar y comentar send_request() para hacer pruebas sin necesidad de registrar datos
        # send_request()
        return {"success": True}
    except Exception as e:
        logger.error(
            f"Error procesando fila {row_idx} del archivo {file_name}, el registro será guardado en archivo de errores"
        )
        logger.info(row)
        return {"success": False, "error": str(e)}


# Función para enviar un batch de filas a la API
def send_to_fuel_api(row, token):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"omitOdometerIfFails": "true"}
    response = requests.post(
        f"{BASE_URL}/fuels", data=row, headers=headers, params=params
    )
    if response.status_code != 201:
        logger.info(
            f"Registrar combustible, error code {response.status_code}, {response.text}"
        )
        raise ValueError(f"Error: {response.status_code} {response.text}")


def send_to_expense_api(row, token):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"omitOdometerIfFails": "true"}
    response = requests.post(
        f"{BASE_URL}/expenses", json=row, headers=headers, params=params
    )
    if response.status_code != 201:
        logger.info(
            f"Registrar gasto, error code {response.status_code}, {response.text}"
        )
        raise ValueError(f"Error: {response.status_code} {response.text}")


def load_product_to_expense_types():
    path = os.path.join(
        os.path.dirname(__file__), "maps", "product_to_expense_types.json"
    )
    return get_json_from_file(path)


def load_product_to_fuel_types():
    path = os.path.join(os.path.dirname(__file__), "maps", "product_to_fuel_types.json")
    return get_json_from_file(path)


def load_locations():
    path = os.path.join(os.path.dirname(__file__), "maps", "repsol-locations-bd.json")
    return get_json_from_file(path)


def get_json_from_file(filename):
    with open(filename, "r", encoding="utf-8") as json_file:
        data_list = json.load(json_file)
        return data_list


def get_operation_type_info(
    cod_product, product_to_fuel_types: list, product_to_expense_types: list
):
    fuel_type_of_fuel_info = next(
        (
            item
            for item in product_to_fuel_types
            if cod_product is not None and item["codigo_producto"] == int(cod_product)
        ),
        None,
    )
    if fuel_type_of_fuel_info is not None:
        return {
            "info": fuel_type_of_fuel_info["pulpo"],
            "is_fuel": True,
        }

    expense_type_info = next(
        (
            item
            for item in product_to_expense_types
            if cod_product is not None and item["codigo_producto"] == int(cod_product)
        ),
        None,
    )

    if expense_type_info is not None:
        return {
            "info": expense_type_info["pulpo"],
            "is_fuel": False,
        }

    raise ValueError(
        f"Tipo de operación {cod_product} no reconocida",
    )


def save_raw_data(data, file_name: str, suffix: str, dir: str):
    """
    Guarda los datos crudos en un nuevo archivo Excel en la carpeta 'processed'.

    :param data: lista de diccionarios con datos crudos
    :param file_name: nombre del archivo original
    :param suffix: sufijo para distinguir entre combustibles y gastos
    :param dir: el directorio donde se almacenara el archivo
    """
    ensure_directory_exists(dir)
    df_raw = pd.DataFrame(data)  # .from_dict()  # Crear DataFrame con los datos crudos
    base_name = os.path.splitext(file_name)[0]  # Elimina la extensión del archivo
    new_file_name = f"{base_name}_{suffix}.xlsx"
    output_path = os.path.join(dir, new_file_name)

    # Guardar el DataFrame como Excel
    df_raw.to_excel(output_path, index=False)
    logger.info(f"Archivo {new_file_name} guardado en ${dir}")


def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Carpeta '{directory}' creada.")


def configure_fuels_custom_fields(token, required_custom_fieds: list, type: str):
    logger.info(f"Configurando Campos Personalizados {type}")
    headers = {"Authorization": f"Bearer {token}"}
    params = {"type": type}
    response = requests.get(f"{BASE_URL}/custom-fields", headers=headers, params=params)
    if response.status_code != 200:
        raise ValueError(
            f"Error al obtener campos personalizados {type}, el estatus devuelto {response.status_code}"
        )
    response_json = response.json()
    if (response_json["customFields"] is None):
        custom_fields_saved = []
    else:
        custom_fields_saved = response_json["customFields"]["fields"]

    saved_field_names = {field["name"] for field in custom_fields_saved}
    # Revisamos los campos necesarios
    has_changed = False
    for field in required_custom_fieds:
        if field["name"] not in saved_field_names:
            has_changed = True
            custom_fields_saved.append(field)
            logger.info(f"Campo '{field['name']}' agregado.")

    if has_changed is False:
        return

    payload = {
        "fields": custom_fields_saved,
        "type": type,
    }
    response = requests.post(f"{BASE_URL}/custom-fields", json=payload, headers=headers)
    if response.status_code != 201:
        raise ValueError(
            f"Error al guardar campos personalizados {type}, {response.status_code}, {response.text}"
        )


# Script principal
def main():
    # Listar archivos en carpeta 'pending'
    files = [
        f for f in os.listdir(PENDING_DIR) if f.endswith(".xls") or f.endswith(".xlsx")
    ]
    if len(files) == 0:
        logger.info(
            "No hay archivos que procesar, verifique que hayan en la carpeta de /pending"
        )
        return

    logger.info("Archivos encontrados para procesar:")
    for idx, file in enumerate(files, start=1):
        logger.info(f"{idx} - {file}")

    confirmation = input("¿Deseas procesar estos archivos? (Y/N): ").strip().upper()
    if confirmation != "Y":
        logger.info("Operación cancelada.")
        return

    token = input(
        "Introduce el token activo para continuar (sin la palabra Bearer): "
    ).strip()

    if not token:
        logger.info("Token no válido, operación cancelada.")
        return

    # Precargamos los datos maestros
    vehicles, payment_methods, fuel_type_of_fuels, expense_types = get_all_entities(
        token
    )

    product_to_expense_types = load_product_to_expense_types()
    product_to_fuel_types = load_product_to_fuel_types()
    locations = load_locations()

    configure_fuels_custom_fields(token, EXPENSES_CUSTOM_FIELDS_DEFINITION, "expenses")
    configure_fuels_custom_fields(token, FUELS_CUSTOM_FIELDS_DEFINITION, "fuels")

    # Procesamiento de archivos
    for idx, file_name in enumerate(files, start=1):
        logger.info(f"Procesando archivo {file_name} ({idx}/{len(files)})")
        file_path = os.path.join(PENDING_DIR, file_name)
        df = pd.read_excel(file_path, sheet_name=0, dtype=str)
        total_rows = len(df)

        if total_rows == 0:
            logger.info(
                f"No hay nada que procesar en el archivo {file_name}, omitiendo..."
            )
            continue

        # Bucle para mapear filas
        logger.info("Mapeando datos...")
        fuels = []
        expenses = []
        mapped_error = []
        for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
            logger.info(f"Mapeando ({row_idx}/{total_rows}) filas")
            row_dict = row.to_dict()
            mapping_result = try_to_map_data(
                row_idx,
                row_dict,
                file_name,
                vehicles,
                payment_methods,
                locations,
                product_to_fuel_types,
                fuel_type_of_fuels,
                product_to_expense_types,
                expense_types,
            )
            if mapping_result["success"]:
                data = mapping_result["data"]
                if data["is_fuel"]:
                    fuels.append({"mapped": data["mapped"], "raw": row_dict})
                else:
                    expenses.append({"mapped": data["mapped"], "raw": row_dict})
            else:
                row_dict["error"] = mapping_result["error"]
                mapped_error.append(row_dict)

        # Si ocurre un error de mapeo genera archivo correspondiente y sigue ejecutando
        if len(mapped_error) != 0:
            logger.info("Datos mapeados pero con errores, generando archivo...")
            save_raw_data(mapped_error, file_name, "mapeo_error", ERROR_DIR)
        else:
            logger.info("Datos mapeados exitosamente")

        fuels_len = len(fuels)
        logger.info(f"Combustibles totales: {fuels_len}")
        expenses_len = len(expenses)
        logger.info(f"Gastos totales: {expenses_len}")

        if fuels_len == 0 and expenses_len == 0:
            raise ValueError(
                "Hubo un error al obtener registros de combustibles y gastos, por favor verifique los datos y los errores"
            )

        if fuels_len > 0:
            logger.info("Procesando Combustibles")
            processed_fuels, error_fuels = process_data(fuels, file_name, token, True)
            if len(processed_fuels):
                save_raw_data(processed_fuels, file_name, "combustibles", PROCESSED_DIR)
            if len(error_fuels) > 0:
                save_raw_data(error_fuels, file_name, "combustibles_error", ERROR_DIR)

        if expenses_len > 0:
            logger.info("Procesando Gastos")
            processed_expenses, error_expenses = process_data(
                expenses, file_name, token, False
            )
            if len(processed_expenses) > 0:
                save_raw_data(processed_expenses, file_name, "gastos", PROCESSED_DIR)
            if len(error_expenses) > 0:
                save_raw_data(error_expenses, file_name, "gastos_error", ERROR_DIR)

        logger.info(f"Archivo {file_name} procesado completamente")
        logger.info("Los archivos procesados crudos quedaron en la carpeta /pending")


if __name__ == "__main__":
    main()
