import csv
import re

from suppliers_enum import SUPPLIERS
from vehicles_enum import VEHICLES

def clean_vehicle_name(name):
    """Elimina caracteres especiales de las matrículas dejando solo alfanuméricos."""
    return re.sub(r'\W+', '', name)

def capitalize_supplier_name(supplier):
    """Formatea el nombre del proveedor."""
    return supplier.capitalize()

def load_rl_enum(file_path):
    rl_enum = {}
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            expense_name = row['expense_name']
            vehicle_name = clean_vehicle_name(row['name'])
            supplier = capitalize_supplier_name(row['supplier'])
            rl_enum[expense_name] = {"vehicle_name": vehicle_name, "supplier": supplier}
    return rl_enum

def generate_updates(account_id, rl_enum_file, output_file):
    rl_enum = load_rl_enum(rl_enum_file)
    updates = []
    with open(output_file, mode='w') as file:
        for expense_name, details in rl_enum.items():
            vehicle_name = details["vehicle_name"]
            supplier = details["supplier"]
            
            supplier_id = SUPPLIERS.get(supplier)
            vehicle_id = VEHICLES.get(vehicle_name)

            if supplier_id and vehicle_id:
                query = f"""UPDATE public.scheduled_expenses
SET 
    vehicle_id = {vehicle_id}, 
    supplier_id = {supplier_id}
WHERE "name"='{expense_name}' 
AND account_id = {account_id};
"""
                updates.append(query)
                file.write(query + "\n")
            else:
                # Registrar problemas si faltan IDs.
                if not supplier_id:
                    print(f"WARNING: No supplier_id found for supplier '{supplier}'.")
                if not vehicle_id:
                    print(f"WARNING: No vehicle_id found for vehicle '{vehicle_name}'.")
    return updates

if __name__ == "__main__":
    account_id = 1 # El de la cuenta.
    rl_enum_file = 'expenses_file_example.csv'  # Ruta del archivo CSV.
    output_file = 'renting_leasing_query_update.txt'  # Ruta del archivo de salida.
    queries = generate_updates(account_id, rl_enum_file, output_file)
    for query in queries:
        print(query)
