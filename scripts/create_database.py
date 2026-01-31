from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url


def main() -> None:
    load_dotenv()

    database_url_raw = os.getenv("DATABASE_URL")
    if not database_url_raw:
        raise RuntimeError("DATABASE_URL is not set")

    url = make_url(database_url_raw)
    target_db = url.database
    if not target_db:
        raise RuntimeError("DATABASE_URL must include a database name")

    # Connect to the maintenance DB to create the target DB.
    admin_url: URL = url.set(database="postgres")

    engine = create_engine(admin_url)

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": target_db},
        ).first()

        if exists:
            print(f"Database already exists: {target_db}")
            return

        # Quote DB name safely for Postgres.
        conn.execute(text(f'CREATE DATABASE "{target_db}"'))
        print(f"Database created: {target_db}")


if __name__ == "__main__":
    main()
