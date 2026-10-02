"""Add Phase 4 intelligence and report persistence tables.

Revision ID: 20260914_phase4_intelligence_schema
Revises: 20260820_initial_schema
Create Date: 2026-09-14 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260914_phase4_intelligence_schema"
down_revision = "20260820_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Phase 4 event, report, and provenance tables."""
    op.create_table(
        "market_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("asset_class", sa.String(length=32), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=False),
        sa.Column("sector", sa.String(length=32), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("sentiment", sa.String(length=32), nullable=False),
        sa.Column("sentiment_confidence", sa.Float(), nullable=False),
        sa.Column("importance_score", sa.Float(), nullable=False),
        sa.Column("importance_confidence", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("market_id", sa.String(length=36), nullable=True),
        sa.Column("embedding_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "daily_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("coverage_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("pipeline_run_id", sa.String(length=36), nullable=True),
        sa.Column("article_count", sa.Integer(), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notion_page_id", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "report_sections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("theme_id", sa.String(length=36), nullable=True),
        sa.Column("asset_class", sa.String(length=32), nullable=True),
        sa.Column("region", sa.String(length=32), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["daily_reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "article_market_event",
        sa.Column("article_id", sa.String(length=36), nullable=False),
        sa.Column("market_event_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"]),
        sa.ForeignKeyConstraint(["market_event_id"], ["market_events.id"]),
        sa.PrimaryKeyConstraint("article_id", "market_event_id"),
    )
    op.create_table(
        "market_event_report_section",
        sa.Column("market_event_id", sa.String(length=36), nullable=False),
        sa.Column("report_section_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["market_event_id"], ["market_events.id"]),
        sa.ForeignKeyConstraint(["report_section_id"], ["report_sections.id"]),
        sa.PrimaryKeyConstraint("market_event_id", "report_section_id"),
    )


def downgrade() -> None:
    """Drop Phase 4 provenance and report tables."""
    op.drop_table("market_event_report_section")
    op.drop_table("article_market_event")
    op.drop_table("report_sections")
    op.drop_table("daily_reports")
    op.drop_table("market_events")
