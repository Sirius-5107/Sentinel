"""Organization domain model.

An Organization is a non-company institution — central bank, government body,
regulatory agency, international organisation, or trade association — that is
relevant to financial markets (e.g. Federal Reserve, SEC, ECB, IMF, OPEC, RBI).
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field, field_validator

from sentinel_core.enums import MarketRegion
from sentinel_core.models._base import SentinelModel
from sentinel_core.types import CountryCode


class Organization(SentinelModel):
    """A non-company institution relevant to financial markets.

    Organizations are distinct from Companies in that they are not publicly
    or privately held commercial entities. Examples include central banks,
    government bodies, regulatory agencies, and international organisations.

    Uniqueness constraints (enforced at the database layer):
        - abbreviation, when non-None, must be unique across all Organization
          records. This enables reliable lookup by short-form name.

    Fields:
        id: UUID v4 primary key.
        name: Full institution name (1-300 chars).
        abbreviation: Common short name; max 20 chars (e.g. 'Fed', 'SEC').
        country: ISO 3166-1 alpha-2 code. None for supranational bodies.
        region: Primary region of influence.
        description: Role summary; max 2000 chars.
        is_verified: True if the record has been manually reviewed.
        mention_count: Denormalised count of article mentions (>= 0).
        last_mentioned_at: UTC timestamp of the most recent mention.
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        Organization(
            name="Federal Reserve System",
            abbreviation="Fed",
            country="US",
            region=MarketRegion.US,
            description="The central banking system of the United States.",
        )
    """

    name: str = Field(
        min_length=1,
        max_length=300,
        description="Full institution name.",
    )
    abbreviation: str | None = Field(
        default=None,
        max_length=20,
        description=(
            "Common abbreviation for the organisation. "
            "Unique across all Organizations when non-None. "
            "Examples: 'Fed', 'SEC', 'ECB', 'IMF'."
        ),
    )
    country: CountryCode | None = Field(
        default=None,
        description=(
            "ISO 3166-1 alpha-2 country code of domicile. "
            "None for supranational organisations (e.g. IMF, BIS)."
        ),
    )
    region: MarketRegion | None = Field(
        default=None,
        description="Primary region of influence.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Brief role summary.",
    )
    is_verified: bool = Field(
        default=False,
        description="True if this record has been manually reviewed and confirmed.",
    )
    mention_count: int = Field(
        default=0,
        ge=0,
        description=(
            "Denormalised count of articles that mention this organisation. "
            "Maintained by the application layer, not a database constraint."
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
