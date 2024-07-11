import psycopg2

"""
Class: Connection

This class is responsible for managing the connection to the database.
"""

class Connection:
    def __init__(self, db_name, host, user, password, port):
        self.db_name = db_name
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.conn = None
    
    def connect(self):
        self.conn = psycopg2.connect(
            database=self.db_name,
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port
        )
    
    def cursor(self):
        if self.conn is None:
            raise Exception("You must call connect() before getting the cursor.")
        return self.conn.cursor()

    def commit(self):
        if self.conn is None:
            raise Exception("You must call connect() before committing.")
        self.conn.commit()