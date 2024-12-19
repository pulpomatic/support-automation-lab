import pandas as pd

class DateTransform:
    def convert_to_iso_format(self, date_string):
        """
        Convierte una fecha de tipo string o Timestamp a un formato ISO 8601 (YYYY-MM-DDTHH:MM:SSZ).
        """
        try:
            if isinstance(date_string, pd.Timestamp):
                date_string = date_string.strftime('%Y-%m-%dT%H:%M:%SZ')
            elif isinstance(date_string, str):
                date_object = pd.to_datetime(date_string, errors='coerce')
                if pd.isna(date_object):
                    raise ValueError(f"Formato de fecha no reconocido: {date_string}")
                date_string = date_object.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                raise ValueError(f"Tipo de dato no esperado para la fecha: {type(date_string)}")
            return date_string
        except Exception as e:
            raise ValueError(f"Error al convertir la fecha: {e}")
