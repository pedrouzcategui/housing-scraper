from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class ListingPrice(SQLModel, table=True):
    __tablename__ = "listings_prices"
    __table_args__ = (
        UniqueConstraint(
            "mercadolibre_listing_id",
            "day",
            name="uq_listings_prices_mlvid_day",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    listing_id: int = Field(foreign_key="listings.id", index=True)
    mercadolibre_listing_id: str = Field(index=True)

    day: date = Field(default_factory=date.today, index=True)

    price: Optional[float] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
