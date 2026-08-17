"""Sentinel system-wide constants.

All magic numbers and fixed limits used across sentinel_core are defined
here. Application-layer packages import from this module rather than
hardcoding values.

Constants are grouped by concern. All values are Final to prevent
accidental reassignment.
"""

from typing import Final

# ── Article limits ────────────────────────────────────────────────────────────

ARTICLE_TITLE_MAX_LENGTH: Final[int] = 500
"""Maximum character length of an Article title."""

ARTICLE_CONTENT_MAX_LENGTH: Final[int] = 100_000
"""Maximum character length of an Article body."""

ARTICLE_SUMMARY_MAX_LENGTH: Final[int] = 2_000
"""Maximum character length of an Article or MarketEvent summary."""

ARTICLE_ERROR_MAX_LENGTH: Final[int] = 2_000
"""Maximum character length of an Article error_message."""

ARTICLE_CONTENT_HASH_LENGTH: Final[int] = 64
"""Expected length of a SHA-256 hex digest (content_hash)."""

ARTICLE_PUBLISHED_AT_MAX_FUTURE_DAYS: Final[int] = 7
"""Maximum number of days in the future that published_at may be (clock-skew tolerance)."""

# ── MarketEvent limits ────────────────────────────────────────────────────────

MARKET_EVENT_TITLE_MAX_LENGTH: Final[int] = 300
"""Maximum character length of a MarketEvent title."""

MARKET_EVENT_SUMMARY_MIN_LENGTH: Final[int] = 100
"""Minimum character length of a MarketEvent summary (enforces 'explain why it matters')."""

MARKET_EVENT_SUMMARY_MAX_LENGTH: Final[int] = 2_000
"""Maximum character length of a MarketEvent summary."""

MARKET_EVENT_OCCURRED_AT_MAX_FUTURE_DAYS: Final[int] = 30
"""Maximum number of days in the future that occurred_at may be."""

# ── Source limits ─────────────────────────────────────────────────────────────

SOURCE_WEIGHT_MIN: Final[float] = 0.1
"""Minimum allowed source weight. Use status=PAUSED to suppress a source."""

SOURCE_WEIGHT_MAX: Final[float] = 2.0
"""Maximum allowed source weight."""

SOURCE_FETCH_INTERVAL_MIN_MINUTES: Final[int] = 1
"""Minimum polling interval in minutes."""

SOURCE_FETCH_INTERVAL_MAX_MINUTES: Final[int] = 1440
"""Maximum polling interval in minutes (once per day)."""

# ── DailyReport limits ────────────────────────────────────────────────────────

DAILY_REPORT_COVERAGE_DATE_MAX_FUTURE_DAYS: Final[int] = 7
"""Maximum days in the future for a DailyReport coverage_date."""

DAILY_REPORT_TITLE_MAX_LENGTH: Final[int] = 300
"""Maximum character length of a DailyReport title."""

# ── ReportSection limits ──────────────────────────────────────────────────────

REPORT_SECTION_TITLE_MAX_LENGTH: Final[int] = 200
"""Maximum character length of a ReportSection title."""

REPORT_SECTION_CONTENT_MAX_LENGTH: Final[int] = 20_000
"""Maximum character length of a ReportSection body."""

# ── PipelineRun / Task ────────────────────────────────────────────────────────

PIPELINE_ALLOWED_TRIGGERS: Final[frozenset[str]] = frozenset({"scheduler", "manual", "api"})
"""Valid values for PipelineRun.trigger."""

TASK_NAME_MAX_LENGTH: Final[int] = 200
"""Maximum character length of a Task name."""

TASK_ERROR_MAX_LENGTH: Final[int] = 5_000
"""Maximum character length of a Task or PipelineRun error message."""
