import sqlite3
from config import *

class Database:

    @staticmethod
    def initialize_database():
        sql = """
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY, 
            title TEXT, 
            type TEXT, 
            price REAL, 
            listing_type TEXT, 
            description TEXT, 
            area REAL, 
            rooms INTEGER, 
            bathrooms INTEGER
        )
        """
        Database.execute_query(sql)

    @staticmethod
    def execute_query(sql, params=None):
        # The 'with' block ensures the connection closes automatically
        with sqlite3.connect(DATABASE_NAME) as conn:
            cur = conn.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            # Changes are auto-committed here if no error occurs
            return cur.fetchall()