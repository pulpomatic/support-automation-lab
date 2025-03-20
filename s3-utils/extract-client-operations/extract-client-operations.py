import re
import sys
import os
import json
import csv
import time
import threading
from datetime import datetime
from io import StringIO
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

import boto3

# Configuración de conexión a S3
s3_client = boto3.client('s3')
bucket_name = 'sftp-getpulpo-eu-production'
processed_path = 'Repsol/processed/'
to_reprocess_path = 'Repsol/to-reprocess/'

# Ruta para el archivo consolidado
processed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')

# Lock para acceso a la estructura de datos compartida
data_lock = threading.Lock()

# Estructura de datos para almacenar filas filtradas
filtered_rows = {
    'header': None,
    'data': []
}

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

def load_accounts_filter():
    """Cargar los IDs de cuenta desde el archivo accounts.json."""
    try:
        with open('accounts.json', 'r') as f:
            accounts = json.load(f)
            if not isinstance(accounts, list):
                raise ValueError("El archivo accounts.json debe contener un array de strings.")
            return set(accounts)  # Usamos un set para búsquedas más rápidas
    except FileNotFoundError:
        print("Error: No se encontró el archivo accounts.json")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: El archivo accounts.json no contiene un JSON válido")
        sys.exit(1)
    except Exception as e:
        print(f"Error al leer accounts.json: {e}")
        sys.exit(1)

def process_csv_stream(file_key, account_ids):
    """Procesar un archivo CSV usando streaming para minimizar el uso de memoria."""
    try:
        # Obtener el nombre del archivo para la columna filename
        filename = file_key.split('/')[-1]
        
        # Obtener el objeto S3
        s3_obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        
        # Preparar para el procesamiento en streaming
        chunk_size = 1024 * 1024  # 1MB chunks
        stream = s3_obj['Body']
        
        # Variables para el procesamiento
        remaining_data = ""
        header = None
        filtered_count = 0
        total_rows = 0
        first_chunk = True
        filtered_lines = []
        
        # Procesar el archivo en chunks
        while True:
            chunk = stream.read(chunk_size).decode('utf-8')
            if not chunk:
                break
            
            # Combinar datos restantes con el nuevo chunk
            data = remaining_data + chunk
            lines = data.split('\n')
            
            # El último elemento puede estar incompleto, guardarlo para el próximo ciclo
            if chunk:  # Si no es el último chunk
                remaining_data = lines.pop()
            else:
                remaining_data = ""
            
            # Procesar el encabezado en el primer chunk
            if first_chunk:
                header_line = lines[0]
                header = header_line.split(',')
                id_cuenta_idx = header.index('id_cuenta') if 'id_cuenta' in header else -1
                if id_cuenta_idx == -1:
                    print(f"Error: El archivo {file_key} no contiene la columna 'id_cuenta'")
                    return None
                
                lines = lines[1:]  # Saltar encabezado para procesamiento
                first_chunk = False
            
            # Procesar líneas
            for line in lines:
                if not line.strip():  # Ignorar líneas vacías
                    continue
                    
                total_rows += 1
                fields = line.split(',')
                
                # Si el campo id_cuenta está dentro del rango y en el set de cuentas
                if id_cuenta_idx < len(fields) and fields[id_cuenta_idx] in account_ids:
                    filtered_lines.append(line)
                    filtered_count += 1
        
        # Procesar los datos restantes si los hay
        if remaining_data:
            fields = remaining_data.split(',')
            if id_cuenta_idx < len(fields) and fields[id_cuenta_idx] in account_ids:
                filtered_lines.append(remaining_data)
                filtered_count += 1
                total_rows += 1
        
        print(f"Total de filas: {total_rows}, Filas filtradas: {filtered_count}")
        
        # Si no se filtraron filas, retornar None
        if filtered_count == 0:
            return None
        
        print(f"Filas filtradas del archivo {filename}: {filtered_count}")
        
        # En lugar de agregar a la estructura global, devolver los datos
        return {
            'header': header,
            'data': filtered_lines,
            'filename': filename
        }
        
    except Exception as e:
        print(f"Error al procesar {file_key}: {e}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Error al procesar el archivo: {e}")

def process_file(bucket, file_info):
    """Procesar un archivo: filtrar en streaming y añadir a la estructura de datos compartida."""
    file_key = file_info['Key']
    account_ids = file_info['account_ids']
    
    print(f"\nProcesando archivo: {file_key}")
    
    # Filtrar datos por IDs de cuenta usando streaming
    result = process_csv_stream(file_key, account_ids)
    if not result:
        print(f"No se encontraron filas para el archivo filtrado en {file_key}")
        return None
    
    return result

def process_files_parallel(bucket, files, account_ids, max_workers=4):
    """Procesar archivos en paralelo usando ProcessPoolExecutor."""
    successful = 0
    failed = 0
    all_filtered_data = []
    header = None
    
    # Añadir account_ids a cada diccionario de archivo
    for file in files:
        file['account_ids'] = account_ids
    
    # Crear una barra de progreso
    with tqdm(total=len(files), desc="Procesando archivos") as pbar:
        # Usar ProcessPoolExecutor para procesamiento paralelo
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Iniciar todas las tareas
            futures = {executor.submit(process_file, bucket, file): file for file in files}
            
            # Procesar resultados a medida que se completan
            for future in as_completed(futures):
                file = futures[future]
                try:
                    result = future.result()
                    if result:
                        # Guardar el primer encabezado que encontremos
                        if header is None and 'header' in result:
                            header = result['header']
                        
                        # Almacenar datos filtrados
                        all_filtered_data.append(result)
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"Error al procesar {file['Key']}: {str(e)}")
                    failed += 1
                finally:
                    pbar.update(1)
    
    # Consolidar todos los datos filtrados
    print("\nConsolidando datos filtrados...")
    filtered_rows['header'] = header + ['filename'] if header else None
    total_rows = 0
    
    for result in all_filtered_data:
        if not result or not result.get('data'):
            continue
            
        filename = result.get('filename', 'unknown')
        data = result.get('data', [])
        print(f"Añadiendo {len(data)} filas de {filename}")
        
        # Añadir cada línea con el nombre del archivo
        for line in data:
            if isinstance(line, str):
                line_list = line.split(',')
            else:
                line_list = line
                
            line_with_filename = line_list + [filename]
            filtered_rows['data'].append(line_with_filename)
            total_rows += 1
    
    print(f"Total de filas consolidadas: {total_rows}")
    return successful, failed

def save_consolidated_file(file_path):
    """Guardar todas las filas filtradas en un archivo CSV consolidado."""
    print(f"Intentando guardar archivo consolidado en {file_path}")
    print(f"Estado de datos: header={filtered_rows['header'] is not None}, filas={len(filtered_rows['data'])}")
    
    if not filtered_rows['header'] or not filtered_rows['data']:
        print("No hay datos para guardar en el archivo consolidado.")
        return False
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Escribir encabezado
            writer.writerow(filtered_rows['header'])
            # Escribir datos
            writer.writerows(filtered_rows['data'])
        
        print(f"Archivo guardado exitosamente: {file_path}")
        return True
    except Exception as e:
        print(f"Error al guardar el archivo consolidado: {e}")
        import traceback
        traceback.print_exc()
        return False

def upload_to_s3(local_file_path, s3_key):
    """Subir archivo a S3."""
    try:
        s3_client.upload_file(local_file_path, bucket_name, s3_key)
        print(f"Archivo subido exitosamente a S3: s3://{bucket_name}/{s3_key}")
        return True
    except Exception as e:
        print(f"Error al subir archivo a S3: {e}")
        return False

def format_size(size_in_bytes):
    """Convertir tamaño de bytes a MB y formatear."""
    return size_in_bytes / (1024 * 1024)

def main():
    # Cargar IDs de cuenta para filtrar
    account_ids = load_accounts_filter()
    print(f"Se cargaron {len(account_ids)} IDs de cuenta para filtrar")
    
    # Verificar/crear directorio para archivo consolidado
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
    
    # Pedir el nombre de la cuenta al usuario
    account_name = input("Ingrese el nombre de la cuenta (ej. servimatic): ").strip()
    if not account_name:
        print("El nombre de la cuenta no puede estar vacío.")
        sys.exit(1)
    
    # Pedir al usuario qué tipo de archivos quiere procesar
    print("\nSeleccione el tipo de archivos a procesar:")
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

    # Crear el nombre del archivo consolidado
    start_date_formatted = start_date.strftime('%Y%m%d')
    end_date_formatted = end_date.strftime('%Y%m%d')
    consolidated_filename = f"{selected_type}_{start_date_formatted}-{end_date_formatted}_{account_name}.csv"
    consolidated_file_path = os.path.join(processed_dir, consolidated_filename)
    s3_consolidated_key = f"{to_reprocess_path}{consolidated_filename}"
    
    print(f"Se creará el archivo consolidado: {consolidated_filename}")
    
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
    
    # Determinar número óptimo de workers basado en CPU y tamaño total
    cpu_count = os.cpu_count()
    recommended_workers = min(cpu_count if cpu_count else 4, max(2, min(8, len(matching_files))))
    
    # Permitir ajuste del número de procesos paralelos
    print(f"\nSe recomienda usar {recommended_workers} procesos en paralelo basado en su sistema")
    try:
        workers_input = input(f"Ingrese número de procesos paralelos [{recommended_workers}]: ").strip()
        max_workers = int(workers_input) if workers_input else recommended_workers
    except ValueError:
        max_workers = recommended_workers
        print(f"Valor inválido, usando {recommended_workers} procesos")

    # Pedir confirmación
    confirm = input("\n¿Deseas procesar estos archivos? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operación cancelada.")
        sys.exit()

    # Registrar tiempo de inicio
    start_time = time.time()
    
    # Procesar archivos en paralelo
    successful, failed = process_files_parallel(bucket_name, matching_files, account_ids, max_workers)
    
    # Verificar si se encontraron filas después del procesamiento
    print(f"\nEstado después del procesamiento: {len(filtered_rows['data'])} filas acumuladas")
    
    # Guardar el archivo consolidado
    if filtered_rows['data']:
        print("\nGuardando archivo consolidado...")
        if save_consolidated_file(consolidated_file_path):
            # Subir archivo consolidado a S3
            print(f"\nSubiendo archivo consolidado a S3: {s3_consolidated_key}")
            upload_to_s3(consolidated_file_path, s3_consolidated_key)
            
            # Mostrar información sobre el archivo consolidado
            file_size = os.path.getsize(consolidated_file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"\nArchivo consolidado generado:")
            print(f"- Local: {consolidated_file_path}")
            print(f"- S3: s3://{bucket_name}/{s3_consolidated_key}")
            print(f"- Tamaño: {file_size_mb:.2f} MB")
            print(f"- Total de filas (incluyendo encabezado): {len(filtered_rows['data']) + 1}")
        else:
            print("\nError al guardar el archivo consolidado.")
    else:
        print("\nNo se generó el archivo consolidado porque no se encontraron coincidencias.")
    
    # Mostrar tiempo total de ejecución
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    
    print(f"\nProceso completado en {int(minutes)} minutos y {int(seconds)} segundos.")
    print(f"Archivos procesados exitosamente: {successful}, no se encontro nada: {failed}")

if __name__ == "__main__":
    main()
