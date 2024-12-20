import os
import requests
import pandas as pd
import logging
from tqdm import tqdm
from datetime import datetime
from utils.expense_mapper import ExpenseMapper

class ExpensesLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.api_url = "https://eu1.getpulpo.com/api/v1/scheduled-expenses/"
        self.users_api_url = "https://eu1.getpulpo.com/api/v1/users"
        self.token = self.load_api_token()
        self.errors_dir = 'errors/'
        os.makedirs(self.errors_dir, exist_ok=True)
        
        # Configurar el logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("expenses_loader.log"),
                logging.StreamHandler()  # También mostrar en consola
            ]
        )
        self.logger = logging.getLogger()
        
        # Inicializar user_id_mapping
        self.user_id_mapping = self.fetch_user_id_mapping()

    def load_api_token(self, env_file_path=".env"):
        """Carga el token de la API desde un archivo .env."""
        try:
            with open(env_file_path, "r") as file:
                for line in file:
                    if line.startswith("API_TOKEN"):
                        return line.split('=')[1].strip()
            raise ValueError("API_TOKEN no encontrado en el archivo .env")
        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo {env_file_path} no se encuentra.")

    def validate_token(self) -> bool:
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(self.api_url, headers=headers)
        return response.status_code == 200

    def fetch_user_id_mapping(self):
        """Obtiene el mapeo de emails a IDs de usuario desde la API."""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            
            # Primera consulta para obtener el total de filas
            response = requests.get(f"{self.users_api_url}?skip=0&take=1", headers=headers)
            response.raise_for_status()
            total_rows = response.json().get('_metadata', {}).get('_total_rows', 0)
            
            if total_rows == 0:
                self.logger.warning("No se encontraron usuarios en la API.")
                return {}

            # Segunda consulta para obtener todos los usuarios
            response = requests.get(f"{self.users_api_url}?skip=0&take={total_rows}", headers=headers)
            response.raise_for_status()
            users = response.json().get('list', [])
            
            # Construir el diccionario de mapeo
            user_id_mapping = {
                user['email']: user['id']
                for user in users
                if user.get('email')  # Filtrar usuarios sin email
            }

            self.logger.info(f"User ID mapping obtenido: {user_id_mapping}")
            return user_id_mapping

        except requests.RequestException as e:
            self.logger.error(f"Error al obtener el mapeo de usuarios: {e}")
            return {}

    def map_rows(self, data_frame: pd.DataFrame) -> list:
        expense_mapper = ExpenseMapper()
        mapped_rows = []

        vehicle_id_mapping = {"ABC-123": 2700975}

        for _, row in data_frame.iterrows():
            def convert_date(date_str):
                if isinstance(date_str, str) and date_str.strip():
                    try:
                        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    except ValueError:
                        return None
                return None

            start_date = convert_date(row["Fecha inicio"])
            end_date = convert_date(row["Fecha fin"])

            user_id = self.user_id_mapping.get(row["Email"], None)
            vehicle_id = vehicle_id_mapping.get(row["Matricula"], None)

            # Obtener valores de impuesto y descuento
            tax_percentage = self.convert_to_numeric(row["Porcentaje impuesto"])
            tax_currency = self.convert_to_numeric(row["Impuesto monetario"])
            discount_percentage = self.convert_to_numeric(row["Porcentaje descuento"])
            discount_currency = self.convert_to_numeric(row["Descuento monetario"])

            # Asignar valores y tipos
            if tax_currency > 0:
                tax = tax_currency
                tax_type = "CURRENCY"
            elif tax_percentage > 0:
                tax = tax_percentage
                tax_type = "PERCENTAGE"
            else:
                tax = 0
                tax_type = "CURRENCY"

            if discount_currency > 0:
                discount = discount_currency
                discount_type = "CURRENCY"
            elif discount_percentage > 0:
                discount = discount_percentage
                discount_type = "PERCENTAGE"
            else:
                discount = 0
                discount_type = "CURRENCY"

            subtotal = self.convert_to_numeric(row["Subtotal"]) or 0
            client_total = self.calculate_total_expense(tax, tax_type, discount_type, discount, subtotal)
            frecuencia = expense_mapper.map_frequency(row["Frecuencia del gasto"])

            mapped_row = {
                "name": row["Nombre del gasto"],
                "expenseTypeId": expense_mapper.map_expense_type(row["Tipo de gasto"]),
                "subtotal": subtotal,
                "taxType": tax_type,
                "tax": tax,
                "discountType": discount_type,
                "discount": discount,
                "total": client_total,
                "userId": user_id,
                "vehicleId": vehicle_id,
                "paymentMethodId": 1873071,
                "supplierId": 1,
                "startDate": start_date,
                "endDate": end_date,
                "frecuency": frecuencia
            }

            mapped_rows.append(mapped_row)

        return mapped_rows

    @staticmethod
    def calculate_total_expense(tax, tax_type, discount_type, discount, subtotal):
        calculated_tax = 0
        calculated_discount = 0

        if discount_type == "PERCENTAGE":
            calculated_discount = (discount / 100) * subtotal
        elif discount_type == "CURRENCY":
            calculated_discount = discount

        subtotal_after_discount = subtotal - calculated_discount

        if tax_type == "PERCENTAGE":
            calculated_tax = (tax / 100) * subtotal_after_discount
        elif tax_type == "CURRENCY":
            calculated_tax = tax

        total = subtotal - calculated_discount + calculated_tax

        return total

    @staticmethod
    def convert_to_numeric(value):
        if isinstance(value, str):
            value = value.strip(" €$").replace(",", ".")
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def convert_to_percentage(value):
        if isinstance(value, str):
            value = value.strip(" €$").replace(",", ".")
        try:
            value = float(value)
            if value >= 1:
                return value / 100
            return value
        except (ValueError, TypeError):
            return 0
    
    def load_expenses(self):
        """Carga el archivo y procesa cada fila."""
        if not self.validate_token():
            print("Token no válido.")
            return
        
        if self.file_path.endswith('.xlsx'):
            data_frame = pd.read_excel(self.file_path)
        elif self.file_path.endswith('.csv'):
            data_frame = pd.read_csv(self.file_path)
        else:
            print("Formato de archivo no soportado.")
            return
        
        mapped_rows = self.map_rows(data_frame)
        
        failed_rows = []
        errors_file = os.path.join(self.errors_dir, f"errors_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx")
        
        with tqdm(total=len(mapped_rows), desc="Procesando filas", unit="fila") as pbar:
            for index, row in enumerate(mapped_rows):
                try:
                    self.logger.info(f"Realizando POST a {self.api_url}")
                    self.logger.info(f"Body enviado: {row}")
                    
                    response = requests.post(self.api_url, json=row, headers={'Authorization': f'Bearer {self.token}'})
                    
                    if response.status_code == 201:
                        self.logger.info(f"Respuesta exitosa para la fila {index + 1}: {response.status_code}")
                    else:
                        self.logger.error(f"Error al procesar la fila {index + 1}: {response.status_code} - {response.text}")
                        failed_rows.append(row)
                except Exception as e:
                    self.logger.error(f"Error al procesar la fila {index + 1}: {e}")
                    failed_rows.append(row)
                pbar.update(1)
        
        if failed_rows:
            error_df = pd.DataFrame(failed_rows)
            error_df.to_excel(errors_file, index=False)
            print(f"Errores guardados en {errors_file}")
        
        result_file = "processed_expenses.xlsx"
        data_frame.to_excel(result_file, index=False)
    
        print("Carga completa. Fin.")

    def log_failed_row(self, row, error_message):
        """Registra filas que fallaron con su error."""
        log_entry = {
            "row": row,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        with open(os.path.join(self.errors_dir, "failed_rows.log"), "a") as log_file:
            log_file.write(f"{log_entry}\n")
        self.logger.error(f"Fila fallida registrada: {log_entry}")