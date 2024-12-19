import os
import pandas as pd
import requests
import json
import time
from DateTransform import DateTransform

class RentingLeasingLoader:
    REQUIRED_COLUMNS = [
        "Contrato*",
        "Propiedad*",
        "Cuota recurrente total*",
        "Porcentaje impuestos*",
        "Impuesto*",
        "Descuento*",
        "Fecha inicio*",
        "Fecha fin*",
        "Tipo de pago*"
    ]
    
    API_URL = "https://eu1.getpulpo.com/api/v1/scheduled-expenses/"

    def __init__(self, file_path):
        """
        Inicializa el objeto cargador con la ruta del archivo a procesar.
        """
        self.file_path = file_path
        self.data = None
        self.api_token = self.fake_load_env_variable('API_TOKEN')
        self.date_transformer = DateTransform()
        self.process_not_complete_file = "not_processed.csv"

    def fake_load_env_variable(self, var_name):
        """
        Carga el valor de una variable de entorno desde el archivo .env.
        """
        try:
            with open('.env', 'r') as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split('=', 1)
                        if key.strip() == var_name:
                            return value.strip()
                raise ValueError(f"Variable de entorno {var_name} no encontrada en el archivo .env.")
        except FileNotFoundError:
            raise ValueError(".env file no encontrado en el directorio actual.")
        except Exception as e:
            raise ValueError(f"Error al leer el archivo .env: {e}")

    def validate_token(self):
        """
        Verifica si el token de API es válido.
        """
        if not self.api_token:
            raise ValueError("Token de autorización no encontrado o vacío.")
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        try:
            response = requests.get(self.API_URL, headers=headers)
            if response.status_code == 200:
                print("Token válido.")
            else:
                raise ValueError(f"Token inválido. Código de respuesta: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error al verificar el token: {e}")
            raise ValueError("Error al validar el token.")

    def load_file(self):
        """
        Carga el archivo CSV o XLSX desde la ruta proporcionada.
        """
        try:
            if self.file_path.endswith('.csv'):
                self.data = pd.read_csv(self.file_path, quotechar='"')
            elif self.file_path.endswith('.xlsx'):
                self.data = pd.read_excel(self.file_path)
            else:
                raise ValueError("El archivo debe ser un CSV o XLSX.")
        except Exception as e:
            raise RuntimeError(f"Error al cargar el archivo: {e}")
        self.data.columns = self.data.columns.str.strip()

    def validate_columns(self):
        """
        Valida que todas las columnas requeridas estén presentes en el archivo.
        """
        if self.data is None:
            raise ValueError("No se ha cargado ningún archivo.")
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in self.data.columns]
        if missing_columns:
            raise ValueError(f"Faltan las siguientes columnas en el archivo: {', '.join(missing_columns)}")

    def process_data(self):
        """
        Procesa los datos, aplicando la transformación necesaria a las fechas.
        """
        processed_data = []
        for index, row in self.data.iterrows():
            item = {
                "name": str(row.get('Contrato*', '')),
                "expenseTypeId": self.map_expense_type(row.get('Propiedad*', '')),
                "subtotal": self.convert_to_numeric(row.get('Cuota recurrente total*')),
                "total": self.convert_to_numeric(row.get('Cuota recurrente total*')),
                "taxType": row.get('Porcentaje impuestos*', ''),
                "tax": self.convert_to_numeric(row.get('Impuesto*')),
                "discountType": row.get('Porcentaje impuestos*', ''),
                "discount": self.convert_to_numeric(row.get('Descuento*')),
                "startDate": self.date_transformer.convert_to_iso_format(row.get('Fecha inicio*')),
                "endDate": self.date_transformer.convert_to_iso_format(row.get('Fecha fin*')),
                "frecuency": self.map_frecuency(row.get('Tipo de pago*', '')),
            }
            processed_data.append(item)
            
            percentage = (index + 1) / len(self.data) * 100
            print(f"Progreso: {percentage:.2f}%")
        
        return processed_data

    def generate_csv(self, output_file):
        """
        Genera un archivo CSV con los datos procesados.
        """
        processed_data = self.process_data()
        df = pd.DataFrame(processed_data)
        df.to_csv(output_file, index=False, quoting=1)
        print(f"Archivo CSV generado: {output_file}")

    def send_to_api(self, data):
        """
        Envía los datos procesados a la API.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        successful_count = 0
        total_count = len(data)
        failed_items = []

        for idx, item in enumerate(data):
            try:
                response = requests.post(self.API_URL, headers=headers, data=json.dumps(item), timeout=10)
                if response.status_code == 201:
                    successful_count += 1
                    print(f"Expense created successfully: {item['name']}")
                else:
                    print(f"Failed to create expense: {response.status_code} - {response.text}")
                    if response.status_code == 400:
                        print(f"Error details: {response.json()}")
                    failed_items.append(item)  # Agregar el item a la lista de fallidos
            except requests.exceptions.RequestException as e:
                print(f"Error al enviar la solicitud a la API: {e}")
                failed_items.append(item)  # Agregar el item a la lista de fallidos
            
            percentage = (idx + 1) / total_count * 100
            print(f"Progreso: {percentage:.2f}%")

        if failed_items:
            self.save_failed_items(failed_items)

        print(f"\nTotal: {total_count} | Successful: {successful_count} | Failed: {len(failed_items)}")

    def save_failed_items(self, failed_items):
        """
        Guarda los elementos que no pudieron ser procesados en un archivo CSV.
        """
        df_failed = pd.DataFrame(failed_items)
        df_failed.to_csv(self.process_not_complete_file, index=False, quoting=1)
        print(f"Archivo con elementos no procesados guardado en: {self.process_not_complete_file}")

    def map_expense_type(self, value):
        """
        Mapea el tipo de propiedad a su correspondiente ID en la API.
        """
        value = value.strip().lower()
        if 'renting' in value:
            return 74093
        elif 'leasing' in value:
            return 74084
        else:
            return None

    def map_frecuency(self, value):
        """
        Mapea el tipo de frecuencia a su formato correspondiente.
        """
        value = value.strip().lower()
        if 'dia' in value:
            return "day"
        elif 'semana' in value:
            return "week"
        elif 'mes' in value:
            return "month"
        elif 'año' in value:
            return "year"
        else:
            return None

    def convert_to_numeric(self, value):
        """
        Convierte una cadena a un valor numérico (flotante), eliminando caracteres innecesarios.
        """
        if value is None or value == "":
            return None
        value = str(value).strip()
        value = value.replace(',', '')
        value = value.replace('€', '')
        value = value.replace('$', '')
        try:
            return float(value)
        except ValueError:
            return None

    def process_failed_items(self):
        """
        Reprocesa los elementos fallidos desde el archivo 'not_processed.csv'.
        """
        if not os.path.exists(self.process_not_complete_file):
            print("No hay elementos para reprocesar.")
            return
        
        df_failed = pd.read_csv(self.process_not_complete_file)
        failed_items = df_failed.to_dict(orient="records")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        for idx, item in enumerate(failed_items):
            try:
                response = requests.post(self.API_URL, headers=headers, data=json.dumps(item), timeout=10)
                if response.status_code == 201:
                    print(f"Reprocessed expense created successfully: {item['name']}")
                else:
                    print(f"Failed to reprocess expense: {response.status_code} - {response.text}")
                time.sleep(0.2)  # Espera de 200ms
            except requests.exceptions.RequestException as e:
                print(f"Error al reprocesar la solicitud a la API: {e}")
                continue

def main():
    # Ruta del archivo que se quiere procesar
    file_path = "R_L-Bot-Template.xlsx"
    
    # Crear una instancia de RentingLeasingLoader
    loader = RentingLeasingLoader(file_path)
    
    try:
        # Cargar el archivo
        loader.load_file()
        
        # Validar las columnas requeridas
        loader.validate_columns()
        
        # Generar el CSV con los datos procesados
        output_file = "processed_data.csv"
        loader.generate_csv(output_file)
        
        # Procesar y enviar los datos a la API
        processed_data = loader.process_data()
        loader.send_to_api(processed_data)
        
        print(f"Archivo procesado con éxito y enviado a la API.")
    
    except ValueError as ve:
        print(f"Error de validación: {ve}")
    except RuntimeError as re:
        print(f"Error de carga de archivo: {re}")
    except Exception as e:
        print(f"Error inesperado: {e}")

# Ejecutar la función main si el archivo se ejecuta directamente
if __name__ == "__main__":
    main()
