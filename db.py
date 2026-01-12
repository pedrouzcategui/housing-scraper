import sqlite3

from config import DATABASE_NAME
from logging_utils import logger

class Database:

    @staticmethod
    def initialize_database():
        sql = """
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mercadolibre_listing_id TEXT UNIQUE, 
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
        try:
            with sqlite3.connect(DATABASE_NAME) as conn:
                cur = conn.cursor()
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                return cur.fetchall()
        except Exception:
            logger.exception("Database query failed", extra={"sql": sql, "params": params})
            raise

    @staticmethod
    def initialize_fresh():
        """Drops and recreates the table to ensure a clean, updated schema."""
        # 1. Get rid of the old table (if it exists)
        Database.execute_query("DROP TABLE IF EXISTS properties")
        
        # 2. Create the table fresh
        # This ensures your SQL structure matches your Python Model
        Database.initialize_database()
        logger.info("Database initialized: Table 'properties' recreated")