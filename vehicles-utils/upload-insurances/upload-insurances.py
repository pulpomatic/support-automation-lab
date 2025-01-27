import logging
import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
VEHICLE_API_URL = os.getenv("VEHICLE_API_URL")
CATALOG_API_URL = os.getenv("CATALOG_API_URL")
LOG_DIR = "./logs"
PENDING_DIR = "./pending"
PROCESSED_DIR = "./processed"
ERROR_DIR = "./error"

# Configuración de logging
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, f"process_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Listas de referencia
PROVIDERS = [{"id": 1, "name": "MAPFRE"}, {"id": 2, "name": "AXA"}]
TAX_TYPES = {"Porcentaje": "PERCENTAGE", "Moneda": "CURRENCY"}
PAYMENT_FREQUENCIES = {"Diario": "day", "Semanal": "week", "Mensual": "month", "Anual": "year"}

# Función para procesar archivos

def process_excel_files():
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
    if not os.path.exists(ERROR_DIR):
        os.makedirs(ERROR_DIR)

    for file in os.listdir(PENDING_DIR):
        if file.endswith(".xlsx"):
            try:
                file_path = os.path.join(PENDING_DIR, file)
                logging.info(f"Procesando archivo: {file}")
                df = pd.ExcelFile(file_path).parse("INSURANCES")
                processed_rows, error_rows = [], []

                for index, row in df.iterrows():
                    try:
                        mapped_data = try_to_map(row)
                        processed_rows.append(mapped_data)
                    except Exception as e:
                        row["map_error"] = str(e)
                        error_rows.append(row)

                save_results(file, processed_rows, error_rows)
            except Exception as e:
                logging.error(f"Error procesando archivo {file}: {str(e)}")

# Función de mapeo
def try_to_map(row):
    try:
        mapped_data = {
            "insurancePolicyNumber": row["Número de Poliza"],
            "insuranceSupplierId": get_supplier_id(row["Proveedor"]),
            "insuranceStartDate": pd.to_datetime(row["Fecha inicio"], format="%d %m %Y").date(),
            "insuranceEndDate": pd.to_datetime(row["Fecha fin"], format="%d %m %Y").date(),
            "insuranceSubtotal": float(row["Prima Subtotal"].strip()),
            "insuranceTaxType": TAX_TYPES[row["Tipo de Impuesto"]],
            "insuranceTax": float(row["Valor de Impuesto"]),
            "insuranceTotalAmount": float(row["Prima Total"].strip()),
            "insuranceTypeId": get_catalog_id(row["Tipo de Seguro"]),
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

# Función para obtener supplier ID
def get_supplier_id(provider_name):
    for provider in PROVIDERS:
        if provider_name in provider["name"]:
            return provider["id"]
    raise ValueError("Proveedor no encontrado")

# Función para obtener catálogo ID
def get_catalog_id(type_name):
    # Aquí realizarías la llamada a la API de catálogos
    return 1  # Mock para este ejemplo

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