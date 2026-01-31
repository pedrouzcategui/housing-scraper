"""add listings_prices

Revision ID: 20260130_000002
Revises: 20260130_000001
Create Date: 2026-01-30

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260130_000002"
down_revision = "20260130_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listings_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("mercadolibre_listing_id", sa.String(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "mercadolibre_listing_id",
            "day",
            name="uq_listings_prices_mlvid_day",
        ),
    )

    op.create_index(
        "ix_listings_prices_listing_id",
        "listings_prices",
        ["listing_id"],
        unique=False,
    )
    op.create_index(
        "ix_listings_prices_mercadolibre_listing_id",
        "listings_prices",
        ["mercadolibre_listing_id"],
        unique=False,
    )
    op.create_index(
        "ix_listings_prices_day",
        "listings_prices",
        ["day"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_listings_prices_day", table_name="listings_prices")
    op.drop_index(
        "ix_listings_prices_mercadolibre_listing_id",
        table_name="listings_prices",
    )
    op.drop_index("ix_listings_prices_listing_id", table_name="listings_prices")
    op.drop_table("listings_prices")
