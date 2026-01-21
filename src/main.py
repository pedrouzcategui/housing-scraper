import os
import asyncio
from src.scraper import main
from src.config import DEBUG_MODE
from src.db.db import Database
from src.utils.strings import to_snake_case

def bootstrap():
    city = input("Enter the city name: ")
    db_name = f"{to_snake_case(city)}.db"
    os.environ['DATABASE_NAME'] = db_name
    
    if DEBUG_MODE:
        Database.initialize_fresh()
    else:
        # Ensure the database/table exists for non-debug runs
        Database.initialize_database()
    asyncio.run(main(city))

if __name__ == "__main__":
    bootstrap()