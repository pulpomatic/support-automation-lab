# Script para Combinar Archivos Excel en CSV o XLSX
## Descripción
Este script en Python está diseñado para combinar múltiples archivos Excel (.xls y .xlsx) en un solo archivo de salida. Los archivos Excel deben estar ubicados en una carpeta llamada files, y el archivo final se generará en una carpeta llamada processed.

El usuario puede elegir el formato del archivo de salida (CSV o XLSX) y el nombre del archivo generado. El script lee únicamente la primera hoja de cada archivo Excel y combina los datos, preservando el formato original.

## Requisitos Previos
Antes de ejecutar el script, asegúrate de tener instaladas las siguientes dependencias:

Python 3.x

## Paquetes de Python necesarios (puedes instalarlos con pip):
```bash
- pip install pandas openpyxl 
```
## Instrucciones de Uso
Ubica los archivos Excel (.xls y .xlsx) que deseas combinar en la carpeta `files`.

Ejecuta el script desde la terminal:

```bash
python combine_excel.py
```

Responde a las preguntas que aparecerán en la terminal:

Selecciona el formato del archivo de salida:
- Escribe 1 para CSV.
- Escribe 2 para XLSX.
- Ingresa el nombre del archivo final (sin la extensión).
- El archivo combinado se guardará en la carpeta processed con el nombre y formato que seleccionaste.
