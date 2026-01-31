from __future__ import annotations

import os
from pathlib import Path
from typing import Generator, Optional

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

# Ensure DATABASE_URL from .env is available for CLI tools (Alembic) and app code.
load_dotenv()

_engine = None
_engine_url: Optional[str] = None


def _build_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # PostgreSQL is the default backend. Require DATABASE_URL for normal runs.
    # A SQLite fallback (DATABASE_NAME) is kept for local dev/tests.
    name = os.getenv("DATABASE_NAME")
    if not name:
        raise RuntimeError(
            "DATABASE_URL is not set. Configure PostgreSQL via DATABASE_URL. "
            "(Optional fallback for dev/tests: set DATABASE_NAME to use SQLite.)"
        )

    if "://" in name:
        return name

    path = Path(name).expanduser()

    # SQLite fallback: For Windows absolute paths, SQLAlchemy expects forward slashes:
    # sqlite:///C:/Users/.../file.db
    if path.is_absolute():
        return f"sqlite:///{path.resolve().as_posix()}"

    return f"sqlite:///{name}"


def get_engine():
    global _engine, _engine_url

    url = _build_database_url()
    if _engine is not None and _engine_url == url:
        return _engine

    connect_args = {}
    if url.startswith("sqlite:"):
        connect_args = {"check_same_thread": False}

    _engine = create_engine(url, echo=False, connect_args=connect_args)
    _engine_url = url
    return _engine


def init_db() -> None:
    # Use Alembic migrations to manage schema.
    _run_migrations()


def drop_and_recreate_db() -> None:
    # Dev helper: destructive reset.
    engine = get_engine()
    SQLModel.metadata.drop_all(engine)
    _run_migrations()


def _run_migrations() -> None:
    """Apply Alembic migrations up to head using DATABASE_URL/DATABASE_NAME."""
    # session.py -> db -> src -> repo root
    repo_root = Path(__file__).resolve().parents[2]
    alembic_ini = repo_root / "alembic.ini"
    if not alembic_ini.exists():
        # Fallback to create_all if migrations are missing (should not happen).
        engine = get_engine()
        SQLModel.metadata.create_all(engine)
        return

    cfg = Config(str(alembic_ini))
    command.upgrade(cfg, "head")


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
