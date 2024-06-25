import os
import pandas as pd

def read_and_split_csv(folder_path, max_rows):
    """
    Lee todos los archivos CSV en el directorio especificado y los divide en múltiples archivos más pequeños, eliminando duplicados.

    Args:
    folder_path (str): La ruta del directorio que contiene los archivos CSV.
    max_rows (int): El número máximo de filas que deben contener los archivos CSV divididos.

    Description:
    - Esta función busca todos los archivos CSV en el directorio dado, los procesa uno por uno y los divide en varios archivos más pequeños basados en el límite de filas especificado.
    - Para cada archivo, se eliminan las filas duplicadas y se mantienen los registros únicos a lo largo de todo el proceso.
    - Los archivos resultantes se guardan en un subdirectorio 'chunked' dentro del directorio especificado.
    """
    # Crea la carpeta chunked si no existe
    chunked_folder = os.path.join(folder_path, "chunked")
    
    if not os.path.exists(chunked_folder):
        os.makedirs(chunked_folder)
    
    filenames = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
    total_files = len(filenames)
    
    if total_files == 0:
        print(f"No CSV files found in the folder {folder_path}. Please check the directory.")
        return

    print(f"Found {total_files} files. Starting processing...")

    for index, filename in enumerate(filenames):
        current_file_path = os.path.join(folder_path, filename)
        filename_without_ext = os.path.splitext(filename)[0]
        output_folder = os.path.join(chunked_folder, filename_without_ext)
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        print(f"Processing {filename}...")
        split_csv_file(current_file_path, output_folder, filename_without_ext, max_rows)
        
        print(f"Processed {index + 1}/{total_files} files.")


def split_csv_file(filepath, output_folder, base_filename, max_rows):
    """
    Procesa un archivo CSV, eliminando filas duplicadas y dividiéndolo en múltiples archivos más pequeños.

    Args:
    filepath (str): La ruta completa del archivo CSV a procesar.
    output_folder (str): La ruta del directorio donde se guardarán los archivos CSV resultantes.
    base_filename (str): El nombre base del archivo original (sin extensión), usado para nombrar los archivos resultantes.
    max_rows (int): El número máximo de filas que deben contener los archivos CSV divididos.

    Description:
    - Esta función lee el archivo CSV en chunks, elimina duplicados tanto dentro de los chunks como globalmente, y escribe cada chunk en un nuevo archivo CSV en el directorio especificado.
    - Utiliza un conjunto de hashes para recordar y verificar la unicidad de cada fila a lo largo de todos los chunks procesados, asegurando que no haya duplicados entre los archivos generados.
    - Los archivos generados llevan un sufijo numerado para indicar su secuencia.
    """
    chunk_count = 1
    unique_hashes = set()

    first_row = pd.read_csv(filepath, nrows=1)
    dtype_dict = {col: str for col in first_row.columns} # Para definir todas las columnas como string
    for chunk in pd.read_csv(filepath, chunksize=max_rows, dtype=dtype_dict):
        chunk.drop_duplicates(inplace=True)
        hashes = chunk.apply(lambda row: hash(tuple(row)), axis=1)
        chunk = chunk[~hashes.isin(unique_hashes)]
        unique_hashes.update(hashes.values)

        if not chunk.empty:
            output_file = os.path.join(output_folder, f"{base_filename}_part{chunk_count}.csv")
            chunk.to_csv(output_file, index=False)
            print(f"Generated file {output_file} with {len(chunk)} rows.")
            chunk_count += 1


def main():
    """
    Función principal que ejecuta el programa. Solicita al usuario la entrada de datos y llama a las funciones de procesamiento.

    Description:
    - Solicita al usuario el número máximo de filas por archivo.
    - Llama a la función read_and_split_csv para iniciar el procesamiento de los archivos en la carpeta './files'.
    """
    folder_path = './files'  # Modify as needed
    max_rows = int(input("Enter the maximum number of rows for new CSV files: "))
    read_and_split_csv(folder_path, max_rows)

if __name__ == "__main__":
    main()
