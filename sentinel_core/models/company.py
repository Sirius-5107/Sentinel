"""Company domain model.

A Company is a publicly or privately held entity that appears in Sentinel's
coverage universe. Companies are knowledge base entities that persist across
articles and accumulate intelligence over time.
"""

from __future__ import annotations

from datetime import UTC, datetime
import uuid

from pydantic import Field, field_validator

from sentinel_core.enums import AssetClass, MarketRegion, Sector
from sentinel_core.models._base import SentinelModel
from sentinel_core.types import CountryCode, IsinCode, Ticker


class Company(SentinelModel):
    """A publicly or privately held company in Sentinel's coverage universe.

    Companies are extracted from articles by the entity extraction pipeline and
    resolved against existing records using ticker, ISIN, and fuzzy name matching.
    A Company record is the long-lived home for all intelligence about that business.

    Uniqueness constraints (enforced at the database layer):
        - ticker, when non-None, must be unique across all Company records.
        - isin, when non-None, must be unique across all Company records.

    Note on name uniqueness:
        name is NOT unique. Different companies may share very similar names
        (e.g. regional subsidiaries). Deduplication is a processing-layer concern.

    Fields:
        id: UUID v4 primary key.
        name: Display name (1-300 chars). Not unique.
        legal_name: Full legal entity name; max 500 chars. Optional.
        ticker: EXCHANGE:SYMBOL identifier. Unique when non-None.
        isin: ISO 6166 ISIN. Unique when non-None.
        country: ISO 3166-1 alpha-2 country of incorporation. Optional.
        sector: Primary GICS sector. Optional.
        asset_class: Relevant asset class. Optional.
        region: Primary market region. Optional.
        market_id: FK to Market (primary listing venue). Optional.
        description: LLM-synthesised overview; max 5000 chars. Optional.
        is_verified: True if manually reviewed.
        mention_count: Denormalised article mention count (>= 0).
        last_mentioned_at: UTC timestamp of most recent mention.
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        Company(
            name="Apple Inc.",
            legal_name="Apple Inc.",
            ticker="NASDAQ:AAPL",
            isin="US0378331005",
            country="US",
            sector=Sector.TECHNOLOGY,
            asset_class=AssetClass.EQUITY,
            region=MarketRegion.US,
        )
    """

    name: str = Field(
        min_length=1,
        max_length=300,
        description="Display name of the company. Not enforced as unique.",
    )
    legal_name: str | None = Field(
        default=None,
        max_length=500,
        description="Full legal entity name.",
    )
    ticker: Ticker | None = Field(
        default=None,
        description=(
            "Exchange-listed security identifier in EXCHANGE:SYMBOL format. "
            "Unique across all Company records when non-None."
        ),
    )
    isin: IsinCode | None = Field(
        default=None,
        description=(
            "ISO 6166 International Securities Identification Number. "
            "Unique across all Company records when non-None."
        ),
    )
    country: CountryCode | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country of incorporation.",
    )
    sector: Sector | None = Field(
        default=None,
        description="Primary GICS industry sector.",
    )
    asset_class: AssetClass | None = Field(
        default=None,
        description="Relevant financial asset class (e.g. EQUITY, PRIVATE_EQUITY).",
    )
    region: MarketRegion | None = Field(
        default=None,
        description="Primary market region.",
    )
    market_id: uuid.UUID | None = Field(
        default=None,
        description="FK to Market — the primary listing venue. Optional.",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="LLM-synthesised company overview.",
    )
    is_verified: bool = Field(
        default=False,
        description="True if this record has been manually reviewed and confirmed.",
    )
    mention_count: int = Field(
        default=0,
        ge=0,
        description=(
            "Denormalised count of articles mentioning this company. "
            "Maintained by the application layer."
        ),
    )
    last_mentioned_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of the most recent article mention.",
    )

    @field_validator("last_mentioned_at", mode="before")
    @classmethod
    def _require_utc_last_mentioned(cls, v: datetime | None) -> datetime | None:
        """Ensure last_mentioned_at is timezone-aware when provided."""
        if v is None:
            return None
        if v.tzinfo is None:
            raise ValueError("last_mentioned_at must be UTC-aware (tzinfo must not be None).")
        return v.astimezone(UTC)
