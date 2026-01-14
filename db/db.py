import os
import sqlite3
from utils.console import console

class Database:

    @staticmethod
    def _get_database_name() -> str:
        name = os.getenv("DATABASE_NAME")
        if not name:
            raise RuntimeError(
                "DATABASE_NAME is not set. Ensure it's defined before database operations."
            )
        return name

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
            with sqlite3.connect(Database._get_database_name()) as conn:
                cur = conn.cursor()
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                return cur.fetchall()
        except Exception as exc:
            console.print("[red]Database query failed[/]", {"sql": sql, "params": params})
            console.print("[red]Error:[/]", exc)
            raise

    @staticmethod
    def initialize_fresh():
        """Drops and recreates the table to ensure a clean, updated schema."""
        # 1. Get rid of the old table (if it exists)
        Database.execute_query("DROP TABLE IF EXISTS properties")
        
        # 2. Create the table fresh
        # This ensures your SQL structure matches your Python Model
        Database.initialize_database()
        console.print("[green]Database initialized:[/] Table 'properties' recreated")
