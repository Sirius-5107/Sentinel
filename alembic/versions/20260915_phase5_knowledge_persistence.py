"""Add typed knowledge entities and MarketEvent relationships.

Revision ID: 20260915_phase5_knowledge_persistence
Revises: 20260820_initial_schema
Create Date: 2026-09-15 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260915_phase5_knowledge_persistence"
down_revision = "20260820_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create typed knowledge tables and explicit event relationships."""
    op.create_table(
        "companies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("legal_name", sa.String(length=500), nullable=True),
        sa.Column("ticker", sa.String(length=32), nullable=True),
        sa.Column("isin", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("sector", sa.String(length=32), nullable=True),
        sa.Column("asset_class", sa.String(length=32), nullable=True),
        sa.Column("region", sa.String(length=32), nullable=True),
        sa.Column("market_id", sa.String(length=36), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mention_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_mentioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_company_name"),
        sa.UniqueConstraint("ticker", name="uq_company_ticker"),
        sa.UniqueConstraint("isin", name="uq_company_isin"),
    )

    op.create_table(
        "people",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("organization_name", sa.String(length=300), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mention_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_mentioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("full_name", name="uq_person_full_name"),
    )

    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("abbreviation", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("region", sa.String(length=32), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mention_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_mentioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_organization_name"),
        sa.UniqueConstraint("abbreviation", name="uq_organization_abbreviation"),
    )

    op.create_table(
        "themes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("asset_class", sa.String(length=32), nullable=True),
        sa.Column("region", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("article_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_signal_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_theme_name"),
        sa.UniqueConstraint("slug", name="uq_theme_slug"),
    )

    op.create_table(
        "company_theme",
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("theme_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_company_theme_company_id",
        ),
        sa.ForeignKeyConstraint(
            ["theme_id"],
            ["themes.id"],
            name="fk_company_theme_theme_id",
        ),
        sa.PrimaryKeyConstraint("company_id", "theme_id"),
    )

    op.create_table(
        "company_person",
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("person_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_company_person_company_id",
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["people.id"],
            name="fk_company_person_person_id",
        ),
        sa.PrimaryKeyConstraint("company_id", "person_id"),
    )

    op.create_table(
        "person_organization",
        sa.Column("person_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["people.id"],
            name="fk_person_organization_person_id",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_person_organization_organization_id",
        ),
        sa.PrimaryKeyConstraint("person_id", "organization_id"),
    )

    op.create_table(
        "market_event_company",
        sa.Column("market_event_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["market_event_id"],
            ["market_events.id"],
            name="fk_market_event_company_market_event_id",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_market_event_company_company_id",
        ),
        sa.PrimaryKeyConstraint("market_event_id", "company_id"),
    )

    op.create_table(
        "market_event_person",
        sa.Column("market_event_id", sa.String(length=36), nullable=False),
        sa.Column("person_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["market_event_id"],
            ["market_events.id"],
            name="fk_market_event_person_market_event_id",
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["people.id"],
            name="fk_market_event_person_person_id",
        ),
        sa.PrimaryKeyConstraint("market_event_id", "person_id"),
    )

    op.create_table(
        "market_event_organization",
        sa.Column("market_event_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["market_event_id"],
            ["market_events.id"],
            name="fk_market_event_organization_market_event_id",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_market_event_organization_organization_id",
        ),
        sa.PrimaryKeyConstraint("market_event_id", "organization_id"),
    )

    op.create_table(
        "market_event_theme",
        sa.Column("market_event_id", sa.String(length=36), nullable=False),
        sa.Column("theme_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["market_event_id"],
            ["market_events.id"],
            name="fk_market_event_theme_market_event_id",
        ),
        sa.ForeignKeyConstraint(
            ["theme_id"],
            ["themes.id"],
            name="fk_market_event_theme_theme_id",
        ),
        sa.PrimaryKeyConstraint("market_event_id", "theme_id"),
    )


def downgrade() -> None:
    """Drop the Phase 5 typed knowledge schema."""
    op.drop_table("market_event_theme")
    op.drop_table("market_event_organization")
    op.drop_table("market_event_person")
    op.drop_table("market_event_company")
    op.drop_table("person_organization")
    op.drop_table("company_person")
    op.drop_table("company_theme")
    op.drop_table("themes")
    op.drop_table("organizations")
    op.drop_table("people")
    op.drop_table("companies")
