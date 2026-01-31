import asyncio
from scraper.scraper import main
from scraper.config import DEBUG_MODE
from db.db import Database

def bootstrap():
    city = input("Enter the city name: ")
    # PostgreSQL: configure DATABASE_URL in your environment (e.g. .env)
    # Keeping DATABASE_NAME unset avoids accidental SQLite usage.
    
    if DEBUG_MODE:
        Database.initialize_fresh()
    else:
        # Ensure the database/table exists for non-debug runs
        Database.initialize_database()
    asyncio.run(main(city))

if __name__ == "__main__":
    bootstrap()