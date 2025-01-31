De forma externa hay que crear un archivo .csv que tenga dos columnas:

1.- Número de licencia del usuario.
2.- ID del usuario de la tabla users.

Ejemplo:
02248259D	1146774
02260484K	1146873
02283636N	1146874

La ruta de este archivo deber colocarse en la variable de entorno CSV_PATH.

Crear una nueva carpeta en la ruta de BASE_DIR.
En esa carpeta colocar todos los archivos que se quieran subir.
El nombre de los archivos debe de tener el siguiente formato:

`[license_number] [Nombre del archivo]`

Ejemplo:

`02248259D test.pdf`
