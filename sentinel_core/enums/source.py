"""Source-related enumerations."""

from enum import StrEnum


class SourceType(StrEnum):
    """Classifies the mechanism by which a Source delivers content.

    Determines which collector implementation is used to fetch articles
    from a given source.
    """

    RSS = "rss"
    """Syndicated RSS or Atom feed."""

    SCRAPE = "scrape"
    """Static HTML page scraped via HTTP."""

    DYNAMIC = "dynamic"
    """JavaScript-rendered page requiring a headless browser (Playwright)."""

    API = "api"
    """Structured data delivered via a REST or GraphQL API."""

    MANUAL = "manual"
    """Human-submitted content; not machine-collected."""


class SourceStatus(StrEnum):
    """Lifecycle state of a Source.

    Controls whether the collector will attempt to fetch from this source
    on its next scheduled run.
    """

    ACTIVE = "active"
    """Currently being polled on its configured interval."""

    PAUSED = "paused"
    """Temporarily suspended; will not be fetched until re-activated."""

    DISABLED = "disabled"
    """Permanently removed from rotation; retained for audit history."""

    ERROR = "error"
    """Failing repeatedly; under investigation. Fetch is suspended."""
