"""Person domain model.

A Person is a named individual — executive, policymaker, analyst, or other
market-relevant person — who appears in Sentinel's coverage.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field, field_validator

from sentinel_core.models._base import SentinelModel
from sentinel_core.types import CountryCode


class Person(SentinelModel):
    """A named individual relevant to financial markets.

    People are extracted entities resolved against existing records by name
    normalisation and context. A Person record accumulates mentions and
    associated events over time.

    Uniqueness constraints:
        None at the model layer. Two people may share a name. Resolution
        is a processing-layer concern (Phase 3).

    Note on external identifiers:
        No external identifier (LinkedIn URL, Wikidata QID, etc.) is included
        at this phase. Such identifiers must be added via an ADR if a data
        provider makes them available in a later phase.

    Fields:
        id: UUID v4 primary key.
        full_name: Full name (1-200 chars).
        title: Current role or title; max 200 chars. Optional.
        organization_name: Primary employer (denormalised); max 300 chars.
        country: ISO 3166-1 alpha-2 country of primary operation. Optional.
        description: Brief biography or role summary; max 2000 chars. Optional.
        is_verified: True if manually reviewed.
        mention_count: Denormalised article mention count (>= 0).
        last_mentioned_at: UTC timestamp of the most recent mention.
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        Person(
            full_name="Jerome Powell",
            title="Chair",
            organization_name="Federal Reserve System",
            country="US",
        )
    """

    full_name: str = Field(
        min_length=1,
        max_length=200,
        description="Full name of the individual.",
    )
    title: str | None = Field(
        default=None,
        max_length=200,
        description="Current role or title (e.g. 'Chair', 'CEO', 'Managing Director').",
    )
    organization_name: str | None = Field(
        default=None,
        max_length=300,
        description=(
            "Primary employer or institution name. Denormalised for display; "
            "the authoritative link is via the organizations many-to-many relationship."
        ),
    )
    country: CountryCode | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country of primary residence or operation.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Brief biography or role summary.",
    )
    is_verified: bool = Field(
        default=False,
        description="True if this record has been manually reviewed and confirmed.",
    )
    mention_count: int = Field(
        default=0,
        ge=0,
        description=(
            "Denormalised count of articles mentioning this person. "
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
