"""Initial schema + migrate properties->listings

Revision ID: 20260130_000001
Revises: 
Create Date: 2026-01-30

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260130_000001"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # USERS
    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("password", sa.String(), nullable=False),
            sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    # LISTINGS
    if not _table_exists("listings"):
        op.create_table(
            "listings",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("mercadolibre_listing_id", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=True),
            sa.Column("state", sa.String(), nullable=True),
            sa.Column("city", sa.String(), nullable=True),
            sa.Column("type", sa.String(), nullable=True),
            sa.Column("price", sa.Float(), nullable=True),
            sa.Column("listing_type", sa.String(), nullable=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("area", sa.Float(), nullable=True),
            sa.Column("rooms", sa.Integer(), nullable=True),
            sa.Column("bathrooms", sa.Integer(), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("images", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        )
        op.create_index(
            "ix_listings_mercadolibre_listing_id",
            "listings",
            ["mercadolibre_listing_id"],
            unique=True,
        )
        op.create_index("ix_listings_state", "listings", ["state"], unique=False)
        op.create_index("ix_listings_city", "listings", ["city"], unique=False)

    # DATA MIGRATION: properties -> listings (if upgrading from older SQLite schema)
    if _table_exists("properties"):
        if dialect == "postgresql":
            images_literal = "'[]'::json"
        else:
            images_literal = "'[]'"

        # Copy common columns. state/city default to NULL, images to []
        op.execute(
            sa.text(
                """
                INSERT INTO listings (
                    id,
                    mercadolibre_listing_id,
                    title,
                    state,
                    city,
                    type,
                    price,
                    listing_type,
                    description,
                    area,
                    rooms,
                    bathrooms,
                    latitude,
                    longitude,
                    images
                )
                SELECT
                    id,
                    mercadolibre_listing_id,
                    title,
                    NULL,
                    NULL,
                    type,
                    price,
                    listing_type,
                    description,
                    area,
                    rooms,
                    bathrooms,
                    latitude,
                    longitude,
                    """ + images_literal + """
                FROM properties
                """
            )
        )

        op.drop_table("properties")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Recreate properties table (legacy)
    if not _table_exists("properties"):
        op.create_table(
            "properties",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("mercadolibre_listing_id", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=True),
            sa.Column("type", sa.String(), nullable=True),
            sa.Column("price", sa.Float(), nullable=True),
            sa.Column("listing_type", sa.String(), nullable=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("area", sa.Float(), nullable=True),
            sa.Column("rooms", sa.Integer(), nullable=True),
            sa.Column("bathrooms", sa.Integer(), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
        )
        op.create_index(
            "ix_properties_mercadolibre_listing_id",
            "properties",
            ["mercadolibre_listing_id"],
            unique=True,
        )

    # Copy back from listings -> properties (drop state/city/images)
    if _table_exists("listings"):
        op.execute(
            sa.text(
                """
                INSERT INTO properties (
                    id,
                    mercadolibre_listing_id,
                    title,
                    type,
                    price,
                    listing_type,
                    description,
                    area,
                    rooms,
                    bathrooms,
                    latitude,
                    longitude
                )
                SELECT
                    id,
                    mercadolibre_listing_id,
                    title,
                    type,
                    price,
                    listing_type,
                    description,
                    area,
                    rooms,
                    bathrooms,
                    latitude,
                    longitude
                FROM listings
                """
            )
        )

        op.drop_index("ix_listings_city", table_name="listings")
        op.drop_index("ix_listings_state", table_name="listings")
        op.drop_index("ix_listings_mercadolibre_listing_id", table_name="listings")
        op.drop_table("listings")

    # Users table downgrade is intentionally left intact.
    # Dropping users can be surprising/destructive.
