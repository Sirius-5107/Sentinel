"""Financial domain enumerations."""

from enum import StrEnum


class AssetClass(StrEnum):
    """The financial asset class most relevant to a piece of content.

    Used to classify articles, market events, companies, and report sections
    by the type of financial instrument or market they concern.
    """

    EQUITY = "equity"
    """Publicly listed common or preferred stock."""

    FIXED_INCOME = "fixed_income"
    """Government and corporate bonds, treasuries, and credit instruments."""

    PRIVATE_CREDIT = "private_credit"
    """Privately negotiated loans and direct lending."""

    PRIVATE_EQUITY = "private_equity"
    """Buyouts, growth equity, and venture capital."""

    REAL_ESTATE = "real_estate"
    """Property, REITs, and real-asset investments."""

    COMMODITIES = "commodities"
    """Energy, metals, agriculture, and other physical goods."""

    CURRENCIES = "currencies"
    """Foreign exchange and currency markets."""

    CRYPTO = "crypto"
    """Digital assets and blockchain-related instruments."""

    MACRO = "macro"
    """Cross-asset macro developments, monetary policy, and central banking."""

    OTHER = "other"
    """Content that does not fit a primary asset class."""


class MarketRegion(StrEnum):
    """Geographic market region for routing and filtering content.

    Derived from Milestone 3 Daily Brief sections. GLOBAL covers
    cross-regional content that does not belong to a single region.
    """

    GLOBAL = "global"
    """Cross-regional; applies to multiple geographies simultaneously."""

    US = "us"
    """United States markets."""

    INDIA = "india"
    """Indian markets (NSE, BSE)."""

    EUROPE = "europe"
    """European markets including UK."""

    ASIA_PACIFIC = "asia_pacific"
    """Asia-Pacific markets excluding India."""

    MIDDLE_EAST = "middle_east"
    """Middle East and North Africa markets."""

    LATIN_AMERICA = "latin_america"
    """Latin American markets."""

    AFRICA = "africa"
    """Sub-Saharan African markets."""


class Sector(StrEnum):
    """GICS-aligned industry sector classification.

    Based on the Global Industry Classification Standard (GICS).
    UNKNOWN is used when the sector cannot be determined.
    """

    TECHNOLOGY = "technology"
    FINANCIALS = "financials"
    HEALTHCARE = "healthcare"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    INDUSTRIALS = "industrials"
    ENERGY = "energy"
    MATERIALS = "materials"
    REAL_ESTATE = "real_estate"
    UTILITIES = "utilities"
    COMMUNICATION_SERVICES = "communication_services"
    UNKNOWN = "unknown"
    """Sector could not be determined from available information."""


class Sentiment(StrEnum):
    """Market or narrative sentiment derived from an article or event.

    Represents the directional signal the content carries for the
    subject it covers. MIXED is used when the content contains
    conflicting signals that do not resolve to a single direction.
    """

    BULLISH = "bullish"
    """Positive outlook; implies favourable conditions for the subject."""

    BEARISH = "bearish"
    """Negative outlook; implies unfavourable conditions for the subject."""

    NEUTRAL = "neutral"
    """No directional signal; factual or inconclusive content."""

    MIXED = "mixed"
    """Conflicting signals within the same piece of content."""


class EventSeverity(StrEnum):
    """Impact level of a MarketEvent.

    Indicates how significant the event is expected to be for markets.
    Used for prioritisation in report assembly and alerting.
    """

    LOW = "low"
    """Routine — normal market activity, unlikely to move prices."""

    MEDIUM = "medium"
    """Notable — warrants monitoring; limited market impact expected."""

    HIGH = "high"
    """Material — likely to move prices in affected markets."""

    CRITICAL = "critical"
    """Systemic — potential for broad, cross-asset market impact."""


class EntityType(StrEnum):
    """Classifies which kind of named entity an extracted reference represents.

    Used internally by the processing pipeline to determine which domain
    model (Company, Person, Organization) a reference should resolve to.
    """

    COMPANY = "company"
    PERSON = "person"
    ORGANIZATION = "organization"
    MARKET = "market"
    THEME = "theme"
    UNKNOWN = "unknown"
    """Entity type could not be determined."""
