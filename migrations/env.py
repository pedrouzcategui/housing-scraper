from __future__ import annotations

import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# Make env vars from .env available to Alembic (DATABASE_URL, etc.)
load_dotenv()

# Ensure repo root + src are importable (so `db.*` imports work)
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Import models so SQLModel.metadata is fully populated
import db.models  # noqa: F401
from sqlmodel import SQLModel

from db.session import _build_database_url

config = context.config

target_metadata = SQLModel.metadata


def get_url() -> str:
    # Prefer DATABASE_URL (Postgres). Allows SQLite in tests.
    return _build_database_url()


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
