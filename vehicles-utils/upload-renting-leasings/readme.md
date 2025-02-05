## Preparación del archivo

Crear una nueva carpeta llamda `pending` aquí.

Colocar el archivo `.xlsx` en la carpeta `pending`. Puede tener cualquier nombre.

En el archivo `.xlsx` tener una hoja con nombre `RENTINGS`.

Valores que sean de tipo fecha se recomienda que estén en formato `YYYY-MM-DD`

Las siguientes columnas deben tener un valor númerico 0 por defecto si no tienen valor:
- Odónetro inicial
- Kilometraje contratado
- Kilometraje por año
- % impuestos
- Cuota de empresa €
- Cuota de empleado €
- Cuota recurrente total €

Para columnas booleanas se recomienda que sean de tipo texto con los siguientes valores
- TRUE
- FALSE

Si necesitas que la actualización de Renting también cree un Gasto Programado, agregar la columna `create scheduled expense` con valor TRUE

## Variables de entorno

El `BEARER_TOKEN` debe contener el token de la sesión de la cuenta a la cual se le van a cargar los datos.

El `BASE_URL` debe contener la url de la api de producción.

## Ejecución

Para ejecutar la carga masiva solo hace falta colocarse en esta ruta e iniciar con el siguiente comando:

```bash
python upload-renting-leasings.py
```

## Logs

Al finalizar la ejecución puedes ver:

Los errores en la carpeta `error`

Los logs en la carpeta `logs`

Los valores que sí se procesaron en la carpeta `processed`
