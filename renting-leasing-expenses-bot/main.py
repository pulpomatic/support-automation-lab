import sys
from expenses_loader import ExpensesLoader
from dotenv import load_dotenv

def main(file_path: str):
    load_dotenv()
    
    loader = ExpensesLoader(file_path)
    
    loader.load_expenses()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 main.py <ruta_del_archivo_xlsx_o_csv>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    main(file_path)
