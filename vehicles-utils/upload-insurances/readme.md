## Requisitos Previos

### Instalación de Librerías

1. Instalar las librerías comunes de Pulpomatic:
   ```bash
   cd ../../libs
   pip install -e .
   ```
   Este paso es necesario para que el script pueda acceder a las funciones comunes como el logger y el cliente de la API.

2. Instalar las dependencias del script:
   ```bash
   pip install -r requirements.txt
   ```

## Estructura de Campos

Los campos del excel se enumeran de la siguiente manera:

1. `"Matrícula"` (Requerido)
2. `"Número de Poliza"` (Requerido)
3. `"Proveedor"` (Requerido)
4. `"Fecha inicio"` (Requerido)
5. `"Fecha fin"` (Requerido)
6. `"Frecuencia de Pago"` (Requerido)
7. `"Prima Subtotal"` (Requerido)
8. `"Tipo de Impuesto"`
9. `"% impuesto"` (Requerido)
10. `"Prima Total"` (Requerido)
11. `"Tipo De Seguro"` (Requerido)
12. `"Crear Gasto Programado"`

## 1.- Preparación del archivo

Crear una nueva carpeta llamda `pending` aquí.

Colocar el archivo `.xlsx` en la carpeta `pending`. Puede tener cualquier nombre.

En el archivo `.xlsx` tener una hoja con nombre `INSURANCES`.

Valores que sean de tipo fecha se recomienda que estén en formato `YYYY-MM-DD`

Las siguientes columnas deben tener un valor númerico 0 por defecto si no tienen valor:
- Prima Subtotal
- % impuesto
- Prima Total

Para columnas booleanas se recomienda que sean de tipo texto con los siguientes valores
- TRUE
- FALSE

## 2.- Variables de entorno

El `BEARER_TOKEN` debe contener el token de la sesión de la cuenta a la cual se le van a cargar los datos.

El `BASE_URL` debe contener la url de la api de producción.

## 3.- Ejecución

Para ejecutar la carga masiva solo hace falta colocarse en esta ruta e iniciar con el siguiente comando:

```bash
python upload-insurances.py
```

## 4.- Logs

Al finalizar la ejecución puedes ver:

Los errores en la carpeta `error`

Los logs en la carpeta `logs`

Los valores que sí se procesaron en la carpeta `processed`

## 5.- Recordatorios

Al finalizar la ejecución se sugiere revisar los reminders creados y cambiar el usuario asignado por los usuarios administradores de la cuenta.

Ya que automáticamente se asignan al usuario del token de sesión que probablemente sea un usuario de Soporte.

Para cambiar el usuario es en dos lados:

reminders:
- Columna `created_by_user_id`: Colocar el id del usuario administrador.
- Columna `responsible_id`: Colocar el id del usuario administrador.

user_reminders:
- Columna `user_id`: Colocar el id del usuario administrador.
- Si la cuenta tiene más usuarios administrador, igual puede ser duplicar los registros y asignar el `user_id` correspondiente.
