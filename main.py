import asyncio
from scraper import main
from config import DEBUG_MODE
from db import Database

def bootstrap():
    if DEBUG_MODE:
        print("Running in DEBUG MODE")
        Database.initialize_fresh()
    asyncio.run(main())

if __name__ == "__main__":
    bootstrap()