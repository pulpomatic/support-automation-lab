import boto3
import pandas as pd
from botocore.exceptions import NoCredentialsError

def list_aws_config():
    """
    Lista la configuración actual de AWS, incluyendo las credenciales y el entorno.
    """
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        current_credentials = credentials.get_frozen_credentials() if credentials else "No credentials"
        print("AWS Configuration:")
        print(f"Access Key: {current_credentials.access_key}")
        print(f"Secret Key: {current_credentials.secret_key}")
        print(f"Session Token: {current_credentials.token if current_credentials.token else 'None'}")
        print(f"Region: {session.region_name}")
    except NoCredentialsError:
        print("No valid AWS credentials found.")

def list_csv_files(bucket_name, prefix):
    """
    Lista todos los archivos CSV en un bucket de S3 bajo un prefijo especificado.

    Args:
    bucket_name (str): Nombre del bucket de S3.
    prefix (str): Prefijo dentro del bucket bajo el cual buscar archivos CSV.

    Returns:
    list of str: Lista de claves de los archivos CSV encontrados.
    """
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    files = [item['Key'] for item in response.get('Contents', []) if item['Key'].endswith('.csv')]
    return files

def confirm_process():
    """
    Solicita al usuario confirmación para continuar con el proceso.

    Returns:
    bool: True si el usuario confirma, False en caso contrario.
    """
    response = input("Files listed above. Continue with the process? (y/n): ")
    return response.lower() == 'y'

def clean_csv_files(bucket_name, files, prefix):
    """
    Procesa y limpia archivos CSV duplicados, guardando los resultados en una carpeta 'cleaned' en S3.

    Args:
    bucket_name (str): Nombre del bucket de S3.
    files (list of str): Lista de claves de archivos para procesar.
    prefix (str): Prefijo base donde se guardarán los archivos limpios.
    """
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    for index, file_key in enumerate(files):
        print(f"({index + 1}/{len(files)}) Processing {file_key}")
        obj = bucket.Object(file_key)
        first_row = pd.read_csv(obj.get()['Body'], nrows=1)
        dtype_dict = {col: str for col in first_row.columns} # Para definir todas las columnas como string
        data = pd.read_csv(obj.get()['Body'], dtype=dtype_dict)
        initial_rows = len(data)
        data.drop_duplicates(inplace=True)
        cleaned_rows = len(data)
        

        # Crear nueva clave para el archivo limpio
        new_key = f"{prefix}/cleaned/{file_key.split('/')[-1].replace('.csv', '_cleaned.csv')}"
        bucket.put_object(Key=new_key, Body=data.to_csv(index=False))
        print(f"({index + 1}/{len(files)}) files processed. Initial rows: {initial_rows}, Rows after clean: {cleaned_rows}")

def main():
    list_aws_config()
    bucket_name = input("Enter the S3 bucket name: ")
    prefix = input("Enter the relative path (prefix) within the bucket: ")
    files = list_csv_files(bucket_name, prefix)
    
    if files:
        for idx, file in enumerate(files):
            print(f"{idx + 1}. {file}")
        if confirm_process():
            print('Process confirmet, starting to clean')
            clean_csv_files(bucket_name, files, prefix)
        else:
            print("Process canceled by the user.")
    else:
        print("No CSV files found at the specified location.")

if __name__ == "__main__":
    main()
