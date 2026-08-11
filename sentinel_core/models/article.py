"""Article domain model.

An Article is the fundamental unit of information in Sentinel. Everything
downstream — scoring, entity extraction, deduplication, synthesis, reporting
— operates on Articles.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

from pydantic import Field, field_validator, model_validator

from sentinel_core.enums import (
    ArticleStatus,
    AssetClass,
    MarketRegion,
    Sector,
    Sentiment,
)
from sentinel_core.models._base import SentinelModel
from sentinel_core.types import ConfidenceScore, ImportanceScore, LanguageCode, Url

# Clock-skew tolerance: published_at may be at most this far in the future.
_MAX_FUTURE_PUBLISHED_AT = timedelta(days=7)


class Article(SentinelModel):
    """A single piece of ingested content at any stage of the processing pipeline.

    Articles are created at ingestion (status=INGESTED) and evolve through
    statuses as they move through the pipeline. Raw content fields (title, url,
    content) are never modified after ingestion. Derived fields (asset_class,
    sentiment, importance_score, etc.) are populated by the processing stage.

    Uniqueness constraints (enforced at the database layer):
        - url must be unique across all Article records.
        - content_hash must be unique across all Article records. A hash
          collision is treated as an exact duplicate.

    Cross-field validation rules:
        - duplicate_of_id must be None unless status=DEDUPLICATED.
        - sentiment_confidence must be paired with sentiment (both or neither).
        - importance_confidence must be paired with importance_score (both or neither).
        - published_at must not be more than 7 days in the future.

    Note on content:
        content is nullable. Some RSS sources provide only titles and summaries.
        Whether the scraping layer should auto-fetch full content when content is
        None is a Phase 2 collector decision (see docs/05-contracts.md §4.2
        Ambiguity).

    Fields:
        id: UUID v4 primary key.
        source_id: FK to Source.
        title: Article headline; 1-500 chars.
        url: Canonical article URL. Unique.
        content: Full article body; max 100,000 chars. Optional.
        summary: LLM-generated or author-provided summary; max 2000 chars.
        published_at: UTC publication time as reported by the source. Optional.
        fetched_at: UTC time Sentinel retrieved this article.
        language: ISO 639-1 language code.
        status: Pipeline processing state.
        asset_class: Set by classifier; None until processing completes.
        region: Set by classifier; None until processing completes.
        sector: Set by classifier; None until processing completes.
        sentiment: Set by classifier; None until processing completes.
        sentiment_confidence: Paired with sentiment. None until classification.
        importance_score: Set by scorer; None until scoring completes.
        importance_confidence: Paired with importance_score.
        content_hash: SHA-256 hex digest of (title + url). Unique.
        embedding_id: Reference to pgvector row. None until embedding generated.
        duplicate_of_id: FK to canonical Article. Non-None only when DEDUPLICATED.
        error_message: Set when status=FAILED; max 2000 chars.
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        Article(
            source_id=uuid.UUID("a1b2c3d4-0000-4000-8000-000000000001"),
            title="Fed holds rates steady as inflation cools",
            url="https://feeds.reuters.com/article/fed-rates-2026",
            content="The Federal Reserve held interest rates...",
            published_at=datetime(2026, 8, 7, 14, 30, tzinfo=timezone.utc),
            content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
    """

    source_id: uuid.UUID = Field(
        description="FK to the Source that produced this article.",
    )
    title: str = Field(
        min_length=1,
        max_length=500,
        description="Article headline.",
    )
    url: Url = Field(
        description="Canonical article URL. Unique across all Articles.",
    )
    content: str | None = Field(
        default=None,
        max_length=100_000,
        description=(
            "Full article body. May be None when the source provides only a "
            "title and summary (e.g. some RSS feeds)."
        ),
    )
    summary: str | None = Field(
        default=None,
        max_length=2000,
        description="LLM-generated or author-provided summary.",
    )
    published_at: datetime | None = Field(
        default=None,
        description=(
            "UTC publication time as reported by the source. None when the "
            "source did not provide a publication date."
        ),
    )
    fetched_at: datetime = Field(
        description="UTC time Sentinel retrieved this article.",
    )
    language: LanguageCode = Field(
        default="en",  # type: ignore[assignment]
        description="ISO 639-1 language code. Inherited from source if not detected.",
    )
    status: ArticleStatus = Field(
        default=ArticleStatus.INGESTED,
        description="Current position of this article in the processing pipeline.",
    )
    asset_class: AssetClass | None = Field(
        default=None,
        description="Set by the classifier. None until processing completes.",
    )
    region: MarketRegion | None = Field(
        default=None,
        description="Set by the classifier. None until processing completes.",
    )
    sector: Sector | None = Field(
        default=None,
        description="Set by the classifier. None until processing completes.",
    )
    sentiment: Sentiment | None = Field(
        default=None,
        description="Set by the classifier. None until processing completes.",
    )
    sentiment_confidence: ConfidenceScore | None = Field(
        default=None,
        description=(
            "Confidence of the sentiment classification. Must be paired with "
            "sentiment: both non-None or both None."
        ),
    )
    importance_score: ImportanceScore | None = Field(
        default=None,
        description="Set by the scorer. None until scoring completes.",
    )
    importance_confidence: ConfidenceScore | None = Field(
        default=None,
        description=(
            "Confidence of the importance score. Must be paired with "
            "importance_score: both non-None or both None."
        ),
    )
    content_hash: str = Field(
        min_length=64,
        max_length=64,
        description=(
            "SHA-256 hex digest of (title + url). Used for exact deduplication. "
            "Unique across all Article records."
        ),
    )
    embedding_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "Reference to the pgvector row storing this article's embedding. "
            "None until the embedding has been generated."
        ),
    )
    duplicate_of_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "FK to the canonical Article when status=DEDUPLICATED. "
            "Must be None for all other statuses."
        ),
    )
    error_message: str | None = Field(
        default=None,
        max_length=2000,
        description="Error detail set when status=FAILED.",
    )

    @field_validator("fetched_at", "published_at", mode="before")
    @classmethod
    def _require_utc(cls, v: datetime | None) -> datetime | None:
        """Ensure datetime fields are UTC-aware when provided."""
        if v is not None and v.tzinfo is None:
            raise ValueError("datetime fields must be UTC-aware (tzinfo must not be None).")
        return v

    @field_validator("published_at")
    @classmethod
    def _published_at_not_too_far_future(cls, v: datetime | None) -> datetime | None:
        """Enforce published_at <= now + 7 days (clock-skew tolerance)."""
        if v is None:
            return v
        cutoff = datetime.now(tz=UTC) + _MAX_FUTURE_PUBLISHED_AT
        if v > cutoff:
            raise ValueError(
                f"published_at must not be more than 7 days in the future; got {v.isoformat()!r}."
            )
        return v

    @field_validator("content_hash")
    @classmethod
    def _validate_content_hash(cls, v: str) -> str:
        """Enforce SHA-256 hex digest: 64 lowercase hex characters."""
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError(
                f"content_hash must be a SHA-256 hex digest (64 lowercase hex chars); got {v!r}."
            )
        return v

    @model_validator(mode="after")
    def _validate_cross_field_rules(self) -> Article:
        """Enforce cross-field consistency rules from the contracts."""
        # Rule: duplicate_of_id only set when DEDUPLICATED
        if self.duplicate_of_id is not None and self.status != ArticleStatus.DEDUPLICATED:
            raise ValueError(
                "duplicate_of_id must be None unless status=DEDUPLICATED; "
                f"got status={self.status!r}."
            )

        # Rule: sentiment and sentiment_confidence must be paired
        sentiment_set = self.sentiment is not None
        confidence_set = self.sentiment_confidence is not None
        if sentiment_set != confidence_set:
            raise ValueError("sentiment and sentiment_confidence must both be set or both be None.")

        # Rule: importance_score and importance_confidence must be paired
        importance_set = self.importance_score is not None
        imp_conf_set = self.importance_confidence is not None
        if importance_set != imp_conf_set:
            raise ValueError(
                "importance_score and importance_confidence must both be set or both be None."
            )

        return self
