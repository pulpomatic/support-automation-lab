# Copy s3 repsol files

Este script permite buscar y copiar archivos desde un bucket sftp de repsol en Amazon S3 según ciertos criterios. 
Puedes elegir entre dos tipos de archivos (`Operaciones liquidadas` y `Delta tarjetas`) y especificar un rango de fechas en el que se buscarán los archivos. 
Los archivos encontrados se copian a una carpeta de destino en el mismo bucket.

---

## Características

1. **Selección de archivos**:
    - **Operaciones liquidadas**: Archivos que contienen los patrones `operaciones_combustible_liquidadas` o `operaciones_otros_liquidadas`, almacenados en subcarpetas como `REPSOL_SETTLED_FUELS` y `REPSOL_SETTLED_EXPENSES`.
    - **Delta tarjetas**: Archivos que contienen el patrón `delta_tarjetas`, almacenados en subcarpetas como `REPSOL_PAYMENT_METHODS`.

2. **Rango de fechas personalizable**:
    - El usuario puede ingresar una fecha de inicio y fin en formato `dd-mm-yyyy`.
    - Los archivos se filtran según las carpetas nombradas por fecha dentro del bucket (por ejemplo: `s3://bucket-name/Repsol/processed/15-09-2024/`).

3. **Tamaños de archivos**:
    - El script muestra el tamaño de cada archivo en MB y la sumatoria del tamaño total de los archivos encontrados.

4. **Confirmación antes de copiar**:
    - El script pide confirmación antes de proceder con la copia de los archivos.

5. **Copia de archivos**:
    - Los archivos encontrados se copian a una carpeta destino especificada (`s3://bucket-name/Repsol/to-reprocess/`).

---

## Requisitos Previos

1. Python 3.6 o superior.
2. Paquete `boto3` instalado:
   ```bash
   pip install boto3

### Consideraciones
Este script está desarrollado para trabajar base a los archivos procesados por el ETLv1, es decir, si el ETLv1 ya ha dejado de funcionar
este script debera ser modificado para que busque los archivos en s3://sftp-getpulpo-eu-production/Repsol/processed/v2/raw/
