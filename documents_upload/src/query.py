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
    
    # Static method to get the account name
    @staticmethod
    def get_account_name(name):
        return f"""SELECT a.id, a.legacy_account_id, a.name FROM accounts a WHERE a.name = '{name}';"""

    # Static method to get the account legacy code
    @staticmethod
    def get_account_legacy_code(legacy_code):
        return f"""SELECT a.id, a.legacy_account_id, a.legacy_code FROM accounts a WHERE a.legacy_code = '{legacy_code}';"""
