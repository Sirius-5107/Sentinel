"""Unit tests for sentinel_core.enums."""

from __future__ import annotations

import pytest

from sentinel_core.enums import (
    ArticleStatus,
    AssetClass,
    EntityType,
    EventSeverity,
    MarketRegion,
    PipelineStatus,
    ReportStatus,
    ReportType,
    Sector,
    Sentiment,
    SourceStatus,
    SourceType,
    TaskStatus,
)


@pytest.mark.unit
class TestEnumSerialization:
    """All enums must serialise to their string value (str, Enum)."""

    def test_source_type_is_str(self) -> None:
        assert SourceType.RSS == "rss"
        assert isinstance(SourceType.RSS, str)

    def test_source_status_is_str(self) -> None:
        assert SourceStatus.ACTIVE == "active"

    def test_article_status_is_str(self) -> None:
        assert ArticleStatus.INGESTED == "ingested"

    def test_sentiment_is_str(self) -> None:
        assert Sentiment.BULLISH == "bullish"

    def test_asset_class_is_str(self) -> None:
        assert AssetClass.EQUITY == "equity"

    def test_market_region_is_str(self) -> None:
        assert MarketRegion.US == "us"

    def test_sector_is_str(self) -> None:
        assert Sector.TECHNOLOGY == "technology"

    def test_event_severity_is_str(self) -> None:
        assert EventSeverity.CRITICAL == "critical"

    def test_report_type_is_str(self) -> None:
        assert ReportType.DAILY_BRIEF == "daily_brief"

    def test_report_status_is_str(self) -> None:
        assert ReportStatus.DRAFT == "draft"

    def test_pipeline_status_is_str(self) -> None:
        assert PipelineStatus.PENDING == "pending"

    def test_task_status_is_str(self) -> None:
        assert TaskStatus.SKIPPED == "skipped"

    def test_entity_type_is_str(self) -> None:
        assert EntityType.COMPANY == "company"


@pytest.mark.unit
class TestEnumMembers:
    """All enum members are present and have the correct values."""

    def test_source_type_members(self) -> None:
        assert set(SourceType) == {
            SourceType.RSS,
            SourceType.SCRAPE,
            SourceType.DYNAMIC,
            SourceType.API,
            SourceType.MANUAL,
        }

    def test_source_status_members(self) -> None:
        assert set(SourceStatus) == {
            SourceStatus.ACTIVE,
            SourceStatus.PAUSED,
            SourceStatus.DISABLED,
            SourceStatus.ERROR,
        }

    def test_article_status_members(self) -> None:
        assert set(ArticleStatus) == {
            ArticleStatus.INGESTED,
            ArticleStatus.PROCESSING,
            ArticleStatus.PROCESSED,
            ArticleStatus.DEDUPLICATED,
            ArticleStatus.PUBLISHED,
            ArticleStatus.FAILED,
        }

    def test_sentiment_members(self) -> None:
        assert set(Sentiment) == {
            Sentiment.BULLISH,
            Sentiment.BEARISH,
            Sentiment.NEUTRAL,
            Sentiment.MIXED,
        }

    def test_asset_class_members(self) -> None:
        assert AssetClass.MACRO == "macro"
        assert AssetClass.PRIVATE_CREDIT == "private_credit"
        assert len(list(AssetClass)) == 10

    def test_market_region_members(self) -> None:
        assert len(list(MarketRegion)) == 8
        assert MarketRegion.GLOBAL == "global"

    def test_sector_members(self) -> None:
        assert len(list(Sector)) == 12
        assert Sector.UNKNOWN == "unknown"

    def test_event_severity_members(self) -> None:
        assert set(EventSeverity) == {
            EventSeverity.LOW,
            EventSeverity.MEDIUM,
            EventSeverity.HIGH,
            EventSeverity.CRITICAL,
        }

    def test_report_type_members(self) -> None:
        assert len(list(ReportType)) == 6
        assert ReportType.DAILY_BRIEF == "daily_brief"

    def test_report_status_members(self) -> None:
        assert set(ReportStatus) == {
            ReportStatus.DRAFT,
            ReportStatus.REVIEW,
            ReportStatus.APPROVED,
            ReportStatus.PUBLISHED,
            ReportStatus.FAILED,
        }

    def test_pipeline_status_members(self) -> None:
        assert set(PipelineStatus) == {
            PipelineStatus.PENDING,
            PipelineStatus.RUNNING,
            PipelineStatus.SUCCESS,
            PipelineStatus.PARTIAL,
            PipelineStatus.FAILED,
        }

    def test_task_status_members(self) -> None:
        assert set(TaskStatus) == {
            TaskStatus.PENDING,
            TaskStatus.RUNNING,
            TaskStatus.SUCCESS,
            TaskStatus.FAILED,
            TaskStatus.SKIPPED,
        }

    def test_entity_type_members(self) -> None:
        assert set(EntityType) == {
            EntityType.COMPANY,
            EntityType.PERSON,
            EntityType.ORGANIZATION,
            EntityType.MARKET,
            EntityType.THEME,
            EntityType.UNKNOWN,
        }


@pytest.mark.unit
class TestEnumRoundtrip:
    """Enum values round-trip through string conversion."""

    def test_asset_class_from_value(self) -> None:
        assert AssetClass("equity") is AssetClass.EQUITY

    def test_pipeline_status_from_value(self) -> None:
        assert PipelineStatus("running") is PipelineStatus.RUNNING

    def test_task_status_from_value(self) -> None:
        assert TaskStatus("skipped") is TaskStatus.SKIPPED
