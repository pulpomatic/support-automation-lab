from pathlib import Path

import pandas as pd


def get_user_input():
    """Get user preferences for file type, output name, and sheet name."""
    file_type = input("Enter the file type for the output (1 for CSV, 2 for XLSX): ")
    if file_type not in ["1", "2"]:
        raise ValueError("Invalid option. Please enter 1 for CSV or 2 for XLSX.")

    output_name = input("Enter the name for the final output file (without extension): ")
    sheet_name = input("Enter the name of the sheet to merge from all files: ")
    return file_type, output_name, sheet_name

def read_files(folder_path, sheet_name):
    """Read the specified sheet from all .xls and .xlsx files in the folder and combine them."""
    all_data = pd.DataFrame()  # Initialize an empty DataFrame for combining data

    for idx, file_path in enumerate(folder_path.glob("*.xls*")):
        try:
            # Read the specified sheet from the Excel file
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, keep_default_na=False)

            """
            Este codigo es util para transformar fechas a un formato especifico
            
            for col in df.columns:
                if "Fecha" in col:
                    df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=False)
                    # Si la columna se ha convertido exitosamente a fechas, formatear como DD/MM/AAAA
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].dt.strftime('%d/%m/%Y')
                    else:
                        # Si no es una fecha, restaurar la columna original (sin cambios)
                        df[col] = df[col].astype(str)
                else:
                    df[col] = df[col].astype(str)
            """
            # Skip headers if it's not the first file
            if idx > 0:
                df = df.iloc[1:]

            all_data = pd.concat([all_data, df], ignore_index=True)
        except Exception as e:
            print(f"Error reading sheet '{sheet_name}' in file {file_path.name}: {e}")
            raise e

    return all_data

def save_combined_data(all_data, file_type, output_name, output_folder):
    """Save the combined data into a CSV or XLSX file based on user preference."""
    output_path = output_folder / f"{output_name}.{file_type}"
    output_folder.mkdir(parents=True, exist_ok=True)  # Ensure output folder exists

    if file_type == "csv":
        all_data.to_csv(output_path, index=False, sep=",", quoting=1)  # Use double quotes for fields
        print(f"CSV file saved to {output_path}")
    else:
        all_data.to_excel(output_path, index=False)
        print(f"XLSX file saved to {output_path}")

def main():
    script_path = Path(__file__).parent  # Get current script path
    input_folder = script_path / "files"  # Define input folder path
    output_folder = script_path / "processed"  # Define output folder path

    # Get user input for file type, output name, and sheet name
    file_type, output_name, sheet_name = get_user_input()
    file_type = "csv" if file_type == "1" else "xlsx"

    # Read and combine files from input folder using the specified sheet
    all_data = read_files(input_folder, sheet_name)

    # Save the combined data based on user choice
    if not all_data.empty:
        save_combined_data(all_data, file_type, output_name, output_folder)
    else:
        print("No data was combined. Please check if the sheet name is correct.")

if __name__ == "__main__":
    main()
