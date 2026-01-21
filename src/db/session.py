from __future__ import annotations

import os
from pathlib import Path
from typing import Generator, Optional

from sqlmodel import Session, SQLModel, create_engine

_engine = None
_engine_url: Optional[str] = None


def _build_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    name = os.getenv("DATABASE_NAME")
    if not name:
        raise RuntimeError(
            "DATABASE_NAME is not set. Ensure it's defined before database operations."
        )

    if "://" in name:
        return name

    path = Path(name).expanduser()

    # For Windows absolute paths, SQLAlchemy expects forward slashes:
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
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def drop_and_recreate_db() -> None:
    engine = get_engine()
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
