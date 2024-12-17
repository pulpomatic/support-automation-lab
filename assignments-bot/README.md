# Driver's assigments bot

## Descripción

El bot nos ayuda a subir de manera masiva los datos asociados de un vehículo a 
un conductor.

En particular (**exclusivamente**) trabajamos con los datos del siguiente 
formulario.

![image](https://github.com/user-attachments/assets/cb937c6a-b458-495a-9445-14506232ea5b)

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

El bot se alimenta de las APIs de Pulpo, en particular de los siguientes 
endpoints:

* `v1/assignments/vehicles/`
* `v1/vehicles/`
* `v1/users/`

Consultamos la API de vehículos y de usuarios de la cuenta, esto para obtener 
los datos de todos los vehículos de la cuenta y todos los usuarios asociados a 
la cuenta.

Una vez hecha esta consulta almacenamos los datos en memoria y hacemos la 
validación con el archivo.

**El archivo:**

El bot funciona con dos formatos de archivos:

* XLSX
* CSV

Dejamos dos archivos de ejemplo en [test_data.csv](https://github.com/pulpomatic/support-automation-lab/blob/main/assignments-bot/test_data.csv) y 
[test_data.xlsx](https://github.com/pulpomatic/support-automation-lab/blob/main/assignments-bot/test_data.xlsx) 

_Nota: El archivo debe de vivir al mismo nivel que `PulpoAPI.py`_

De esta manera nuestro bot hace dos comparaciones particulares con el archivo y 
los datos obtenidos:

### Conductores

Como en nuestro archivo tenemos dos campos que nos ayudan a obtener el 
conductor:

* Nombre
* Email

El bot tendrá que verificar si los datos obtenidos hacen match con ambos campos.

### Vehículos

El caso de vehículos se puede parecer al de conductores, pero lo que hacemos es 
verificar si el campo de la matricula en el archivo viene exactamente igual que 
en el campo nombre obtenido por la API. En caso de no hacerlo entonces nos 
apoyamos de `registrationNumberV2` que es un campo que previamente limpio la
matricula antes de almacenarla, por lo que nos asegura que en este campo la
matricula viene sin guiones o espacios.

## Ejecución

Para correr el programa una vez teniendo el archivo debemos de entrar a la cuenta y obtener
el `TOKEN` de la misma y modificar el `.env` para que tome el token de la cuenta.

Lo siguiente que debe hacer es modificar el nombre del archivo en la función `main()`.

Una vez hecho esto podemos correr el siguiente comando:

```bash
$ python3 PulpoAPI.py
```

El bot nos mostrará en pantalla el procesamiento del archivo junto con un procentaje:

```bash
python3 PulpoAPI.py
Total de usuarios: 314
Total de vehículos disponibles: 324
Asignación procesada para el usuario ALEJANDRO PALACIOS VALENCIA y vehículo 0029MTN
Procesando asignaciones: 1/330 - 0.30% completado
Asignación procesada para el usuario MARCOS HERRERA MUÑOZ y vehículo 0046LNJ
Procesando asignaciones: 2/330 - 0.61% completado
Asignación procesada para el usuario ROBERTO LEON RODRIGUEZ y vehículo 0118LNJ
Procesando asignaciones: 3/330 - 0.91% completado
Asignación procesada para el usuario LUIS GONZALO GIL AÑON y vehículo 0134LNJ
Procesando asignaciones: 4/330 - 1.21% completado
Asignación procesada para el usuario JOSE MANUEL JIMENEZ OSTOS y vehículo 0196LCM
Procesando asignaciones: 5/330 - 1.52% completado
Asignación procesada para el usuario JORGE BENITO BEATOVE y vehículo 0214LNT
Procesando asignaciones: 6/330 - 1.82% completado
Asignación procesada para el usuario ANDRES ALBERTO CASTELLANOS QUINTANA y vehículo 0218-KYZ
Procesando asignaciones: 7/330 - 2.12% completado
Asignación procesada para el usuario CARLES GARCIA MOLINA y vehículo 0236LNT
Procesando asignaciones: 8/330 - 2.42% completado
Asignación procesada para el usuario DIEGO ROMERO CAMPO y vehículo 0241LNT
Procesando asignaciones: 9/330 - 2.73% completado
Asignación procesada para el usuario ROBERTO MIGUEL SIERRA y vehículo 0252LNT
Procesando asignaciones: 10/330 - 3.03% completado
Asignación procesada para el usuario ALBERTO PAMPLONA GARCIA y vehículo 0252MBZ
Procesando asignaciones: 11/330 - 3.33% completado
Asignación procesada para el usuario JUAN CARLOS RODRIGUEZ RODRIGUEZ y vehículo 0273LNT
Procesando asignaciones: 12/330 - 3.64% completado
Asignación procesada para el usuario FRANCISCO JAVIER SANZ GARCIA y vehículo 0282MBZ
Procesando asignaciones: 13/330 - 3.94% completado
Asignación procesada para el usuario BEATRIZ ANDRES GARCIA y vehículo 0303MKJ
Procesando asignaciones: 14/330 - 4.24% completado
Asignación procesada para el usuario CONSTANTIN POPICA y vehículo 0319MBZ
Procesando asignaciones: 15/330 - 4.55% completado
Asignación procesada para el usuario VICTOR FILGUEIRA GONZALEZ y vehículo 0320MJD
Procesando asignaciones: 16/330 - 4.85% completado
Asignación procesada para el usuario JORDI PORQUERES COCHS y vehículo 0351MJD
Procesando asignaciones: 17/330 - 5.15% completado
Asignación procesada para el usuario PEDRO BAYER SILVENTE y vehículo 0353MJD
Procesando asignaciones: 18/330 - 5.45% completado
Asignación procesada para el usuario DANIEL ARRO RUIZ y vehículo 0354MJD
Procesando asignaciones: 19/330 - 5.76% completado
Asignación procesada para el usuario OLGA RUZOLA GOMEZ y vehículo 0359MJD
Procesando asignaciones: 20/330 - 6.06% completado
Asignación procesada para el usuario JUAN AGUILELLA MADRID y vehículo 0452LNS
```

### Datos no procesados

Si el conductor no existe en la aplicación, entonces mandará un mensaje de error y nos 
devolverá al final de la ejecución un archivo llamado `User_Not_Exists.txt`
Con el siguiente formato:

```bash
Usuario: JUAN CARLOS RODRIGUEZ GARCIA (juancarlos.rodriguez2@chubbfs.com) - Asignación no procesada: {'startDate': '2024-08-14T00:00:00.000Z', 'endDate': None, 'userId': None, 'vehicleId': None, 'odometer': 0}
Usuario: JUAN CARLOS RODRIGUEZ GARCIA (juancarlos.rodriguez2@chubbfs.com) - Asignación no procesada: {'startDate': '2024-08-14T00:00:00.000Z', 'endDate': None, 'userId': None, 'vehicleId': None, 'odometer': 0}
```

De esta manera podemos comentarle al CUSU en cuestión sobre esto o nosotros crear el 
usuario con previo acuerdo del CUSU de la cuenta.


### Pasos siguientes

Conectar el bot con:

* Medios de pago.
* Vehículo.

