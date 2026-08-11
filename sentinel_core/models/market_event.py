"""MarketEvent domain model.

A MarketEvent is the output of the intelligence layer's synthesis step —
a discrete, time-bounded financial or economic development with market impact.
This is the core of ADR-0001 (event-centric data model).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

from pydantic import Field, field_validator

from sentinel_core.enums import (
    AssetClass,
    EventSeverity,
    MarketRegion,
    Sector,
    Sentiment,
)
from sentinel_core.models._base import SentinelModel
from sentinel_core.types import ConfidenceScore, ImportanceScore

# MarketEvent may reference an event up to 30 days in the future.
_MAX_FUTURE_OCCURRED_AT = timedelta(days=30)

# Summary minimum length enforces the "explain why it matters" principle.
_SUMMARY_MIN_LENGTH = 100


class MarketEvent(SentinelModel):
    """A discrete financial or economic development with market impact.

    MarketEvents are derived from one or more Articles by the intelligence
    layer. They are the primary signal objects: what the knowledge base tracks
    over time, and what report sections are built from.

    This model implements ADR-0001 (event-centric data model): all financial
    developments are represented as events with typed entities, a severity
    level, and temporal attributes.

    Evidence requirement (see docs/05-contracts.md §4.8 Ambiguity):
        At least one source Article must be associated with each MarketEvent
        before it is persisted. This constraint is enforced at the application
        layer (Phase 4), not in this Pydantic model, because the model does
        not hold the list of source article UUIDs — that is a database join.
        The minimum article threshold may be raised by the intelligence layer's
        configuration.

    Validation rules:
        - summary must be at least 100 characters ("explain why it matters").
        - occurred_at must not be more than 30 days in the future.
        - All datetime fields must be UTC-aware.

    Fields:
        id: UUID v4 primary key.
        title: Concise, factual event description; 1-300 chars.
        summary: Synthesised narrative explaining the event and its significance;
            100-2000 chars.
        asset_class: Primary asset class affected.
        region: Primary geographic region.
        sector: Sector, if event is sector-specific. Optional.
        severity: Impact level.
        sentiment: Market sentiment signal of this event.
        sentiment_confidence: Confidence in the sentiment assignment.
        importance_score: Signal importance score.
        importance_confidence: Confidence in the importance score.
        occurred_at: UTC time the real-world event occurred or was announced.
        market_id: FK to Market most directly affected. Optional.
        embedding_id: Reference to pgvector row. None until embedding generated.
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        MarketEvent(
            title="Federal Reserve holds rates at 5.25-5.50%",
            summary=(
                "The Federal Reserve held the federal funds rate steady at "
                "5.25-5.50% at its August 2026 meeting, citing continued "
                "progress on inflation while maintaining optionality for a "
                "September cut. This reinforces the higher-for-longer narrative "
                "that has supported the US dollar and pressured rate-sensitive "
                "equities."
            ),
            asset_class=AssetClass.MACRO,
            region=MarketRegion.US,
            severity=EventSeverity.HIGH,
            sentiment=Sentiment.NEUTRAL,
            sentiment_confidence=0.85,
            importance_score=7.5,
            importance_confidence=0.78,
            occurred_at=datetime(2026, 8, 7, 18, 0, tzinfo=timezone.utc),
        )
    """

    title: str = Field(
        min_length=1,
        max_length=300,
        description="Concise, factual description of the market event.",
    )
    summary: str = Field(
        min_length=_SUMMARY_MIN_LENGTH,
        max_length=2000,
        description=(
            "Synthesised narrative explaining the event and why it matters. "
            "Minimum 100 characters — one-line summaries are not permitted. "
            "Implements the 'explain why it matters' core principle."
        ),
    )
    asset_class: AssetClass = Field(
        description="Primary financial asset class affected by this event.",
    )
    region: MarketRegion = Field(
        description="Primary geographic region of this event.",
    )
    sector: Sector | None = Field(
        default=None,
        description="Industry sector, if this event is sector-specific.",
    )
    severity: EventSeverity = Field(
        description="Impact level of this market event.",
    )
    sentiment: Sentiment = Field(
        description="Market sentiment signal carried by this event.",
    )
    sentiment_confidence: ConfidenceScore = Field(
        description="Confidence in the sentiment classification (0.0-1.0).",
    )
    importance_score: ImportanceScore = Field(
        description="Signal importance score (0.0-10.0).",
    )
    importance_confidence: ConfidenceScore = Field(
        description="Confidence in the importance score (0.0-1.0).",
    )
    occurred_at: datetime = Field(
        description=(
            "UTC timestamp of when the real-world event occurred or was announced. "
            "Must not be more than 30 days in the future."
        ),
    )
    market_id: uuid.UUID | None = Field(
        default=None,
        description="FK to the Market most directly affected. Optional.",
    )
    embedding_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "Reference to the pgvector row storing this event's embedding. "
            "None until the embedding has been generated."
        ),
    )

    @field_validator("occurred_at", mode="before")
    @classmethod
    def _validate_occurred_at(cls, v: datetime) -> datetime:
        """Ensure occurred_at is UTC-aware and not more than 30 days in the future."""
        if v.tzinfo is None:
            raise ValueError("occurred_at must be UTC-aware (tzinfo must not be None).")
        cutoff = datetime.now(tz=UTC) + _MAX_FUTURE_OCCURRED_AT
        if v > cutoff:
            raise ValueError(
                f"occurred_at must not be more than 30 days in the future; got {v.isoformat()!r}."
            )
        return v
