import logging
import os
from datetime import datetime


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