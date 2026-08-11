"""Market domain model.

A Market represents a financial exchange or trading venue at which
securities are listed. Markets are reference data — seeded at bootstrap
and rarely changed.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from sentinel_core.enums import MarketRegion
from sentinel_core.models._base import SentinelModel
from sentinel_core.types import CountryCode, CurrencyCode, IanaTimezone, MicCode

# Optional MIC: the field is Optional[MicCode] — nullable per the contract.
OptionalMicCode = Annotated[MicCode | None, Field(default=None)]


class Market(SentinelModel):
    """A financial market or exchange venue.

    Markets are reference data representing venues where securities are listed
    and traded (e.g. NYSE, NASDAQ, NSE, BSE, LSE). They provide context for
    Company primary listings and MarketEvent origin.

    Uniqueness constraints (enforced at the database layer):
        - abbreviation must be unique across all Market records.
        - mic, when non-None, must be unique across all Market records.

    Fields:
        id: UUID v4 primary key.
        name: Full name of the market (e.g. 'New York Stock Exchange').
        mic: ISO 10383 Market Identifier Code; 4 uppercase letters. Optional.
        abbreviation: Short common name (e.g. 'NYSE'). Max 20 chars. Unique.
        country: ISO 3166-1 alpha-2 country code of operation.
        region: Geographic market region.
        currency: ISO 4217 currency code (e.g. 'USD').
        timezone: IANA timezone string for the market's trading hours.
        is_active: False if this market is closed or delisted.
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        Market(
            name="New York Stock Exchange",
            mic="XNYS",
            abbreviation="NYSE",
            country="US",
            region=MarketRegion.US,
            currency="USD",
            timezone="America/New_York",
        )
    """

    name: str = Field(
        min_length=1,
        max_length=200,
        description="Full name of the market or exchange.",
    )
    mic: MicCode | None = Field(
        default=None,
        description=(
            "ISO 10383 Market Identifier Code (4 uppercase letters). "
            "Unique when non-None. Example: 'XNYS'."
        ),
    )
    abbreviation: str = Field(
        min_length=1,
        max_length=20,
        description=(
            "Common short name for the market. Unique across all Markets. "
            "Example: 'NYSE', 'NSE', 'LSE'."
        ),
    )
    country: CountryCode = Field(
        description="ISO 3166-1 alpha-2 country code of the market's jurisdiction.",
    )
    region: MarketRegion = Field(
        description="Geographic market region.",
    )
    currency: CurrencyCode = Field(
        description="ISO 4217 primary trading currency (e.g. 'USD', 'INR').",
    )
    timezone: IanaTimezone = Field(
        description=(
            "IANA timezone string for the market's trading hours "
            "(e.g. 'America/New_York', 'Asia/Kolkata')."
        ),
    )
    is_active: bool = Field(
        default=True,
        description="False if this market is closed or delisted.",
    )
