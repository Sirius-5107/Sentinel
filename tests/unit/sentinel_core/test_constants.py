"""Unit tests for sentinel_core.constants."""

from __future__ import annotations

import pytest

from sentinel_core.constants import (
    ARTICLE_CONTENT_HASH_LENGTH,
    ARTICLE_CONTENT_MAX_LENGTH,
    ARTICLE_PUBLISHED_AT_MAX_FUTURE_DAYS,
    ARTICLE_SUMMARY_MAX_LENGTH,
    ARTICLE_TITLE_MAX_LENGTH,
    DAILY_REPORT_COVERAGE_DATE_MAX_FUTURE_DAYS,
    MARKET_EVENT_OCCURRED_AT_MAX_FUTURE_DAYS,
    MARKET_EVENT_SUMMARY_MIN_LENGTH,
    PIPELINE_ALLOWED_TRIGGERS,
    SOURCE_FETCH_INTERVAL_MAX_MINUTES,
    SOURCE_FETCH_INTERVAL_MIN_MINUTES,
    SOURCE_WEIGHT_MAX,
    SOURCE_WEIGHT_MIN,
)


@pytest.mark.unit
class TestConstantValues:
    """Constants must have the values the domain models depend on."""

    def test_article_title_max_length(self) -> None:
        assert ARTICLE_TITLE_MAX_LENGTH == 500

    def test_article_content_max_length(self) -> None:
        assert ARTICLE_CONTENT_MAX_LENGTH == 100_000

    def test_article_summary_max_length(self) -> None:
        assert ARTICLE_SUMMARY_MAX_LENGTH == 2_000

    def test_article_content_hash_length(self) -> None:
        assert ARTICLE_CONTENT_HASH_LENGTH == 64

    def test_article_published_at_max_future_days(self) -> None:
        assert ARTICLE_PUBLISHED_AT_MAX_FUTURE_DAYS == 7

    def test_market_event_summary_min_length(self) -> None:
        assert MARKET_EVENT_SUMMARY_MIN_LENGTH == 100

    def test_market_event_occurred_at_max_future_days(self) -> None:
        assert MARKET_EVENT_OCCURRED_AT_MAX_FUTURE_DAYS == 30

    def test_source_weight_min(self) -> None:
        assert SOURCE_WEIGHT_MIN == 0.1

    def test_source_weight_max(self) -> None:
        assert SOURCE_WEIGHT_MAX == 2.0

    def test_source_fetch_interval_min(self) -> None:
        assert SOURCE_FETCH_INTERVAL_MIN_MINUTES == 1

    def test_source_fetch_interval_max(self) -> None:
        assert SOURCE_FETCH_INTERVAL_MAX_MINUTES == 1440

    def test_daily_report_coverage_date_max_future_days(self) -> None:
        assert DAILY_REPORT_COVERAGE_DATE_MAX_FUTURE_DAYS == 7

    def test_pipeline_allowed_triggers(self) -> None:
        assert frozenset({"scheduler", "manual", "api"}) == PIPELINE_ALLOWED_TRIGGERS


@pytest.mark.unit
class TestConstantsConsistencyWithModels:
    """Constants must match the validation limits in the domain models."""

    def test_market_event_summary_min_matches_model(self) -> None:
        """The model rejects summaries below MARKET_EVENT_SUMMARY_MIN_LENGTH."""
        from datetime import UTC, datetime

        from pydantic import ValidationError as PydanticValidationError

        from sentinel_core.enums import AssetClass, EventSeverity, MarketRegion, Sentiment
        from sentinel_core.models import MarketEvent

        short_summary = "x" * (MARKET_EVENT_SUMMARY_MIN_LENGTH - 1)
        with pytest.raises(PydanticValidationError):
            MarketEvent(
                title="Test",
                summary=short_summary,
                asset_class=AssetClass.MACRO,
                region=MarketRegion.US,
                severity=EventSeverity.HIGH,
                sentiment=Sentiment.NEUTRAL,
                sentiment_confidence=0.8,
                importance_score=5.0,
                importance_confidence=0.8,
                occurred_at=datetime.now(tz=UTC),
            )

    def test_article_content_hash_length_matches_model(self) -> None:
        """The model rejects hashes shorter or longer than 64 chars."""
        from datetime import UTC, datetime
        from typing import cast
        import uuid

        from pydantic import HttpUrl
        from pydantic import ValidationError as PydanticValidationError

        from sentinel_core.models import Article

        with pytest.raises(PydanticValidationError):
            Article(
                source_id=uuid.uuid4(),
                title="Test",
                url=cast("HttpUrl", "https://example.com/article"),
                fetched_at=datetime.now(tz=UTC),
                content_hash="short",  # Not 64 chars
            )
