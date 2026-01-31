import importlib
from datetime import date

from sqlmodel import Session, select


def test_listing_prices_one_row_per_listing_per_day(tmp_path, monkeypatch):
    db_path = tmp_path / "test_prices.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    import db.session as db_session

    # Ensure the engine is rebuilt for this test database.
    db_session._engine = None
    db_session._engine_url = None

    # Reload models so SQLModel.metadata is populated for migrations.
    import db.models as db_models

    importlib.reload(db_models)

    from db.models import Listing, ListingPrice

    # Apply migrations to this SQLite database.
    db_session.init_db()

    with Session(db_session.get_engine()) as session:
        listing = Listing(mercadolibre_listing_id="123", title="x")
        session.add(listing)
        session.commit()
        session.refresh(listing)

        today = date.today()

        first = ListingPrice(
            listing_id=listing.id,
            mercadolibre_listing_id=listing.mercadolibre_listing_id,
            day=today,
            price=10.0,
        )
        session.add(first)
        session.commit()

        # Second insert for same (mlv_id, day) should be rejected by unique constraint.
        second = ListingPrice(
            listing_id=listing.id,
            mercadolibre_listing_id=listing.mercadolibre_listing_id,
            day=today,
            price=11.0,
        )
        session.add(second)
        try:
            session.commit()
        except Exception:
            session.rollback()

        rows = session.exec(
            select(ListingPrice).where(
                ListingPrice.mercadolibre_listing_id == listing.mercadolibre_listing_id,
                ListingPrice.day == today,
            )
        ).all()
        assert len(rows) == 1
