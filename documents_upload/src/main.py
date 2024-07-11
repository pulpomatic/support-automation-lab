from document import *
from query import *
from conection import *
from terminal import *

directory_path = 'files/'

documents = get_documents_from_files(directory_path)

valid_documents = []
invalid_documents = []

for doc in documents:
    if doc.is_valid_plate():
        valid_documents.append(doc)
    else:
        invalid_documents.append(doc)

print(Terminal.get_logo())

nombre_cuenta = Terminal.account_name()

print("VALID DOCUMENTS:")
print_document_info(valid_documents)

print("INVALID DOCUMENTS:")
print_document_info(invalid_documents)

create_and_move_documents(valid_documents, directory_path)

create_and_move_documents(invalid_documents, directory_path)

plates = get_plate_by_folder_name(directory_path)

print(f"[{','.join(plates)}]")

# Create an instance of Query with the query for the account name
query_instance = Query(Query.get_account_name(nombre_cuenta))

# Execute the query
query_instance.execute()
