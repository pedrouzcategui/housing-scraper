from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, String
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Session, SQLModel, select

from db.session import get_engine
from utils.console import console


class Property(SQLModel, table=True):
    __tablename__ = "properties"

    id: Optional[int] = Field(default=None, primary_key=True)

    mercadolibre_listing_id: str = Field(index=True, unique=True)
    title: Optional[str] = Field(default=None)

    # Keep Python attr as p_type but DB column name as "type"
    p_type: Optional[str] = Field(default=None, sa_column=Column("type", String))

    price: Optional[float] = Field(default=None)
    listing_type: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    area: Optional[float] = Field(default=None)
    rooms: Optional[int] = Field(default=None)
    bathrooms: Optional[int] = Field(default=None)

    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)

    def save(self) -> None:
        """Inserts the current property object into the database."""
        try:
            with Session(get_engine()) as session:
                session.add(self)
                session.commit()
                session.refresh(self)
            console.print(f"[green]Property saved:[/] '{self.title}'")
        except IntegrityError:
            console.print(
                f"[yellow]Property already exists:[/] {self.mercadolibre_listing_id}"
            )
        except Exception:
            console.print(f"[red]Failed to save property[/] {self.mercadolibre_listing_id}")
            raise

    @staticmethod
    def get_all() -> list["Property"]:
        """Fetches all properties and returns them as Property objects."""
        try:
            with Session(get_engine()) as session:
                return list(session.exec(select(Property)).all())
        except Exception:
            console.print("[red]Failed to fetch properties[/]")
            raise
