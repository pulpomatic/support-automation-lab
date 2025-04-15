
README - Script de Carga Masiva de Recordatorios
Descripción
Este script permite la carga masiva de recordatorios a partir de archivos Excel (XLSX/XLS). El script es capaz de procesar múltiples hojas dentro de un mismo archivo, mapear los datos a la estructura requerida por la API, y crear los recordatorios correspondientes en el sistema Pulpo.

Características Principales
Procesamiento de múltiples archivos desde una carpeta de pendientes
Soporte para múltiples hojas en cada archivo Excel
Validación y mapeo de datos antes de la creación de recordatorios
Reportes detallados de éxitos y errores en formato Excel
Manejo de excepciones para evitar fallos durante el procesamiento
Conservación de archivos originales para referencia futura
Requisitos
Python 3.6 o superior
Dependencias (instalar con pip install -r requirements.txt):
pandas
pytz
requests
python-dotenv
Configuración
El script utiliza un archivo .env en el mismo directorio para configurar las credenciales y URLs:

CopyInsert
BEARER_TOKEN=tu_token_aqui
BASE_URL=[https://eu1.getpulpo.com/api/v1](https://eu1.getpulpo.com/api/v1)
BASE_URL_V2=[https://eu1.getpulpo.com/api/v2](https://eu1.getpulpo.com/api/v2)
Estructura de Directorios
El script crea y utiliza los siguientes directorios:

/pending: Carpeta donde se deben colocar los archivos Excel a procesar
/processed: Carpeta donde se guardan los reportes de filas procesadas exitosamente
/error: Carpeta donde se almacenan los reportes de errores de procesamiento
/logs: Carpeta donde se guardan los logs JSON con información detallada
Formato del Archivo Excel
El archivo Excel debe contener al menos las siguientes columnas:

Nombre de la Tarea*: Título del recordatorio (obligatorio)
Descripción: Descripción del recordatorio (opcional)
Fecha Vto Tarea*: Fecha de vencimiento (obligatorio, formatos soportados: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)
Hora*: Hora de vencimiento (opcional, formatos: HH:MM, HH:MM:SS)
Prioridad*: Nivel de prioridad (Alta, Media, Baja)
Opciones: Tipo de entidad y nombre/identificador (Conductores o Vehículos)
Responsable de la Tarea: Nombre del responsable
Recordatorio: Tipo de notificación (Email, Notificación o ambos)
valor*: Valor de tiempo para la notificación
Unidad de tiempo de notificación: Unidad de tiempo (minutos, horas, días)
Uso
Coloca tus archivos Excel en la carpeta /pending
Ejecuta el script: python load-reminders-from-xlsx.py
El script te mostrará los archivos disponibles y te pedirá confirmación
Selecciona el modo de ejecución:
T: Modo de prueba (solo valida los datos sin crear recordatorios)
P: Modo de persistencia (crea los recordatorios en el sistema)
Para cada hoja en los archivos, podrás decidir si deseas procesarla
Modos de Ejecución
Modo de Prueba (T)
En este modo, el script:

Valida todas las filas para detectar errores de mapeo
Genera reportes de errores de mapeo
No crea recordatorios en el sistema
Es ideal para verificar el formato de tus datos antes de la carga real
Modo de Persistencia (P)
En este modo, el script:

Valida y procesa todas las filas
Crea los recordatorios en el sistema mediante llamadas a la API
Genera reportes tanto de éxitos como de errores
Es el modo que debes usar para la carga final de datos
Archivos de Salida
Por cada archivo procesado, el script puede generar:

Reporte de éxitos: Excel con las filas procesadas correctamente
Ubicación: /processed/[timestamp]_[nombre-archivo]_processed.xlsx
Incluye los IDs de los recordatorios creados
Reporte de errores de mapeo: Excel con las filas que fallaron en la validación
Ubicación: /error/[timestamp]_[nombre-archivo]_mapeo.xlsx
Incluye los mensajes de error específicos
Reporte de errores de procesamiento: Excel con las filas que fallaron al crear el recordatorio
Ubicación: /error/[timestamp]_[nombre-archivo]_errors.xlsx
Incluye los mensajes de error de la API
Log JSON: Archivo con información técnica detallada del procesamiento
Ubicación: /logs/[timestamp]_[nombre-archivo].json
Manejo de Errores
El script está diseñado para ser robusto ante errores comunes:

Errores de mapeo: Cuando el formato de los datos no es válido
Errores de procesamiento: Cuando la API rechaza la creación del recordatorio
Errores de formato de fecha/hora: Soporte para múltiples formatos
Campos vacíos o inválidos: Validación de todos los campos obligatorios
Extensión y Mantenimiento
Para modificar el comportamiento del script:

Añadir nuevos formatos de fecha: Editar los arrays date_formats en la función try_to_map
Modificar los mapeos: Editar los diccionarios en la parte superior del script (PRIORITY_LEVELS, ENTITY_TYPES, etc.)
Cambiar el formato del payload: Modificar la construcción del objeto recordatorio en la función try_to_map
Soporte
Para consultas o reportes de errores, contactar al equipo de desarrollo.

Desarrollado por el equipo de Pulpo para la automatización de carga de recordatorios.