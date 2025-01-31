import os
import requests
import csv
import mimetypes
import logging

from dotenv import load_dotenv
from requests.exceptions import HTTPError, Timeout, RequestException
from tqdm import tqdm

# Configuración del registro de errores
logging.basicConfig(
    filename="app.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.ERROR,
)

# Cargar variables de entorno
load_dotenv()

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

CSV_PATH = os.getenv("CSV_PATH")
BASE_DIR = os.getenv("BASE_DIR")

TIMEOUT = 40  # Timeout para las peticiones en segundos
ERROR_LOG_FILE = "failed_requests.txt"

BASE_URL = os.getenv("BASE_URL")


def save_failed_request(url, files):
    """Guarda la información de una solicitud fallida en un archivo .txt."""
    try:
        with open(ERROR_LOG_FILE, "a") as error_file:
            error_file.write(f"URL: {url}\n")
            error_file.write("Archivos:\n")
            for file_tuple in files:
                filename = file_tuple[1][0]
                error_file.write(f"- {filename}\n")
            error_file.write("\n")
    except Exception as e:
        logging.error(f"Error guardando la solicitud fallida: {e}")


def get_files_from_directory(directory):
    """Obtiene una lista de archivos en un directorio y sus subdirectorios."""
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            if os.path.isfile(full_path):
                files.append(
                    (
                        "files",
                        (
                            filename,
                            open(full_path, "rb"),
                            mimetypes.guess_type(filename)[0],
                        ),
                    )
                )
    return files


def make_request(url, files):
    """Realiza una solicitud POST a la API especificada."""
    try:
        response = requests.post(url, headers=HEADERS, files=files, timeout=TIMEOUT)
        if response.status_code == 201:
            print("Éxito:", response.status_code, response.text, "\n")
        else:
            logging.error(f"Error en la petición: {response.status_code}, URL: {url}")
            save_failed_request(url, files)
            print(f"Error en la petición: {response.status_code}, URL: {url}")
    except HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        save_failed_request(url, files)
        print(f"HTTP error occurred: {http_err}")
    except Timeout as timeout_err:
        logging.error(f"The request timed out: {timeout_err}")
        save_failed_request(url, files)
        print(f"The request timed out: {timeout_err}")
    except RequestException as req_err:
        logging.error(f"Other request exception: {req_err}")
        save_failed_request(url, files)
        print(f"Other request exception: {req_err}")
    finally:
        for file_tuple in files:
            file_tuple[1][1].close()  # Cerrar archivos para liberar recursos


def process_csv(csv_path, base_dir):
    """Procesa el archivo CSV y realiza las solicitudes API."""
    with open(csv_path) as csvfile:
        archivo = list(csv.reader(csvfile))
        total = len(archivo)

        with tqdm(total=total, desc="Procesando archivos") as progress_bar:
            for row in archivo:
                url = f"{BASE_URL}/documents/archives/VEHICLES/{row[1]}?path="
                directory = os.path.join(base_dir, row[0])
                if os.path.isdir(directory):
                    files = get_files_from_directory(directory)
                    if files:
                        make_request(url, files)
                progress_bar.update(1)


if __name__ == "__main__":
    process_csv(CSV_PATH, BASE_DIR)
