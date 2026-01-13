import os
import unicodedata
import asyncio
from scraper import main
from config import DEBUG_MODE
from db import Database

def to_snake_case(text):
    normalized = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
    return ''.join(c if c.isalnum() or c == '_' else '_' for c in normalized.lower().replace(' ', '_').replace('-', '_'))

def bootstrap():
    city = input("Enter the city name: ")
    db_name = f"{to_snake_case(city)}.db"
    os.environ['DATABASE_NAME'] = db_name
    
    if DEBUG_MODE:
        print("Running in DEBUG MODE")
        Database.initialize_fresh()
    asyncio.run(main(city))

if __name__ == "__main__":
    bootstrap()