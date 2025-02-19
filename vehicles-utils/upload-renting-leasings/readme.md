# Descripción
Este script nos permite subir la información de Renting&Leasing de los clientes, su objetivo técnico es actualizar estos atributos
en los datos del cliente

Este script evaluará los datos antes de cargarlos y arrojará errores en el caso de que se presenten, los que sean éxitoso pasarán a cargarse

Al ser un script de actualización este sobrescribe los datos del vehículo, por ello,
es importante saber que cada vez que se corre este script los datos de renting&leasing se sobrescriben y se invalida la versión anterior,
así que, se puede dejar un rastro que no se desee, es bueno correr el script sin persistir los datos para corroborar que todo esté correcto para 
que la carga sea lo más limpia posible.

El script carga primero los datos de los vehículos y luego carga los datos de los gastos programados.

## Requisistos

- Tener activo el módulo de Renting&Leasing previamente
- Tener acceso a la cuenta con un usuario de soporte
- Asignarte zona horaria correspondiente a la del cliente
- Asignarte todos los segmentos (Requerido dependiendo el caso)
```sql
UPDATE accounts_users
SET segments = (SELECT array(select id from segments s where account_id = $account_id))
where account_id = $account_id and user_id in (select id from users where email = $email);
```

## Estructura del Proyecto

- `pending/`: carpeta donde se colocan los archivos de datos pendientes de procesar.
- `processed/`: carpeta donde se almacenan los archivos procesados con datos crudos exitosos.
- `error/`: carpeta donde se almacenan los archivos con datos crudos que generaron errores.
- `logs/`: carpeta que contiene un archivo de log generado para cada ejecución del script, detallando el proceso.

## Errores frecuentes

- Respuestas 502 de la API: Si la operación da este error al ser cargada, puedes repetir el proceso con el archivo de error
- Vehículos no encontrados: Cuando esto sucede debes verificar de que no sea un tema de permisos o segmentos, te recomiendo comprobar la existencia
yendo a la base de datos y consultando a ver si existen, en caso de que no hay que ir con el CuSu o el cliente para que los creen.

## Creación de Proveedores

En algunos casos te tocará dar de alta algunos proveedores, debido a que nuestra base de datos es limitada y no tenemos todos los proveedores mapeados
para ello podemos procesar el archivo en modo de pruebas y si fallan las filas por proveedor


## Estructura de Campos

Los campos del excel se enumeran de la siguiente manera:

1. `"Matrícula"` (Requerido)
2. `"Fecha inicio"` (Requerido)
3. `"Fecha fin"` (Requerido)
4. `"Propiedad"` (Requerido)
5. `"Referencia"`
6. `"Proveedor"` (Requerido)
7. `"Odómetro inicial"`
8. `"Kilometraje contratado"`
9. `"Kilometraje por año"`
10. `"Cuota inicial subtotal €"` (Solamente se utilizan si es Leasing)
11. `"Cuota inicial tipo de impuesto"` (Solamente se utilizan si es Leasing)
12. `"Cuota inicial impuesto"` (Solamente se utilizan si es Leasing)
13. `"Cuota inicial total €"` (Solamente se utilizan si es Leasing)
14. `"Cuota recurrente de empresa €"`
15. `"Cuota recurrente de empleado €"`
16. `"Cuota recurrente tipo de impuesto"`
17. `"Cuota recurrente impuesto"`
18. `"Cuota recurrente total €"`
19. `"Bonificación por km no recorrido"`
20. `"Penalización por km excedido"`
21. `"Permanencia mínima"`
22. `"Tipo de contrato"`
23. `"Tipo de pago"`
24. `"Vehículo de sustitución"`
25. `"Seguro"`
26. `"Servicio de telemetría"`
27. `"Mantenimiento preventivo"`
28. `"Mantenimiento correctivo"`
29. `"Asistencia de carretera"`
30. `"Gestión de trámites"`
31. `"Gestión de multas"`
32. `"Rotulación"`
33. `"Equipamiento"`
34. `"Valor del vehículo"`
35. `"Valor residual"`
36. `"Crear gasto programado"`

### Notas importantes:
- La primera fila debe contener la descripción de los tipos de campo, por eso siempre se hace skip
- Todos los campos son técnicamente opcionales, pero para el contexto de carga de Renting&Leasing es necesario tener los 
obligatorios en el excel, si no el script fallará y no tiene sentido hacer la carga.
- Algunas de estas propiedades se utilizan con el método **`row.get()`** para manejar valores opcionales (como `"Número de contrato"`, `"Permanencia mínima"`, etc.).
- Si el valor asociado a una clave es `None`, se suelen usar valores predeterminados (como `0` o `FALSE`, dependiendo del caso).
- Las fechas se procesan con los formatos y transformaciones necesarias (`pd.to_datetime` y conversión a ISO 8601 si es necesario).

## TODO

### 1. Preparación del archivo

1. Crear una nueva carpeta llamada `pending` aquí.
2. Colocar el archivo `.xlsx` en la carpeta `pending`. Puede tener cualquier nombre.
3. En el archivo `.xlsx` con toda la información de renting y leasing en la primera hoja (preferiblemente eliminar las demás)
4. Verificar que los valores como de fecha y número estén correctamente formateados y que no sean formato texto.
5. Las celdas vacías se considerarán como `null` y dependiendo del caso se asumirá un `0` o un valor vacío
6. Para columnas booleanas se recomienda que sean de tipo texto con los siguientes valores
   - TRUE
   - FALSE
7. Dependiendo de cada fila se puede crear un Gasto Programado, para ello la columna `crear gasto programado` debe tener TRUE, de lo contrario se asumirá false

### 2. Variables de entorno

- `BEARER_TOKEN` debe contener el token de la sesión de la cuenta a la cual se le van a cargar los datos.
- `BASE_URL` debe contener la url de la api de producción.

### 3. Ejecución

- Para ejecutar la carga masiva solo hace falta colocarse en esta ruta e iniciar con el siguiente comando:
```bash
python upload-renting-leasings.py
```

### 4. Actualizar Tareas

El script no está preparado para actualizar las tareas, por eso al finalizar la ejecución se sugiere revisar 
los reminders creados y cambiar el usuario asignado por los usuarios administradores de la cuenta, estos se definen en el ticket.
Ya que automáticamente se asignan al usuario del token de sesión que probablemente sea un usuario de Soporte.

Para cambiar el usuario es en dos lados:

Tabla reminders:
- Columna `responsible_id`: Colocar el id del usuario administrador, puede ser el principal o cualquiera de los admins.

Tabla user_reminders:
- Columna `user_id`: Colocar el id del usuario administrador.
- Si la cuenta tiene más usuarios administrador, igual puede ser duplicar los registros y asignar el `user_id` correspondiente.

Puedes ejecutar los sql que están en el archivo [update_reminders.sql](update_reminders.sql)

### 5. Validación de datos

Con la siguiente query puedes comprobar que los datos estén registrados correctamente, es simplemente comparar el conteo 
de bd con el del archivo de procesados

```sql
select 
	count(*) 
from vehicles_properties vp 
where 
	vp.account_id = 291251 
	and vp.created_at >= '2025-02-18' 
	and vp.created_by_user_id = 6
	and vp.is_active = true;
```