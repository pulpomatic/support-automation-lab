# Renting and Leasing bot

## Descripción

El bot nos ayuda a subir de manera masiva los gastos programados de Renting y Leasing
de una cuenta.

En particular (**exclusivamente**) trabajamos con los datos del siguiente 
formulario.

![image](https://github.com/user-attachments/assets/f6326c66-647e-43c4-af1b-530feddafedb)


## Requisitos

Debemos de tener instalado: 

* `Python: >= 3.13.0`
* `pip >= 24.2`

## Instalación

Una vez descargado el repositorio debemos de crear un [ambiente virtual](https://docs.python.org/3/library/venv.html) para poder instalar las dependencias
a través del manejador de paquetes `pip`.

Una vez tengamos el repositorio y nuestro ambiente virtual debemos de seguir el 
siguiente comando:

```bash
$ pip install -r requirements.txt
```

## Funcionamiento

El bot se alimenta de la API de Pulpo, en particular el siguiente
endpoint:

* `v1/scheduled-expenses/`

**El archivo:**

El bot funciona con dos formatos de archivos:

* XLSX
* CSV

Dejamos dos archivos de ejemplo en [R_L-Bot-Template.csv](https://github.com/pulpomatic/support-automation-lab/blob/main/renting-leasing-expenses-bot/R_L-Bot-Template.csv) y 
[R_L-Bot-Template.xlsx](https://github.com/pulpomatic/support-automation-lab/blob/main/renting-leasing-expenses-bot/R_L-Bot-Template.xlsx) 

_Nota: El archivo debe de vivir al mismo nivel que `RentingLeasingLoader.py`_

## Formato
El bot válida que existan los siguientes campos en el archivo a subir:

* Contrato*
* Propiedad*
* Cuota recurrente total*
* Porcentaje impuestos*
* Impuesto*	Descuento*
* Fecha inicio*
* Fecha fin*
* Tipo de pago*

Todos los campos con asterísco son obligatorios.

_Nota: Podemos agregar esta información en el mismo archivo que se crea para la subida
de Renting y Leasing, pero el nombre de los `headers` deben de ser iguales (incluyendo el asterísco)._

## Ejecución

Para correr el programa una vez teniendo el archivo debemos de entrar a la cuenta y obtener
el `TOKEN` de la misma y modificar el `.env` para que tome el token de la cuenta.

Debemos de tener un archivo como los dados en el ejemplo y modificar la siguiente linea:

```bash
file_path = "R_L-Bot-Template.xlsx"
```

Una vez hecho esto podemos correr el siguiente comando:

```bash
$ python3 RentingLeasingLoader.py
```

El bot nos mostrará en pantalla el procesamiento del archivo junto con un procentaje:

```bash
python3 RentingLeasingLoader.py
Token cargado.
Progreso: 50.00%
Progreso: 100.00%
Archivo CSV generado: processed_data.csv
Progreso: 50.00%
Progreso: 100.00%
Expense created successfully: 2024/Diciembre/Test01-Renting/Bot
Progreso: 50.00%
Expense created successfully: 2024/Diciembre/Test02-Leasing/Bot
Progreso: 100.00%

Total: 2 | Successful: 2 | Failed: 0
Archivo procesado con éxito y enviado a la API
```

### Datos no procesados

Si hubiesen archivos que no se procesaron tendrán el nombre: `not_processed.csv`

De esta manera podemos comentarle al CUSU en cuestión sobre esto o nosotros resolver
con previo acuerdo del CUSU de la cuenta.
