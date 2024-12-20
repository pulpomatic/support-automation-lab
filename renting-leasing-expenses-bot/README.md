# Expenses bot

## Descripción

El bot nos ayuda a subir de manera masiva los gastos de una cuenta.

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
* `v1/users`

**El archivo:**

El bot funciona con dos formatos de archivos:

* XLSX
* CSV

Dejamos dos archivos de ejemplo en [R_L-Bot-Template.csv](https://github.com/pulpomatic/support-automation-lab/blob/main/renting-leasing-expenses-bot/R_L-Bot-Template.csv) y 
[R_L-Bot-Template.xlsx](https://github.com/pulpomatic/support-automation-lab/blob/main/renting-leasing-expenses-bot/R_L-Bot-Template.xlsx) 

_Nota: El archivo debe de vivir al mismo nivel que `RentingLeasingLoader.py`_

## Formato
El bot válida que existan los siguientes campos en el archivo a subir:

* Nombre del gasto
* Tipo de gasto
* Fecha
* Hora
* Fecha inicio
* Fecha fin
* Frecuencia del gasto
* Subtotal
* Porcentaje descuento
* Porcentaje impuesto
* Descuento monetario
* Impuesto monetario
* Matricula
* Email
* Medio de pago
* Proveedor

_Nota: Podemos agregar esta información en el mismo archivo que se crea para la subida
de Renting y Leasing, pero el nombre de los `headers` deben de ser iguales (incluyendo el asterísco)._

## Ejecución

Para correr el programa una vez teniendo el archivo debemos de entrar a la cuenta y obtener
el `TOKEN` de la misma y modificar el `.env` para que tome el token de la cuenta.

```bash
python3 main.py <Ruta del archivo.csv/.xlsx>
```

El bot nos mostrará en pantalla el procesamiento del archivo junto con un procentaje:

```bash
python3 main.py R_L-Bot-Template.csv
Procesando filas:   0%|                                                    | 0/2 [00:00<?, ?fila/s]2024-12-20 10:09:33,884 - INFO - Realizando POST a https://eu1.getpulpo.com/api/v1/scheduled-expenses/
2024-12-20 10:09:33,884 - INFO - Body enviado: {'name': '2024/Diciembre/Test01-Renting/Bot', 'expenseTypeId': 74093, 'subtotal': 399.0, 'taxType': 'PERCENTAGE', 'tax': 16.0, 'discountType': 'PERCENTAGE', 'discount': 21.0, 'total': 365.64360000000005, 'userId': 269797, 'vehicleId': 2700975, 'paymentMethodId': 1873071, 'supplierId': 1, 'startDate': '2023-01-01T00:00:00.000Z', 'endDate': '2026-01-01T00:00:00.000Z', 'frecuency': 'year'}
2024-12-20 10:09:34,736 - INFO - Respuesta exitosa para la fila 1: 201
Procesando filas:  50%|██████████████████████                      | 1/2 [00:00<00:00,  1.17fila/s]2024-12-20 10:09:34,737 - INFO - Realizando POST a https://eu1.getpulpo.com/api/v1/scheduled-expenses/
2024-12-20 10:09:34,737 - INFO - Body enviado: {'name': '2024/Diciembre/Test01-Leasing/Bot', 'expenseTypeId': 74084, 'subtotal': 299.0, 'taxType': 'CURRENCY', 'tax': 30.0, 'discountType': 'CURRENCY', 'discount': 50.0, 'total': 279.0, 'userId': 269797, 'vehicleId': 2700975, 'paymentMethodId': 1873071, 'supplierId': 1, 'startDate': '2024-02-01T00:00:00.000Z', 'endDate': '2024-05-01T00:00:00.000Z', 'frecuency': 'month'}
2024-12-20 10:09:35,483 - INFO - Respuesta exitosa para la fila 2: 201
Procesando filas: 100%|████████████████████████████████████████████| 2/2 [00:01<00:00,  1.25fila/s]
Carga completa. Fin.
```

### Datos no procesados

Si hubiesen archivos que no se procesaron estarán en la carpeta: `errors/`

De esta manera podemos comentarle al CUSU en cuestión sobre esto o nosotros resolver
con previo acuerdo del CUSU de la cuenta.
