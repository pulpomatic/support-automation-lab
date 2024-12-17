import pandas as pd

class DriverLoader:
    REQUIRED_COLUMNS = [
        "Conductor*",
        "Email*",
        "Fecha inicio*",
        "Hora inicio*",
        "Fecha Fin",
        "Hora Fin",
        "Matricula*"
    ]
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None

    def load_file(self):
        """Carga el archivo y detecta si es CSV o XLSX."""
        try:
            if self.file_path.endswith('.csv'):
                self.data = pd.read_csv(self.file_path, quotechar='"')  # Añadir quotechar si hay comillas
            elif self.file_path.endswith('.xlsx'):
                self.data = pd.read_excel(self.file_path)
            else:
                raise ValueError("El archivo debe ser un CSV o XLSX.")
        except Exception as e:
            raise RuntimeError(f"Error al cargar el archivo: {e}")
        
        # Limpiar espacios extra en los nombres de las columnas
        self.data.columns = self.data.columns.str.strip()

    def validate_columns(self):
        """Valida que el archivo tenga las columnas necesarias."""
        if self.data is None:
            raise ValueError("No se ha cargado ningún archivo.")
        
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in self.data.columns]
        if missing_columns:
            raise ValueError(f"Faltan las siguientes columnas en el archivo: {', '.join(missing_columns)}")

    def process_data(self):
        """Procesa los datos y retorna una lista de conductores."""
        if self.data is None:
            raise ValueError("No se ha cargado ningún archivo.")
        
        drivers = []
        for _, row in self.data.iterrows():
            try:
                driver = {
                    "name": str(row.get("Conductor*", "")).strip(),
                    "email": str(row.get("Email*", "")).strip(),
                    "start_date": str(row.get("Fecha inicio*", "")).strip(),
                    "start_time": str(row.get("Hora inicio*", "")).strip(),
                    "end_date": str(row.get("Fecha Fin", "")).strip() if pd.notna(row.get("Fecha Fin")) else "",
                    "end_time": str(row.get("Hora Fin", "")).strip() if pd.notna(row.get("Hora Fin")) else "",
                    "vehicle": str(row.get("Matricula*", "")).strip()
                }
                drivers.append(driver)
            except Exception as e:
                print(f"Error al procesar fila: {row.to_dict()} - {e}")
                continue
        return drivers
