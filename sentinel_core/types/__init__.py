"""Sentinel domain value objects.

All types in this package are immutable, validated Annotated wrappers around
primitives. They carry no identity and are reused across all domain models.

Exported types
--------------
ConfidenceScore
    Float in [0.0, 1.0], 4 d.p. — confidence in a derived value.

ImportanceScore
    Float in [0.0, 10.0], 2 d.p. — signal importance level.

CountryCode
    ISO 3166-1 alpha-2 (e.g. 'US', 'IN').

LanguageCode
    ISO 639-1 two-letter code (e.g. 'en', 'hi').

Ticker
    EXCHANGE:SYMBOL security identifier (e.g. 'NYSE:BRK.B').

Url
    Validated HTTP/HTTPS URL (Pydantic HttpUrl).

IanaTimezone
    IANA timezone string (e.g. 'America/New_York').

CurrencyCode
    ISO 4217 three-letter currency code (e.g. 'USD').

MicCode
    ISO 10383 four-letter Market Identifier Code (e.g. 'XNYS').

IsinCode
    ISO 6166 twelve-character ISIN (e.g. 'US0378331005').

SlugField
    URL-safe lowercase slug, max 100 chars (e.g. 'ai-capex-cycle').
"""

from sentinel_core.types.value_objects import (
    ConfidenceScore,
    CountryCode,
    CurrencyCode,
    IanaTimezone,
    ImportanceScore,
    IsinCode,
    LanguageCode,
    MicCode,
    SlugField,
    Ticker,
    Url,
)

__all__ = [
    "ConfidenceScore",
    "CountryCode",
    "CurrencyCode",
    "IanaTimezone",
    "ImportanceScore",
    "IsinCode",
    "LanguageCode",
    "MicCode",
    "SlugField",
    "Ticker",
    "Url",
]
