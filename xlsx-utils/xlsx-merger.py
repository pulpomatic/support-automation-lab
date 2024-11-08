from pathlib import Path

import pandas as pd


def get_user_input():
    """Get user preferences for file type and output name."""
    file_type = input("Enter the file type for the output (1 for CSV, 2 for XLSX): ")
    while file_type not in ["1", "2"]:
        print("Invalid option. Please enter 1 for CSV or 2 for XLSX.")
        file_type = input("Enter the file type for the output (1 for CSV, 2 for XLSX): ")

    output_name = input("Enter the name for the final output file (without extension): ")
    return file_type, output_name

def read_files(folder_path):
    """Read all .xls and .xlsx files in the specified folder and combine them."""
    all_data = pd.DataFrame()  # Initialize an empty DataFrame for combining data

    for file_path in folder_path.glob("*.xls*"):
        try:
            df = pd.read_excel(file_path, sheet_name=0, dtype=str)  # Read file as strings
            all_data = pd.concat([all_data, df], ignore_index=True)  # Append to main DataFrame
        except Exception as e:
            print(f"Error reading file {file_path.name}: {e}")
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

    # Get user input for file type and output name
    file_type, output_name = get_user_input()
    file_type = "csv" if file_type == "1" else "xlsx"

    # Read and combine files from input folder
    all_data = read_files(input_folder)

    # Save the combined data based on user choice
    save_combined_data(all_data, file_type, output_name, output_folder)

if __name__ == "__main__":
    main()
