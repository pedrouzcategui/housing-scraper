from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError

from db.session import drop_and_recreate_db, get_engine, init_db
from utils.console import console


class Database:
    @staticmethod
    def initialize_database() -> None:
        init_db()

    @staticmethod
    def initialize_fresh() -> None:
        drop_and_recreate_db()
        console.print("[green]Database initialized:[/] Tables recreated")

    @staticmethod
    def execute_query(sql: str, params=None):
        """Compatibility helper: executes raw SQL via SQLAlchemy.

        Prefer SQLModel sessions/models for new code.
        """
        try:
            engine = get_engine()
            with engine.begin() as conn:
                result = conn.exec_driver_sql(sql, params or ())
                try:
                    return result.fetchall()
                except Exception:
                    return []
        except SQLAlchemyError as exc:
            console.print("[red]Database query failed[/]", {"sql": sql, "params": params})
            console.print("[red]Error:[/]", exc)
            raise
