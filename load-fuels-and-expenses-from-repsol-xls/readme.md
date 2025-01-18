# Importador Manual de Gastos y Combustibles de Repsol

Este script permite procesar archivos Excel que son exportados desde misolred con datos de combustibles y gastos, mapeando la información de este proveedor para que Pulpo pueda ingerirla
enviándola a una API y generando registros de éxito o error en archivos separados. 
Está diseñado para procesar en paralelo varios registros a la vez, con pausas configurables entre cada batch, y generar archivos de log para cada ejecución.

## Estructura del Proyecto

- `pending/`: carpeta donde se colocan los archivos de datos pendientes de procesar.
- `processed/`: carpeta donde se almacenan los archivos procesados con datos crudos exitosos.
- `error/`: carpeta donde se almacenan los archivos con datos crudos que generaron errores.
- `logs/`: carpeta que contiene un archivo de log generado para cada ejecución del script, detallando el proceso.

## Dependencias

Este script utiliza las siguientes librerías:
- `pandas`: para manipular y procesar archivos Excel.
- `requests`: para enviar datos a una API REST.
- `logging`: para registrar los eventos de cada ejecución en un archivo de log.
- `concurrent.futures`: para manejar procesamiento en paralelo.
- `pytz`: para la gestión de zonas horarias.
- `asyncio` y `functools`: para mejorar la gestión de concurrencia.

### Requisitos

- Python 3.7 o superior
- Librerías adicionales: `pandas`, `requests`, `pytz`
- Entorno que permita la instalación y ejecución de dependencias externas.

## Instalación

1. Clonar este repositorio o descargar el script.
2. Instalar las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3. Crear un archivo `.env` que contenga las variables correspondientes, consulta el `.env.example`

## Configuración

Asegurate de asociar un usuario a la cuenta destino, luego iniciar sesión, muy importante seleccionar la cuenta y copiarte el token,
este lo solicitará el script para poder cargar la información

## Ejecución

1. Coloca los archivos `.xls` o `.xlsx` que deseas procesar en la carpeta `pending`.
2. Ejecuta el script:
    ```bash
    python load-fuels-and-expenses-from-respol-xls.py
    ```
3. El script pedirá confirmación para procesar los archivos y un token de autorización para realizar las solicitudes a la API.
4. Considera asignar tu usuario a la cuenta a la cual vas a registrar operaciones antes de ejecutar el archivo
5. Opcionalmente, vas a tener que asignarte segmentos para poder ver todos los vehículos, para ello puedes ejecutar el siguiente SQL
```sql
   UPDATE accounts_users
   SET segments = (SELECT array(select id from segments s where account_id = $account_id))
   where account_id = $account_id and user_id in (select id from users where email = $email);
```
6. Los resultados se almacenarán en:
    - **processed/**: registros exitosos (en archivos crudos separados).
    - **error/**: registros con errores o fallos.
    - **logs/**: archivos de log detallados de cada ejecución.
7. Considera ejecutar el script en modo de prueba para verificar errores e inconsistencias, antes de persistir los combustibles y gastos.

## Configuración de Logs

El archivo de log se crea en cada ejecución y se almacena en la carpeta `logs`. Los logs contienen:
- Mensajes de información sobre el progreso del procesamiento.
- Mensajes de error en caso de fallos en el mapeo de datos o en las solicitudes a la API.

