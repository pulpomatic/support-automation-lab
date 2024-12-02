import re
import sys
from datetime import datetime

import boto3

# Configuración de conexión a S3
s3_client = boto3.client('s3')
bucket_name = 'sftp-getpulpo-eu-production'
processed_path = 'Repsol/processed/'
to_reprocess_path = 'Repsol/to-reprocess/'

# Expresiones regulares para buscar archivos
patterns = {
    "operaciones_liquidadas": re.compile(r"operaciones_combustible_liquidadas|operaciones_otros_liquidadas"),
    "delta_tarjetas": re.compile(r"delta_tarjetas")
}

# Subcarpetas específicas según tipo
subfolders = {
    "operaciones_liquidadas": ["REPSOL_SETTLED_FUELS", "REPSOL_SETTLED_EXPENSES"],
    "delta_tarjetas": ["REPSOL_PAYMENT_METHODS"]
}

# Configuración de rango de fechas
def is_within_date_range(folder_name, start_date, end_date):
    """Verificar si el nombre de la carpeta es una fecha válida y está dentro del rango."""
    try:
        folder_date = datetime.strptime(folder_name, '%d-%m-%Y')
        return start_date <= folder_date <= end_date
    except ValueError:
        return False

def list_folders(bucket, prefix):
    """Listar carpetas en la ruta especificada."""
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
    return [content.get('Prefix') for content in response.get('CommonPrefixes', [])]

def list_files(bucket, prefix):
    """Listar archivos en una carpeta especificada."""
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [
        {'Key': content['Key'], 'Size': content['Size']}
        for content in response.get('Contents', []) if content['Key'].endswith('.csv')
    ]

def find_matching_files(bucket, prefix, pattern, subfolder_list, start_date, end_date):
    """Buscar archivos que coincidan con los patrones en carpetas dentro del rango de fechas."""
    matching_files = []
    folders = list_folders(bucket, prefix)

    for folder in folders:
        folder_name = folder.replace(prefix, '').strip('/')
        if is_within_date_range(folder_name, start_date, end_date):
            for subfolder in subfolder_list:
                subfolder_prefix = f"{folder}{subfolder}/"
                files = list_files(bucket, subfolder_prefix)
                for file in files:
                    file_key = file['Key']
                    if pattern.search(file_key):
                        matching_files.append(file)
    return matching_files

def copy_file(bucket, source_key, destination_prefix):
    """Copiar archivo a la carpeta de reprocesamiento."""
    destination_key = f"{destination_prefix}{source_key.split('/')[-1]}"
    s3_client.copy_object(
        Bucket=bucket,
        CopySource={'Bucket': bucket, 'Key': source_key},
        Key=destination_key
    )
    print(f"Archivo copiado: {source_key} -> {destination_key}")

def format_size(size_in_bytes):
    """Convertir tamaño de bytes a MB y formatear."""
    return size_in_bytes / (1024 * 1024)

def main():
    # Pedir al usuario qué tipo de archivos quiere copiar
    print("Seleccione el tipo de archivos a copiar:")
    print("1. Operaciones liquidadas (combustible y otros)")
    print("2. Delta tarjetas")
    choice = input("Ingrese el número de su elección (1 o 2): ").strip()

    if choice == "1":
        selected_type = "operaciones_liquidadas"
    elif choice == "2":
        selected_type = "delta_tarjetas"
    else:
        print("Selección inválida. Finalizando.")
        sys.exit()

    # Pedir rango de fechas al usuario
    try:
        start_date_str = input("Ingrese la fecha de inicio (formato dd-mm-yyyy): ").strip()
        end_date_str = input("Ingrese la fecha de fin (formato dd-mm-yyyy): ").strip()
        start_date = datetime.strptime(start_date_str, '%d-%m-%Y')
        end_date = datetime.strptime(end_date_str, '%d-%m-%Y')
        if start_date > end_date:
            raise ValueError("La fecha de inicio no puede ser mayor a la fecha de fin.")
    except ValueError as e:
        print(f"Error en las fechas ingresadas: {e}")
        sys.exit()

    print(f"Buscando archivos desde: {start_date.strftime('%d-%m-%Y')} hasta {end_date.strftime('%d-%m-%Y')}")

    # Buscar archivos dentro del rango de fechas
    pattern = patterns[selected_type]
    subfolder_list = subfolders[selected_type]
    matching_files = find_matching_files(bucket_name, processed_path, pattern, subfolder_list, start_date, end_date)

    if not matching_files:
        print("No se encontraron archivos que coincidan con los patrones.")
        sys.exit()

    # Mostrar los archivos encontrados con sus tamaños
    total_size_mb = 0
    print("\nArchivos encontrados:")
    for file in matching_files:
        size_mb = format_size(file['Size'])
        total_size_mb += size_mb
        print(f"- {file['Key']} (Tamaño: {size_mb:.2f} MB)")

    # Mostrar el tamaño total
    print(f"\nTamaño total de archivos encontrados: {total_size_mb:.2f} MB")

    # Pedir confirmación
    confirm = input("\n¿Deseas copiar estos archivos a la carpeta 'to-reprocess'? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operación cancelada.")
        sys.exit()

    # Copiar archivos a la carpeta de reprocesamiento
    for file in matching_files:
        copy_file(bucket_name, file['Key'], to_reprocess_path)

    print("\nProceso completado.")

if __name__ == "__main__":
    main()
