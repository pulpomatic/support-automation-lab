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
        return plate and plate.isalnum()

def clean_plate(plate):
    cleaned_plate = plate.replace("-", "").replace(" ", "").upper()
    if not cleaned_plate:
        return "NO PLATE FOR FILE"
    return cleaned_plate

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
    invalid_folder_path = os.path.join(base_path, 'invalid-documents')
    
    if not os.path.exists(invalid_folder_path):
        os.makedirs(invalid_folder_path)
    
    for doc in documents:
        src = os.path.join(base_path, doc.name)
        plate = clean_plate(doc.get_plate())
        
        print(f"Processing {doc.name}: Plate = {plate}, is_valid = {doc.is_valid_plate()}")
        
        if doc.is_valid_plate():
            folder_path = os.path.join(base_path, plate)
            
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            dst = os.path.join(folder_path, doc.name)
            
            if os.path.exists(src):
                shutil.copy(src, dst)
                print(f"Copied {doc.name} to {folder_path}")
            else:
                print(f"Source file {src} does not exist")
        else:
            dst = os.path.join(invalid_folder_path, doc.name)
            
            if os.path.exists(src):
                shutil.copy(src, dst)
                print(f"Copied {doc.name} to {invalid_folder_path}")
            else:
                print(f"Source file {src} does not exist")

def get_plate_by_folder_name(base_path):
    plates = []
    
    for folder_name in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder_name)
        
        if os.path.isdir(folder_path):
            if (folder_name == 'invalid-documents'):
                continue
            plate = folder_name.split('_')[0]
            plates.append(plate)
    
    return plates
