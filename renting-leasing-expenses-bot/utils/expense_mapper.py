import pandas as pd
from datetime import datetime
from deep_translator import GoogleTranslator

class ExpenseMapper:
    def __init__(self):
        self.expense_type_map = {
            "bonificaciones": 74079,
            "bombonas": 74080,
            "compra": 74081,
            "donativos": 74082,
            "lavado/limpieza": 74083,
            "leasing": 74084,
            "lubricantes": 74085,
            "multas": 74086,
            "ocupación recarga eléctrica": 74087,
            "otros": 74088,
            "parking": 74089,
            "peajes": 74090,
            "penalizaciones": 74091,
            "recargas": 74092,
            "renting": 74093,
            "taller": 74095,
            "tienda": 74096,
            "trámites del vehículo": 74097,
            "itv": 74098,
            "recarga eléctrica": 80613
        }
        self.frequency_map = {
            "año": "year",
            "mes": "month",
            "día": "day",
            "semana": "week"
        }
        self.translator = GoogleTranslator(source="en", target="es")

    def translate_to_spanish(self, value):
        try:
            return self.translator.translate(value)
        except Exception as e:
            print(f"Error al traducir: {e}")
            return value

    def map_expense_type(self, value):
        if isinstance(value, str):
            value = value.strip().lower()
        else:
            value = str(value).strip().lower()
        mapped_id = self.expense_type_map.get(value)
        if mapped_id:
            return mapped_id

        value_in_spanish = self.translate_to_spanish(value)
        return self.expense_type_map.get(value_in_spanish, None)


    def map_frequency(self, value):
        if pd.isna(value):
            return None
        value = value.strip().lower()
        return self.frequency_map.get(value, value)
