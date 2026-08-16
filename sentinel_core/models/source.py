"""Source domain model.

A Source represents a single external content provider from which Sentinel
ingests articles. It is the entry point into the entire processing pipeline.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field, field_validator

from sentinel_core.enums import AssetClass, MarketRegion, SourceStatus, SourceType
from sentinel_core.models._base import SentinelModel
from sentinel_core.types import LanguageCode, Url

_FETCH_INTERVAL_MIN = 1
_FETCH_INTERVAL_MAX = 1440  # once per day
_WEIGHT_MIN = 0.1
_WEIGHT_MAX = 2.0


class Source(SentinelModel):
    """An external content provider that supplies articles to Sentinel.

    Sources are configured in configs/sources.yaml and registered in the
    database. The database record is the runtime source of truth; the YAML
    file is only used during bootstrap.

    Uniqueness constraints (enforced at the database layer):
        - name must be unique across all Source records.

    Validation rules:
        - weight must be in [0.1, 2.0].
        - fetch_interval_minutes must be in [1, 1440].
        - consecutive_errors must be >= 0.
        - last_fetched_at must not be in the future.
        - All datetime fields must be UTC-aware; non-UTC aware datetimes are
          normalised to UTC.

    Fields:
        id: UUID v4 primary key.
        name: Display name. Unique. 1-200 chars.
        url: Valid http(s) URL for the feed or page.
        source_type: Collection mechanism (RSS, SCRAPE, DYNAMIC, API, MANUAL).
        status: Lifecycle state; defaults to ACTIVE.
        region: Geographic market region for this source's content.
        asset_class: Primary asset class this source covers.
        language: ISO 639-1 language code; defaults to 'en'.
        weight: Relative importance in deduplication / scoring [0.1, 2.0].
        fetch_interval_minutes: How often to poll; 1-1440 minutes.
        last_fetched_at: UTC timestamp of the most recent successful fetch.
        last_error: Most recent fetch error message; max 2000 chars.
        consecutive_errors: Count of consecutive failures since last success.
        created_at: UTC construction timestamp.
        updated_at: UTC version timestamp of this snapshot.

    Example::

        Source(
            name="Reuters Business",
            url="https://feeds.reuters.com/reuters/businessNews",
            source_type=SourceType.RSS,
            region=MarketRegion.GLOBAL,
            asset_class=AssetClass.MACRO,
        )
    """

    name: str = Field(
        min_length=1,
        max_length=200,
        description="Display name of the source. Unique across all Sources.",
    )
    url: Url = Field(
        description="Valid http(s) URL for the feed or page.",
    )
    source_type: SourceType = Field(
        description="Collection mechanism that determines which collector to use.",
    )
    status: SourceStatus = Field(
        default=SourceStatus.ACTIVE,
        description="Lifecycle state controlling whether the collector will poll this source.",
    )
    region: MarketRegion = Field(
        description="Geographic market region that this source primarily covers.",
    )
    asset_class: AssetClass = Field(
        description="Primary financial asset class covered by this source.",
    )
    language: LanguageCode = Field(
        default="en",  # type: ignore[assignment]
        description="ISO 639-1 language code of the source content. Defaults to 'en'.",
    )
    weight: float = Field(
        default=1.0,
        description=(
            "Relative importance of this source in deduplication and scoring. "
            "Range: [0.1, 2.0]. Use status=PAUSED instead of weight=0.0 to suppress."
        ),
    )
    fetch_interval_minutes: int = Field(
        default=60,
        description=(
            "How frequently the collector polls this source, in minutes. Range: [1, 1440]."
        ),
    )
    last_fetched_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of the most recent successful fetch.",
    )
    last_error: str | None = Field(
        default=None,
        max_length=2000,
        description="Most recent fetch error message. Should be set when status=ERROR.",
    )
    consecutive_errors: int = Field(
        default=0,
        ge=0,
        description="Count of consecutive fetch failures. Resets to 0 on success.",
    )

    @field_validator("weight")
    @classmethod
    def _validate_weight(cls, v: float) -> float:
        """Enforce weight in [0.1, 2.0]."""
        if v < _WEIGHT_MIN or v > _WEIGHT_MAX:
            raise ValueError(
                f"weight must be in [{_WEIGHT_MIN}, {_WEIGHT_MAX}]; got {v!r}. "
                "Use status=PAUSED to suppress a source instead of weight=0.0."
            )
        return v

    @field_validator("fetch_interval_minutes")
    @classmethod
    def _validate_fetch_interval(cls, v: int) -> int:
        """Enforce fetch_interval_minutes in [1, 1440]."""
        if v < _FETCH_INTERVAL_MIN or v > _FETCH_INTERVAL_MAX:
            raise ValueError(
                f"fetch_interval_minutes must be in "
                f"[{_FETCH_INTERVAL_MIN}, {_FETCH_INTERVAL_MAX}]; got {v!r}."
            )
        return v

    @field_validator("last_fetched_at", mode="before")
    @classmethod
    def _validate_last_fetched_at(cls, v: datetime | None) -> datetime | None:
        """Normalise last_fetched_at to UTC; reject naive datetimes and future values."""
        if v is None:
            return v
        if v.tzinfo is None:
            raise ValueError(
                "last_fetched_at must be timezone-aware (UTC-aware); got naive datetime."
            )
        v = v.astimezone(UTC)
        now = datetime.now(tz=UTC)
        if v > now:
            raise ValueError(f"last_fetched_at must not be in the future; got {v.isoformat()!r}.")
        return v
