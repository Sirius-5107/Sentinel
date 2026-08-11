"""Immutable value objects for the Sentinel domain.

These types are validated wrappers around primitives. They carry no identity
of their own and are reused across all domain models. All are defined as
Annotated types so they compose naturally with Pydantic v2 fields.
"""

from __future__ import annotations

import re
from typing import Annotated
import zoneinfo

from pydantic import AfterValidator, HttpUrl

# ── ConfidenceScore ────────────────────────────────────────────────────────────


def _validate_confidence(value: float) -> float:
    """Enforce 0.0 ≤ value ≤ 1.0, rounded to 4 decimal places."""
    if value < 0.0 or value > 1.0:
        raise ValueError(f"ConfidenceScore must be in [0.0, 1.0]; got {value!r}")
    return round(value, 4)


ConfidenceScore = Annotated[
    float,
    AfterValidator(_validate_confidence),
]
"""Confidence in a derived value (classification, scoring, sentiment).

Range: 0.0 (no confidence) to 1.0 (certainty).
Stored to 4 decimal places.

Notes:
    - 0.0 means the system has no basis for confidence, not that the value
      is incorrect.
    - 1.0 is reserved for deterministic / manually-verified outcomes.
      Model outputs must never reach 1.0.
"""

# ── ImportanceScore ────────────────────────────────────────────────────────────


def _validate_importance(value: float) -> float:
    """Enforce 0.0 ≤ value ≤ 10.0, rounded to 2 decimal places."""
    if value < 0.0 or value > 10.0:
        raise ValueError(f"ImportanceScore must be in [0.0, 10.0]; got {value!r}")
    return round(value, 2)


ImportanceScore = Annotated[
    float,
    AfterValidator(_validate_importance),
]
"""Quantifies the significance of an article or market event.

Range: 0.0 (noise) to 10.0 (critical systemic event).
Stored to 2 decimal places.

Scoring guidance (non-normative, not enforced by validation):
    0.0 - 2.9  Noise — routine movement, duplicated coverage
    3.0 - 5.9  Signal — noteworthy development
    6.0 - 7.9  High signal — material market event
    8.0 - 10.0 Critical — systemic or macro-level event
"""

# ── CountryCode ────────────────────────────────────────────────────────────────

_COUNTRY_CODE_RE = re.compile(r"^[A-Z]{2}$")


def _validate_country_code(value: str) -> str:
    """Enforce ISO 3166-1 alpha-2 pattern: exactly 2 uppercase letters."""
    if not _COUNTRY_CODE_RE.match(value):
        raise ValueError(
            f"CountryCode must be exactly 2 uppercase letters [A-Z]{{2}}; got {value!r}"
        )
    return value


CountryCode = Annotated[
    str,
    AfterValidator(_validate_country_code),
]
"""ISO 3166-1 alpha-2 country code (e.g. 'US', 'IN', 'GB').

Validation enforces the pattern [A-Z]{2}. No lookup against an authoritative
list is performed — that would introduce a runtime dependency not justified
at this phase.
"""

# ── LanguageCode ───────────────────────────────────────────────────────────────

_LANGUAGE_CODE_RE = re.compile(r"^[a-z]{2}$")


def _validate_language_code(value: str) -> str:
    """Enforce ISO 639-1 pattern: exactly 2 lowercase letters."""
    if not _LANGUAGE_CODE_RE.match(value):
        raise ValueError(
            f"LanguageCode must be exactly 2 lowercase letters [a-z]{{2}}; got {value!r}"
        )
    return value


LanguageCode = Annotated[
    str,
    AfterValidator(_validate_language_code),
]
"""ISO 639-1 two-letter language code (e.g. 'en', 'hi', 'zh').

Validation enforces the pattern [a-z]{2}.
"""

# ── Ticker ─────────────────────────────────────────────────────────────────────

_TICKER_RE = re.compile(r"^[A-Z]{1,10}:[A-Z0-9.]{1,10}$")


def _validate_ticker(value: str) -> str:
    """Enforce EXCHANGE:SYMBOL format, max 21 characters."""
    if len(value) > 21:
        raise ValueError(f"Ticker must be at most 21 characters; got {len(value)}")
    if not _TICKER_RE.match(value):
        raise ValueError(f"Ticker must match [A-Z]{{1,10}}:[A-Z0-9.]{{1,10}}; got {value!r}")
    return value


Ticker = Annotated[
    str,
    AfterValidator(_validate_ticker),
]
"""Exchange-listed security identifier in EXCHANGE:SYMBOL format.

Pattern: [A-Z]{1,10}:[A-Z0-9.]{1,10}, max 21 characters total.

Examples:
    'NYSE:BRK.B', 'NSE:RELIANCE', 'NASDAQ:AAPL', 'LSE:HSBA'

Notes:
    The colon separator is mandatory. The exchange prefix disambiguates
    identically-named tickers across different exchanges.
"""

# ── Url ────────────────────────────────────────────────────────────────────────

Url = HttpUrl
"""Validated HTTP or HTTPS URL.

Scheme must be http or https. Must include a host. Delegates to
Pydantic's HttpUrl for all validation.
"""

# ── IanaTimezone ───────────────────────────────────────────────────────────────


def _validate_iana_timezone(value: str) -> str:
    """Verify the string is a valid IANA timezone key via zoneinfo."""
    try:
        zoneinfo.ZoneInfo(value)
    except (zoneinfo.ZoneInfoNotFoundError, KeyError) as exc:
        raise ValueError(f"timezone must be a valid IANA timezone string; got {value!r}") from exc
    return value


IanaTimezone = Annotated[
    str,
    AfterValidator(_validate_iana_timezone),
]
"""IANA timezone identifier (e.g. 'America/New_York', 'Asia/Kolkata').

Validated by attempting zoneinfo.ZoneInfo(value). Raises ValueError if
the string is not a recognised IANA key.
"""

# ── CurrencyCode ───────────────────────────────────────────────────────────────

_CURRENCY_CODE_RE = re.compile(r"^[A-Z]{3}$")


def _validate_currency_code(value: str) -> str:
    """Enforce ISO 4217 pattern: exactly 3 uppercase letters."""
    if not _CURRENCY_CODE_RE.match(value):
        raise ValueError(
            f"CurrencyCode must be exactly 3 uppercase letters [A-Z]{{3}}; got {value!r}"
        )
    return value


CurrencyCode = Annotated[
    str,
    AfterValidator(_validate_currency_code),
]
"""ISO 4217 currency code (e.g. 'USD', 'INR', 'EUR').

Validation enforces the pattern [A-Z]{3}.
"""

# ── MicCode ────────────────────────────────────────────────────────────────────

_MIC_CODE_RE = re.compile(r"^[A-Z]{4}$")


def _validate_mic_code(value: str) -> str:
    """Enforce ISO 10383 MIC pattern: exactly 4 uppercase letters."""
    if not _MIC_CODE_RE.match(value):
        raise ValueError(f"MicCode must be exactly 4 uppercase letters [A-Z]{{4}}; got {value!r}")
    return value


MicCode = Annotated[
    str,
    AfterValidator(_validate_mic_code),
]
"""ISO 10383 Market Identifier Code (e.g. 'XNYS', 'XNAS', 'XNSE').

Validation enforces the pattern [A-Z]{4}.
"""

# ── IsinCode ───────────────────────────────────────────────────────────────────

_ISIN_CODE_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{10}$")


def _validate_isin_code(value: str) -> str:
    """Enforce ISO 6166 ISIN pattern: 2 letters + 10 alphanumeric."""
    if not _ISIN_CODE_RE.match(value):
        raise ValueError(f"ISIN must match [A-Z]{{2}}[A-Z0-9]{{10}} (12 chars); got {value!r}")
    return value


IsinCode = Annotated[
    str,
    AfterValidator(_validate_isin_code),
]
"""ISO 6166 International Securities Identification Number.

Pattern: 2-letter country code + 10 alphanumeric characters = 12 chars total.
Example: 'US0378331005' (Apple Inc.)
"""

# ── SlugField ──────────────────────────────────────────────────────────────────

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _validate_slug(value: str) -> str:
    """Enforce URL-safe slug: lowercase alphanumeric with internal hyphens."""
    if len(value) > 100:
        raise ValueError(f"Slug must be at most 100 characters; got {len(value)}")
    if not _SLUG_RE.match(value):
        raise ValueError(f"Slug must match ^[a-z0-9]+(-[a-z0-9]+)*$; got {value!r}")
    return value


SlugField = Annotated[
    str,
    AfterValidator(_validate_slug),
]
"""URL-safe slug for use as a human-readable identifier.

Pattern: ^[a-z0-9]+(-[a-z0-9]+)*$
Max length: 100 characters.
No leading or trailing hyphens. Internal hyphens only between segments.

Examples: 'ai-capex-cycle', 'india-infrastructure', 'private-credit'
"""
