import os
import shutil

class Document:
    """
    This class is responsible for managing the documents that will be uploaded to the server.
    """
    def __init__(self, name):
        self.name = name
        
    def get_plate(self):
        return self.name.split("_")[0]
    
    def get_type(self):
        return self.name.split(".")[-1].upper()

    def __str__(self):
        return f"{self.name}"

    def is_valid_plate(self):
        plate = clean_plate(self.get_plate())
        return plate.isalnum()

def clean_plate(plate):
    return plate.replace("-", "").replace(" ", "").upper()

def get_documents_from_files(path):
    documents = []
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)):
            doc = Document(filename)
            documents.append(doc)
    return documents

def print_document_info(documents):
    for doc in documents:
        print(f"Document: {doc}")
        print(f"Plate: {clean_plate(doc.get_plate())}")
        print(f"Type: {doc.get_type()}")
        print()

def create_and_move_documents(documents, base_path):
    for doc in documents:
        if doc.is_valid_plate():
            plate = clean_plate(doc.get_plate())
            folder_path = os.path.join(base_path, plate)
            
            # Delete all files in the folder
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            else:
                # Create the folder if it doesn't exist
                os.makedirs(folder_path)
            
            # Move the document to the folder
            src = os.path.join(base_path, doc.name)
            dst = os.path.join(folder_path, doc.name)
            shutil.copy(src, dst)
            print(f"Copy {doc.name} to {folder_path}")


# Define la ruta del directorio
directory_path = 'files/'

# Obtén los documentos del directorio
documents = get_documents_from_files(directory_path)

# Arreglos para almacenar documentos válidos e inválidos
valid_documents = []
invalid_documents = []

# Separa los documentos en válidos e inválidos
for doc in documents:
    if doc.is_valid_plate():
        valid_documents.append(doc)
    else:
        invalid_documents.append(doc)

# Imprime la información de todos los documentos
print("VALID DOCUMENTS:")
print_document_info(valid_documents)

print("INVALID DOCUMENTS:")
print_document_info(invalid_documents)

# Crea carpetas para los documentos válidos y mueve los documentos a las carpetas correspondientes
create_and_move_documents(valid_documents, directory_path)