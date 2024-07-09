"""
Class: Query

This class is responsible for managing the queries that will be executed in the database.
"""

class Query:

    # Constructor
    def __init__(self, query):
        self.query = query
        
    # Method to execute the query
    def execute(self):
        print(f"Executing query: {self.query}")
        return True

    # Method to get the info of the query
    def __str__(self):
        return f"{self.query}"
    
    # Method to get the account name
    def get_account_name(self, name):
        return f"SELECT a.id, a.legacy_account_id, a.name 
                 FROM accounts a 
                 WHERE a.name = '{name}'"
    
    # Method to get the account legacy code
    def get_account_legacy_code(self, legacy_code):
        return f"SELECT a.id, a.legacy_account_id, a.legacy_code
                 FROM accounts a 
                 WHERE a.legacy_code = '{legacy_code}'"
    
    # Method to get the account mgmt id
    def get_account_mgmt_id(self):
        return f"SELECT * FROM {self.query}"