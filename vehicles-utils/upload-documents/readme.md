De forma externa hay que crear un archivo .csv que tenga dos columnas:

1.- Placa del vehículo.
2.- ID del vehículo de la tabla vehicles.

Ejemplo:
0029MTN	3003116
0046LNJ	3003092
0118LNJ	3003093

La ruta de este archivo deber colocarse en la variable de entorno CSV_PATH.

Crear una nueva carpeta en la ruta de BASE_DIR.
En esa carpeta crear carpetas donde el nombre de cada una sea equivalente a la Placa del vehículo (primera columna).
Dentro de cada una de esas carpetas colocar los archivos que se quieran subir.
