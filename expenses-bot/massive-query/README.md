# Actualización de proveedores y matrículas

Para no hacer que el bot cierre la conexión, decidimos crear este proceso
extra en el cual debemos de obtener únicamente los ids y nombres de los 
proveedores y matrículas.

### CSV
Creamos un archivo CSV con los siguientes datos obtenidos en el Excel del 
cliente:

```csv
expense_name,name,supplier
2023/PRENT0101,5603-MTV,AUTOCENTER
2023/R1450,9032 PLQ,BANSACAR
```
### Enumeración de matrículas
Obtenemos las matriculas y sus ids del archivo Excel con la siguiente query:

```sql
SELECT v.registration_number_v2, v.id 
FROM vehicles v 
WHERE v.account_id = :core_account_id -- Cambiarlo por el de la cuenta.
AND v."name" IN (
    '5603-MTV',
    '9032 PLQ'
);
```

Los datos obtenidos los debemos de transformar a una enumeración válida de 
Python.

### Enumeración proveedores
Obtenemos las matriculas y sus ids del archivo Excel con la siguiente query:

```sql
SELECT s.id, s."name"
FROM suppliers s 
WHERE s.supplier_type_id IN (
    71214,
    71215
)
AND s.suppliers_group_id IN (
    1, -- Proveedores de Repsol.
    6992, -- Proveedores de Renting/Leasing Repsol.
    8328, -- Proveedores de Seguros Repsol.
    ... -- Podemos agregar más grupos, en particular el de la cuenta.
)
ORDER BY id;
```

*Podemos ampliar la enumeración de suppliers_enum si es necesario.*

Finalmente el script guardará en un archivo lo scripts SQL para la actualización
masiva de estos campos.

```bash
WARNING: No supplier_id found for supplier 'Autocenter'.
UPDATE public.scheduled_expenses
SET 
    vehicle_id = 3029816, 
    supplier_id = 686303
WHERE "name"='2023/R1450' 
AND account_id = 1;
```
