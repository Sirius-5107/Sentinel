"""Unit tests for Source and Article models."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import uuid

from pydantic import ValidationError
import pytest

from sentinel_core.enums import (
    ArticleStatus,
    AssetClass,
    MarketRegion,
    Sector,
    Sentiment,
    SourceStatus,
    SourceType,
)
from sentinel_core.models import Article, Source


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


# -- Source -------------------------------------------------------------------


@pytest.mark.unit
class TestSource:
    def test_minimal_construction(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = Source(**source_kwargs)
        assert s.name == "Reuters Business"
        assert s.source_type == SourceType.RSS
        assert s.status == SourceStatus.ACTIVE
        assert s.language == "en"
        assert s.weight == 1.0
        assert s.fetch_interval_minutes == 60
        assert s.consecutive_errors == 0
        assert s.last_fetched_at is None
        assert s.last_error is None

    def test_is_frozen(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = Source(**source_kwargs)
        with pytest.raises((TypeError, ValidationError)):
            s.name = "Changed"  # type: ignore[misc]

    def test_weight_lower_bound(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = Source(**{**source_kwargs, "weight": 0.1})
        assert s.weight == 0.1

    def test_weight_upper_bound(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = Source(**{**source_kwargs, "weight": 2.0})
        assert s.weight == 2.0

    def test_weight_below_minimum_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="weight"):
            Source(**{**source_kwargs, "weight": 0.09})

    def test_weight_above_maximum_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="weight"):
            Source(**{**source_kwargs, "weight": 2.01})

    def test_fetch_interval_lower_bound(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = Source(**{**source_kwargs, "fetch_interval_minutes": 1})
        assert s.fetch_interval_minutes == 1

    def test_fetch_interval_upper_bound(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = Source(**{**source_kwargs, "fetch_interval_minutes": 1440})
        assert s.fetch_interval_minutes == 1440

    def test_fetch_interval_zero_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="fetch_interval_minutes"):
            Source(**{**source_kwargs, "fetch_interval_minutes": 0})

    def test_fetch_interval_too_large_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="fetch_interval_minutes"):
            Source(**{**source_kwargs, "fetch_interval_minutes": 1441})

    def test_negative_consecutive_errors_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Source(**{**source_kwargs, "consecutive_errors": -1})

    def test_last_fetched_at_in_future_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        future = _utcnow() + timedelta(seconds=60)
        with pytest.raises(ValidationError, match="future"):
            Source(**{**source_kwargs, "last_fetched_at": future})

    def test_naive_last_fetched_at_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            Source(**{**source_kwargs, "last_fetched_at": dt(2026, 8, 7)})

    def test_last_fetched_at_past_valid(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        past = _utcnow() - timedelta(hours=1)
        s = Source(**{**source_kwargs, "last_fetched_at": past})
        assert s.last_fetched_at == past

    def test_invalid_url_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Source(**{**source_kwargs, "url": "not-a-url"})

    def test_name_too_long_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Source(**{**source_kwargs, "name": "x" * 201})

    def test_last_error_max_length_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Source(**{**source_kwargs, "last_error": "x" * 2001})

    def test_paused_status(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = Source(**{**source_kwargs, "status": SourceStatus.PAUSED})
        assert s.status == SourceStatus.PAUSED

    def test_json_serialization(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = Source(**source_kwargs)
        data = s.model_dump(mode="json")
        assert data["name"] == "Reuters Business"
        assert data["source_type"] == "rss"
        assert data["status"] == "active"

    def test_naive_created_at_raises(self, source_kwargs: dict) -> None:  # type: ignore[type-arg]
        """SentinelModel timestamps must be UTC-aware."""
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            Source(**{**source_kwargs, "created_at": dt(2026, 8, 7)})


# -- Article ------------------------------------------------------------------


@pytest.mark.unit
class TestArticle:
    def test_minimal_construction(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        a = Article(**article_kwargs)
        assert a.title == "Fed holds rates steady"
        assert a.status == ArticleStatus.INGESTED
        assert a.language == "en"
        assert a.content is None
        assert a.sentiment is None
        assert a.sentiment_confidence is None
        assert a.importance_score is None
        assert a.importance_confidence is None
        assert a.duplicate_of_id is None

    def test_is_frozen(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        a = Article(**article_kwargs)
        with pytest.raises((TypeError, ValidationError)):
            a.title = "Changed"  # type: ignore[misc]

    def test_full_construction(self, article_kwargs: dict, source_id: uuid.UUID) -> None:  # type: ignore[type-arg]
        a = Article(
            **{
                **article_kwargs,
                "content": "Full article body here.",
                "summary": "Brief summary.",
                "published_at": _utcnow() - timedelta(hours=1),
                "language": "en",
                "status": ArticleStatus.PROCESSED,
                "asset_class": AssetClass.MACRO,
                "region": MarketRegion.US,
                "sector": Sector.FINANCIALS,
                "sentiment": Sentiment.BULLISH,
                "sentiment_confidence": 0.9,
                "importance_score": 6.5,
                "importance_confidence": 0.8,
            }
        )
        assert a.sentiment == Sentiment.BULLISH
        assert a.importance_score == 6.5

    def test_duplicate_of_id_requires_deduplicated_status(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="DEDUPLICATED"):
            Article(**{**article_kwargs, "duplicate_of_id": uuid.uuid4()})

    def test_duplicate_of_id_valid_when_deduplicated(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        canonical_id = uuid.uuid4()
        a = Article(
            **{
                **article_kwargs,
                "status": ArticleStatus.DEDUPLICATED,
                "duplicate_of_id": canonical_id,
            }
        )
        assert a.duplicate_of_id == canonical_id

    def test_sentiment_without_confidence_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="sentiment"):
            Article(
                **{**article_kwargs, "sentiment": Sentiment.BULLISH, "sentiment_confidence": None}
            )

    def test_confidence_without_sentiment_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="sentiment"):
            Article(**{**article_kwargs, "sentiment": None, "sentiment_confidence": 0.9})

    def test_importance_score_without_confidence_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="importance"):
            Article(**{**article_kwargs, "importance_score": 5.0, "importance_confidence": None})

    def test_importance_confidence_without_score_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="importance"):
            Article(**{**article_kwargs, "importance_score": None, "importance_confidence": 0.8})

    def test_published_at_too_far_future_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="future"):
            Article(**{**article_kwargs, "published_at": _utcnow() + timedelta(days=8)})

    def test_published_at_within_7_days_valid(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        near_future = _utcnow() + timedelta(days=6)
        a = Article(**{**article_kwargs, "published_at": near_future})
        assert a.published_at == near_future

    def test_naive_fetched_at_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            Article(**{**article_kwargs, "fetched_at": dt(2026, 8, 7)})

    def test_invalid_content_hash_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Article(**{**article_kwargs, "content_hash": "not-a-sha256-hash"})

    def test_content_hash_wrong_length_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Article(**{**article_kwargs, "content_hash": "abc123"})

    def test_content_max_length_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Article(**{**article_kwargs, "content": "x" * 100_001})

    def test_summary_max_length_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Article(**{**article_kwargs, "summary": "x" * 2001})

    def test_title_empty_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Article(**{**article_kwargs, "title": ""})

    def test_invalid_url_raises(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Article(**{**article_kwargs, "url": "not-a-url"})

    def test_json_serialization(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        a = Article(**article_kwargs)
        data = a.model_dump(mode="json")
        assert data["title"] == "Fed holds rates steady"
        assert data["status"] == "ingested"
        assert isinstance(data["id"], str)
        assert isinstance(data["source_id"], str)

    def test_published_at_none_valid(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        a = Article(**{**article_kwargs, "published_at": None})
        assert a.published_at is None

    def test_valid_content_hash_accepted(self, article_kwargs: dict) -> None:  # type: ignore[type-arg]
        valid_hash = "a" * 64
        a = Article(**{**article_kwargs, "content_hash": valid_hash})
        assert a.content_hash == valid_hash
