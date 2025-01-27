import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

from DriverLoader import DriverLoader

# Cargar las variables de entorno
load_dotenv()

class PulpoAPI:
    def __init__(self):
        self._load_env()
        self._validate_env_variables()
        self._set_headers()

    def _set_headers(self):
        """Configura los headers para las solicitudes."""
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }

    def _load_env(self):
        """Carga las variables de entorno."""
        self.bearer_token = os.getenv("BEARER_TOKEN")
        self.base_url = os.getenv("BASE_URL")
        self.assignments_endpoint = os.getenv("ASSIGNMENTS_ENDPOINT")
        self.vehicles_endpoint = os.getenv("VEHICLES_ENDPOINT")
        self.drivers_endpoint = os.getenv("DRIVERS_ENDPOINT")

    def _validate_env_variables(self):
        """Valida que las variables requeridas estén configuradas."""
        if not all([self.bearer_token, self.base_url, self.assignments_endpoint, self.vehicles_endpoint, self.drivers_endpoint]):
            raise EnvironmentError("Una o más variables del entorno no están configuradas correctamente.")

    def get_users(self):
        """Obtiene todos los usuarios de la API en una sola solicitud y filtra los que coinciden."""
        url = f"{self.base_url}{self.drivers_endpoint}?skip=0&take=1&userType=4"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        total_rows = data["_metadata"]["_total_rows"]
        print(f"Total de usuarios: {total_rows}")

        url = f"{self.base_url}{self.drivers_endpoint}?skip=0&take={total_rows}&userType=4"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        users = response.json()["list"]
        user_ids = {}

        for user in users:
            user_name = user.get("name", "").strip()
            user_email = user.get("email", "").strip()
            user_id = user.get("id")

            user_ids[user_id] = (user_name, user_email)

        return user_ids

    def get_vehicles(self):
        """Obtiene los IDs de los vehículos que coinciden con 'name' o 'registrationNumberV2'."""
        vehicles_ids = {}

        url = f"{self.base_url}{self.vehicles_endpoint}?skip=0&take=1"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        total_vehicles = data["_metadata"]["_total_rows"]
        print(f"Total de vehículos disponibles: {total_vehicles}")

        url = f"{self.base_url}{self.vehicles_endpoint}?skip=0&take={total_vehicles}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        vehicles = response.json().get("vehicles", [])

        for vehicle in vehicles:
            vehicle_id = vehicle.get("id")
            vehicle_name = vehicle.get("name")
            vehicle_registration = vehicle.get("registrationNumberV2", "").replace("-", "")

            vehicles_ids[vehicle_id] = {
                "name": vehicle_name,
                "registrationNumberV2": vehicle_registration
            }

        return vehicles_ids

    def post_assignment(self, vehicle_id, body):
        """
        Realiza un POST al endpoint de assignments.
        """
        # Limpiar el body eliminando los campos innecesarios
        body_cleaned = {key: value for key, value in body.items() if key not in ['vehicleId']}
        
        url = f"{self.base_url}{self.assignments_endpoint}{vehicle_id}"
        
        try:
            response = requests.post(url, json=body_cleaned, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al realizar el POST: {e}")
            print(f"URL del POST: {url}")
            print(f"Body enviado: {body_cleaned}")
            return None

def convert_to_iso_format(date_str):
    """
    Convierte una fecha en el formato 'DD/MM/YYYY' al formato ISO 8601 'YYYY-MM-DDTHH:MM:SS.sssZ'.
    """
    # Primero, parseamos la fecha en el formato DD/MM/YYYY
    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
    
    # Luego, la convertimos al formato ISO 8601
    return date_obj.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def build_assignment_body(row, user_id, vehicle_id):
    """
    Construye el body para la asignación basado en los datos del archivo y la API.

    :param row: Diccionario con los datos de la fila (CSV/XLSX).
    :param user_id: ID del usuario asignado.
    :param vehicle_id: ID del vehículo asignado.
    :return: Diccionario con el payload de la asignación.
    """
    # Convertir fechas y horas
    start_date = convert_to_iso_format(row['start_date'])
    end_date = None

    if row.get("end_date"):
        end_date = convert_to_iso_format(row['end_date'])

    # Crear el body con el user_id y el vehicle_id
    body = {
        "startDate": start_date,
        "endDate": end_date,  # endDate puede ser None, pero se convertirá a null en el siguiente paso
        "userId": user_id,
        "vehicleId": vehicle_id,
        "odometer": 0,
    }

    # Asegurarse de que None se convierta en null para JSON
    return {key: (None if value is None else value) for key, value in body.items()}

def process_assignments(file_data, user_ids, vehicles_data, api):
    """
    Procesa las asignaciones de conductores a vehículos y guarda los datos de usuarios no encontrados
    junto con los bodies generados en un archivo 'User_Not_Exists.txt'.
    """
    users_not_found = []
    total_assignments = len(file_data)
    processed_assignments = 0

    for row in file_data:
        conductor = row["name"].strip()
        email = row["email"].strip()
        matricula = row["vehicle"].strip()

        # Buscar el userId
        user_id = None
        for uid, (name, user_email) in user_ids.items():
            if name == conductor:  #user_email == email:
                user_id = uid
                break

        if not user_id:
            print(f"Error: No se encontró usuario para {conductor} ({email})")
            
            # Construir el body con datos vacíos ya que no hay usuario
            body = build_assignment_body(row, None, None)
            
            users_not_found.append(f"Usuario: {conductor} ({email}) - Asignación no procesada: {body}\n")
            continue

        # Buscar el vehicleId
        vehicle = None
        for vehicle_id, vehicle_info in vehicles_data.items():
            if matricula == vehicle_info["name"] or matricula.replace(" ", "").replace("-", "") == vehicle_info["registrationNumberV2"]:
                vehicle = vehicle_info
                vehicle_id = vehicle_id
                break

        if not vehicle:
            print(f"Error: No se encontró vehículo para matrícula {matricula}")
            continue

        # Generar el body para la asignación
        body = build_assignment_body(row, user_id, vehicle_id)

        # Realizar el POST para la asignación
        try:
            response = api.post_assignment(vehicle_id, body)
            if response:
                print(f"Asignación procesada para el usuario {conductor} y vehículo {matricula}")
            else:
                print(f"Error al procesar asignación para {conductor} y vehículo {matricula}")
        except Exception as e:
            print(f"Excepción al realizar el POST: {e}")

        # Incrementar el contador de asignaciones procesadas
        processed_assignments += 1
        
        # Mostrar barra de progreso
        percentage = (processed_assignments / total_assignments) * 100
        print(f"\rProcesando asignaciones: {processed_assignments}/{total_assignments} - {percentage:.2f}% completado", end="")

        # Esperar 200ms antes de la siguiente petición
        time.sleep(0.2)

    # Guardar los usuarios no encontrados
    if users_not_found:
        with open("User_Not_Exists.txt", "w") as file:
            for entry in users_not_found:
                file.write(entry)
        print(f"\nSe guardaron los datos en 'User_Not_Exists.txt'")

def main():
    archivo = 'Chubb-Asginaciones-Conductores.csv'
    pulpo_api = PulpoAPI()

    loader = DriverLoader(archivo)
    loader.load_file()
    loader.validate_columns()
    drivers_data = loader.process_data()

    user_ids = pulpo_api.get_users()
    vehicles_data = pulpo_api.get_vehicles()

    process_assignments(drivers_data, user_ids, vehicles_data, pulpo_api)


if __name__ == "__main__":
    main()
