# Importador Manual de Gastos y Combustibles de Repsol

Este script permite procesar archivos Excel que son exportados desde misolred con datos de combustibles y gastos, mapeando la información de este proveedor para que Pulpo pueda ingerirla
enviándola a una API y generando registros de éxito o error en archivos separados. 
Está diseñado para procesar en paralelo varios registros a la vez, con pausas configurables entre cada batch, y generar archivos de log para cada ejecución.

⚠️Es muy importante considerar que esta carga no evalúa si ya fueron previamente ejecutadas o si esas operaciones existen, por lo tanto, cada vez que corras el script corres el riesgo de duplicar datos⚠️

## Requisitos Previos

### Instalación de Librerías

1. Instalar las librerías comunes de Pulpomatic:
   ```bash
   cd ../libs
   pip install -e .
   ```
   Este paso es necesario para que el script pueda acceder a las funciones comunes como el logger y el cliente de la API.

2. Instalar las dependencias del script:
   ```bash
   pip install -r requirements.txt
   ```

### Variables de Entorno

Crear un archivo `.env` que contenga:
- `BEARER_TOKEN`: Token de autenticación para la API
- `BASE_URL`: URL base de la API

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

## Configuración

Asegura estar asociado con un usuario a la cuenta destino, luego iniciar sesión, muy importante seleccionar la cuenta y copiarte el token,
este lo solicitará el script para poder cargar la información

Luego verificar que tengas todos los segmentos y por último configurar la zona horaria de tu usuario a Madrid.

Para configurar los segmentos a tu usuario puedes ejecutar el siguiente SQL
   ```sql
      UPDATE accounts_users
      SET segments = (SELECT array(select id from segments s where account_id = $account_id))
      where account_id = $account_id and user_id in (select id from users where email = $email);
   ```

## Ejecución

1. Coloca los archivos `.xls` o `.xlsx` que deseas procesar en la carpeta `pending`.
2. Ejecuta el script:
    ```bash
    python load-fuels-and-expenses-from-respol-xls.py
    ```
3. El script pedirá confirmación para procesar los archivos y un token de autorización para realizar las solicitudes a la API.
4. Considera ejecutar el script en modo de prueba colocando la T al inicio
5. Luego puedes ejecutar el script en modo P de persistir para que se guarde en nuestra base de datos
6. Los resultados se almacenarán en:
    - **processed/**: registros exitosos (en archivos crudos separados).
    - **error/**: registros con errores o fallos.
    - **logs/**: archivos de log detallados de cada ejecución.

_Hay que estar muy atento en los archivos procesados y los archivos de error, ya que puede darse el caso que una operación no se mapee correctamente o que la api de error,
haciendo que se te descuadre por completo la carga. 
Si hay registros que te dan error, puedes corregir lo que sea necesario y luego intentar cargarlos de nuevo con el archivo de error_

## Como comprobar que se cargaron bien las operaciones?

Esta parte no es complicada, una vez terminada la carga podemos hacer una sumatoria de la columna IMP_TOTAL en excel, esto nos dará un valor por ejemplo 50.000,
entonces luego corriendo este query:
```sql
   select count(e.*), sum(e.total) from expenses e where e.is_active is true and e.created_by_user_id = $user_id and e.account_id = $account_id and e.create_at >= $current_date;
```
Cambiando los parámetros 
- user_id: El usuario con el que generaste el token
- account_id: La cuenta
- current_date: La fecha en la que realizaste la carga

Podemos obtener un valor exactamente igual al del archivo, en este caso nos debería dar 50.000 y el conteo total de filas que tiene el archivo.

_Nota: En caso alterno debemos contabilizar los archivos procesados con éxito, ya que en el camino suele dar errores por mapeo o por procesamiento y nos puede dar falsos positivos_

## Errores frecuentes

- Respuestas 502 de la API: Si la operación da este error al ser cargada, puedes repetir el proceso con el archivo de error
- Vehículos o Medios de Pago no encontrados: Cuando esto sucede debes verificar de que no sea un tema de permisos o segmentos, puedes comprobar la existencia de ambos
yendo a la base de datos y consultando a ver si existen, en caso de que no hay que ir con el CuSu o el cliente para que los creen.

## Configuración de Logs

El archivo de log se crea en cada ejecución y se almacena en la carpeta `logs`. Los logs contienen:
- Mensajes de información sobre el progreso del procesamiento.
- Mensajes de error en caso de fallos en el mapeo de datos o en las solicitudes a la API.
