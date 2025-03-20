# Extract Client Operations

Utilidad para extraer y filtrar datos de operaciones específicas del bucket S3, filtrando por ID de cuenta y consolidando en un único archivo.

## Descripción

Este script permite:

1. Buscar archivos CSV de operaciones liquidadas o delta tarjetas en el bucket S3 `sftp-getpulpo-eu-production`
2. Filtrar los registros según los IDs de cuenta definidos en `accounts.json`
3. Consolidar todos los registros filtrados en un único archivo CSV con formato conveniente
4. Almacenar el archivo consolidado tanto localmente como en S3

## Requisitos

- Python 3.6+
- Acceso configurado a AWS S3
- Dependencias:
  ```
  boto3
  tqdm
  ```

## Configuración

1. Crear un archivo `accounts.json` con los IDs de cuenta a filtrar:
   ```json
   [
     "12345",
     "67890"
   ]
   ```

2. Asegurarse de tener configuradas las credenciales de AWS (a través de variables de entorno o archivo de configuración)

## Uso

```bash
python extract-client-operations.py
```

El script solicitará:

1. **Nombre de la cuenta**: Identificador de la cuenta (ej. "servimatic")
2. **Tipo de archivos**: 
   - Opción 1: Operaciones liquidadas (combustible y otros)
   - Opción 2: Delta tarjetas
3. **Rango de fechas**: Fechas de inicio y fin en formato dd-mm-yyyy
4. **Número de procesos paralelos**: Para optimizar el rendimiento

## Salida

El script generará:

- Un archivo consolidado local en la carpeta `processed/` con el formato:
  `{tipo}_{fecha_inicio}-{fecha_fin}_{nombre_cuenta}.csv`
- El mismo archivo en el bucket S3 en la ruta `Repsol/to-reprocess/`
- El archivo incluye una columna `filename` que indica el archivo original de cada registro

## Ejemplos de nombres de archivo generados

- `operaciones_liquidadas_20250220-20250320_servimatic.csv`
- `delta_tarjetas_20250220-20250320_servimatic.csv`

## Optimización

El script está optimizado para procesar archivos grandes mediante:
- Procesamiento en streaming para minimizar el uso de memoria
- Ejecución en paralelo para aprovechar múltiples CPU
- Barra de progreso para monitoreo del avance

## Notas

- Para archivos muy grandes, considere aumentar los recursos de la máquina
- Los archivos procesados mantienen la estructura original, con la adición de la columna `filename`
