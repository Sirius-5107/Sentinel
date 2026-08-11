"""Theme domain model.

A Theme represents a persistent investment thesis — a cross-asset, multi-company
narrative that Sentinel tracks over time. Examples: 'AI Capex Cycle',
'India Infrastructure Build-out', 'Private Credit Expansion'.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from sentinel_core.enums import AssetClass, MarketRegion
from sentinel_core.models._base import SentinelModel
from sentinel_core.types import SlugField


class Theme(SentinelModel):
    """A persistent investment theme tracked by Sentinel.

    Themes are the highest-level categorisation in the knowledge base. They are
    manually seeded and LLM-maintained. Articles are tagged to themes by the
    intelligence layer and Themes accumulate evidence over time.

    Uniqueness constraints (enforced at the database layer):
        - name must be unique across all Themes.
        - slug must be unique across all Themes.

    Fields:
        id: UUID v4 primary key.
        name: Human-readable theme name (1-200 chars). Unique.
        slug: URL-safe identifier matching ^[a-z0-9]+(-[a-z0-9]+)*$. Unique.
        description: Overview of the theme; max 5000 chars. Optional.
        asset_class: Primary asset class, if theme is class-specific. Optional.
        region: Primary region, if theme is region-specific. Optional.
        is_active: False when the theme is archived.
        article_count: Denormalised count of tagged articles (>= 0).
        last_signal_at: UTC timestamp of the most recent article tagged here.
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        Theme(
            name="AI Capex Cycle",
            slug="ai-capex-cycle",
            description=(
                "Tracks the accelerating capital expenditure by hyperscalers "
                "and enterprises on AI infrastructure, GPUs, and data centres."
            ),
            asset_class=AssetClass.EQUITY,
            region=MarketRegion.GLOBAL,
        )
    """

    name: str = Field(
        min_length=1,
        max_length=200,
        description="Human-readable theme name. Unique across all Themes.",
    )
    slug: SlugField = Field(
        description=(
            "URL-safe identifier matching ^[a-z0-9]+(-[a-z0-9]+)*$. "
            "Max 100 characters. Unique across all Themes."
        ),
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Human-readable overview of the investment theme.",
    )
    asset_class: AssetClass | None = Field(
        default=None,
        description="Primary asset class, if this theme is class-specific.",
    )
    region: MarketRegion | None = Field(
        default=None,
        description="Primary market region, if this theme is region-specific.",
    )
    is_active: bool = Field(
        default=True,
        description="False if the theme is archived and no longer receives new signal.",
    )
    article_count: int = Field(
        default=0,
        ge=0,
        description=(
            "Denormalised count of articles tagged to this theme. "
            "Maintained by the application layer."
        ),
    )
    last_signal_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of the most recent article tagged to this theme.",
    )

    @field_validator("last_signal_at", mode="before")
    @classmethod
    def _require_utc_last_signal(cls, v: datetime | None) -> datetime | None:
        """Ensure last_signal_at is timezone-aware when provided."""
        if v is not None and v.tzinfo is None:
            raise ValueError("last_signal_at must be UTC-aware (tzinfo must not be None).")
        return v
