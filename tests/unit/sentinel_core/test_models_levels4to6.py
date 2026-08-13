"""Unit tests for MarketEvent, PipelineRun, Task, DailyReport, ReportSection."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import uuid

from pydantic import ValidationError
import pytest

from sentinel_core.enums import (
    AssetClass,
    EventSeverity,
    MarketRegion,
    PipelineStatus,
    ReportStatus,
    ReportType,
    Sector,
    Sentiment,
    TaskStatus,
)
from sentinel_core.models import (
    DailyReport,
    MarketEvent,
    PipelineRun,
    ReportSection,
    Task,
)


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


def _utctoday() -> date:
    """Return today's date in UTC — matches the validator in DailyReport."""
    return datetime.now(tz=UTC).date()


# -- MarketEvent --------------------------------------------------------------


@pytest.mark.unit
class TestMarketEvent:
    def test_minimal_construction(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        e = MarketEvent(**market_event_kwargs)
        assert e.title == "Federal Reserve holds rates at 5.25-5.50%"
        assert e.asset_class == AssetClass.MACRO
        assert e.region == MarketRegion.US
        assert e.severity == EventSeverity.HIGH
        assert e.sentiment == Sentiment.NEUTRAL
        assert e.sector is None
        assert e.market_id is None
        assert e.embedding_id is None

    def test_is_frozen(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        e = MarketEvent(**market_event_kwargs)
        with pytest.raises((TypeError, ValidationError)):
            e.title = "Changed"  # type: ignore[misc]

    def test_summary_too_short_raises(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            MarketEvent(**{**market_event_kwargs, "summary": "Too short."})

    def test_summary_exactly_100_chars_valid(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        e = MarketEvent(**{**market_event_kwargs, "summary": "x" * 100})
        assert len(e.summary) == 100

    def test_summary_max_length_raises(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            MarketEvent(**{**market_event_kwargs, "summary": "x" * 2001})

    def test_occurred_at_too_far_future_raises(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        far_future = _utcnow() + timedelta(days=31)
        with pytest.raises(ValidationError, match="future"):
            MarketEvent(**{**market_event_kwargs, "occurred_at": far_future})

    def test_occurred_at_within_30_days_valid(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        near_future = _utcnow() + timedelta(days=29)
        e = MarketEvent(**{**market_event_kwargs, "occurred_at": near_future})
        assert e.occurred_at == near_future

    def test_naive_occurred_at_raises(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            MarketEvent(**{**market_event_kwargs, "occurred_at": dt(2026, 8, 7)})

    def test_with_sector(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        e = MarketEvent(**{**market_event_kwargs, "sector": Sector.TECHNOLOGY})
        assert e.sector == Sector.TECHNOLOGY

    def test_with_market_id(self, market_event_kwargs: dict, market_id: uuid.UUID) -> None:  # type: ignore[type-arg]
        e = MarketEvent(**{**market_event_kwargs, "market_id": market_id})
        assert e.market_id == market_id

    def test_title_empty_raises(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            MarketEvent(**{**market_event_kwargs, "title": ""})

    def test_title_max_length_raises(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            MarketEvent(**{**market_event_kwargs, "title": "x" * 301})

    def test_sentiment_confidence_out_of_range_raises(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            MarketEvent(**{**market_event_kwargs, "sentiment_confidence": 1.5})

    def test_importance_score_out_of_range_raises(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            MarketEvent(**{**market_event_kwargs, "importance_score": 10.01})

    def test_json_serialization(self, market_event_kwargs: dict) -> None:  # type: ignore[type-arg]
        e = MarketEvent(**market_event_kwargs)
        data = e.model_dump(mode="json")
        assert data["asset_class"] == "macro"
        assert data["severity"] == "high"
        assert isinstance(data["id"], str)


# -- PipelineRun --------------------------------------------------------------


@pytest.mark.unit
class TestPipelineRun:
    def test_minimal_construction(self) -> None:
        pr = PipelineRun()
        assert pr.status == PipelineStatus.PENDING
        assert pr.trigger == "scheduler"
        assert pr.started_at is None
        assert pr.completed_at is None
        assert pr.articles_ingested == 0
        assert pr.error_count == 0

    def test_duration_seconds_none_when_not_complete(self) -> None:
        pr = PipelineRun()
        assert pr.duration_seconds is None

    def test_duration_seconds_computed(self) -> None:
        start = _utcnow()
        end = start + timedelta(seconds=42)
        pr = PipelineRun(status=PipelineStatus.SUCCESS, started_at=start, completed_at=end)
        assert pr.duration_seconds == pytest.approx(42.0)

    def test_duration_seconds_is_not_a_field(self) -> None:
        pr = PipelineRun()
        data = pr.model_dump()
        assert "duration_seconds" not in data

    def test_started_at_must_be_none_when_pending(self) -> None:
        with pytest.raises(ValidationError, match="started_at"):
            PipelineRun(status=PipelineStatus.PENDING, started_at=_utcnow())

    def test_completed_at_must_be_none_when_running(self) -> None:
        with pytest.raises(ValidationError, match="completed_at"):
            PipelineRun(
                status=PipelineStatus.RUNNING,
                started_at=_utcnow(),
                completed_at=_utcnow(),
            )

    def test_completed_at_before_started_at_raises(self) -> None:
        start = _utcnow()
        with pytest.raises(ValidationError, match=">= started_at"):
            PipelineRun(
                status=PipelineStatus.SUCCESS,
                started_at=start,
                completed_at=start - timedelta(seconds=1),
            )

    def test_articles_processed_exceeds_ingested_raises(self) -> None:
        with pytest.raises(ValidationError, match="articles_processed"):
            PipelineRun(articles_ingested=5, articles_processed=10)

    def test_invalid_trigger_raises(self) -> None:
        with pytest.raises(ValidationError, match="trigger"):
            PipelineRun(trigger="cron")

    def test_valid_triggers(self) -> None:
        for trigger in ("scheduler", "manual", "api"):
            pr = PipelineRun(trigger=trigger)
            assert pr.trigger == trigger

    def test_naive_started_at_raises(self) -> None:
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            PipelineRun(status=PipelineStatus.RUNNING, started_at=dt(2026, 8, 7))

    def test_successful_run(self) -> None:
        start = _utcnow()
        end = start + timedelta(minutes=5)
        pr = PipelineRun(
            status=PipelineStatus.SUCCESS,
            started_at=start,
            completed_at=end,
            articles_ingested=100,
            articles_processed=95,
            articles_deduplicated=5,
            events_synthesised=20,
            trigger="scheduler",
        )
        assert pr.duration_seconds == pytest.approx(300.0)
        assert pr.articles_ingested == 100

    def test_is_frozen(self) -> None:
        pr = PipelineRun()
        with pytest.raises((TypeError, ValidationError)):
            pr.trigger = "manual"  # type: ignore[misc]

    def test_json_serialization(self) -> None:
        pr = PipelineRun()
        data = pr.model_dump(mode="json")
        assert data["status"] == "pending"
        assert data["trigger"] == "scheduler"
        assert "duration_seconds" not in data


# -- Task ---------------------------------------------------------------------


@pytest.mark.unit
class TestTask:
    def test_minimal_construction(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        t = Task(**task_kwargs)
        assert t.name == "collect.reuters_rss"
        assert t.status == TaskStatus.PENDING
        assert t.items_processed == 0
        assert t.items_failed == 0
        assert t.metadata == {}
        assert t.started_at is None
        assert t.completed_at is None

    def test_duration_seconds_none_when_incomplete(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        t = Task(**task_kwargs)
        assert t.duration_seconds is None

    def test_duration_seconds_computed(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        start = _utcnow()
        end = start + timedelta(seconds=10)
        t = Task(
            **{
                **task_kwargs,
                "status": TaskStatus.SUCCESS,
                "started_at": start,
                "completed_at": end,
            }
        )
        assert t.duration_seconds == pytest.approx(10.0)

    def test_duration_seconds_not_in_dump(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        t = Task(**task_kwargs)
        assert "duration_seconds" not in t.model_dump()

    def test_completed_at_none_when_pending(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="completed_at"):
            Task(**{**task_kwargs, "completed_at": _utcnow()})

    def test_completed_at_before_started_raises(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        start = _utcnow()
        with pytest.raises(ValidationError, match=">= started_at"):
            Task(
                **{
                    **task_kwargs,
                    "status": TaskStatus.SUCCESS,
                    "started_at": start,
                    "completed_at": start - timedelta(seconds=1),
                }
            )

    def test_items_failed_exceeds_processed_raises(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="items_failed"):
            Task(**{**task_kwargs, "items_processed": 3, "items_failed": 5})

    def test_negative_items_processed_raises(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Task(**{**task_kwargs, "items_processed": -1})

    def test_metadata_stored(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        t = Task(
            **{
                **task_kwargs,
                "status": TaskStatus.SUCCESS,
                "started_at": _utcnow(),
                "completed_at": _utcnow() + timedelta(seconds=1),
                "metadata": {"source": "Reuters", "batch_size": "50"},
            }
        )
        assert t.metadata["source"] == "Reuters"

    def test_skipped_status_valid(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        t = Task(**{**task_kwargs, "status": TaskStatus.SKIPPED})
        assert t.status == TaskStatus.SKIPPED

    def test_is_frozen(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        t = Task(**task_kwargs)
        with pytest.raises((TypeError, ValidationError)):
            t.name = "Changed"  # type: ignore[misc]

    def test_json_serialization(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        t = Task(**task_kwargs)
        data = t.model_dump(mode="json")
        assert data["name"] == "collect.reuters_rss"
        assert data["status"] == "pending"

    def test_naive_completed_at_raises(self, task_kwargs: dict) -> None:  # type: ignore[type-arg]
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            Task(
                **{
                    **task_kwargs,
                    "status": TaskStatus.SUCCESS,
                    "started_at": _utcnow(),
                    "completed_at": dt(2026, 8, 7),
                }
            )


# -- DailyReport --------------------------------------------------------------


@pytest.mark.unit
class TestDailyReport:
    def test_minimal_construction(self, daily_report_kwargs: dict) -> None:  # type: ignore[type-arg]
        r = DailyReport(**daily_report_kwargs)
        assert r.report_type == ReportType.DAILY_BRIEF
        assert r.status == ReportStatus.DRAFT
        assert r.title is None
        assert r.executive_summary is None
        assert r.published_at is None
        assert r.notion_page_id is None
        assert r.article_count == 0
        assert r.event_count == 0

    def test_is_frozen(self, daily_report_kwargs: dict) -> None:  # type: ignore[type-arg]
        r = DailyReport(**daily_report_kwargs)
        with pytest.raises((TypeError, ValidationError)):
            r.status = ReportStatus.PUBLISHED  # type: ignore[misc]

    def test_coverage_date_too_far_future_raises(self) -> None:
        # Use UTC date + 9 days — safely beyond the 7-day limit regardless of timezone offset.
        far_future = _utctoday() + timedelta(days=9)
        with pytest.raises(ValidationError, match="future"):
            DailyReport(coverage_date=far_future)

    def test_coverage_date_6_days_valid(self) -> None:
        # Use UTC date + 6 days — safely within the 7-day limit on any timezone offset.
        near_future = _utctoday() + timedelta(days=6)
        r = DailyReport(coverage_date=near_future)
        assert r.coverage_date == near_future

    def test_published_at_requires_published_status(self, daily_report_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="published_at"):
            DailyReport(
                **{**daily_report_kwargs, "status": ReportStatus.DRAFT, "published_at": _utcnow()}
            )

    def test_notion_page_id_requires_published_status(self, daily_report_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="notion_page_id"):
            DailyReport(
                **{
                    **daily_report_kwargs,
                    "status": ReportStatus.APPROVED,
                    "notion_page_id": "some-notion-id",
                }
            )

    def test_published_state_valid(self, daily_report_kwargs: dict) -> None:  # type: ignore[type-arg]
        r = DailyReport(
            **{
                **daily_report_kwargs,
                "status": ReportStatus.PUBLISHED,
                "published_at": _utcnow(),
                "notion_page_id": "notion-page-abc123",
            }
        )
        assert r.status == ReportStatus.PUBLISHED
        assert r.notion_page_id == "notion-page-abc123"

    def test_naive_published_at_raises(self, daily_report_kwargs: dict) -> None:  # type: ignore[type-arg]
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            DailyReport(
                **{
                    **daily_report_kwargs,
                    "status": ReportStatus.PUBLISHED,
                    "published_at": dt(2026, 8, 7),
                    "notion_page_id": "abc",
                }
            )

    def test_negative_article_count_raises(self, daily_report_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            DailyReport(**{**daily_report_kwargs, "article_count": -1})

    def test_title_max_length_raises(self, daily_report_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            DailyReport(**{**daily_report_kwargs, "title": "x" * 301})

    def test_json_serialization(self, daily_report_kwargs: dict) -> None:  # type: ignore[type-arg]
        r = DailyReport(**daily_report_kwargs)
        data = r.model_dump(mode="json")
        assert data["report_type"] == "daily_brief"
        assert data["status"] == "draft"
        assert isinstance(data["id"], str)


# -- ReportSection ------------------------------------------------------------


@pytest.mark.unit
class TestReportSection:
    def test_minimal_construction(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = ReportSection(**report_section_kwargs)
        assert s.title == "US Equities"
        assert s.order == 2
        assert s.content is None
        assert s.word_count is None
        assert s.event_count == 0
        assert s.theme_id is None
        assert s.asset_class is None
        assert s.region is None

    def test_is_frozen(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = ReportSection(**report_section_kwargs)
        with pytest.raises((TypeError, ValidationError)):
            s.title = "Changed"  # type: ignore[misc]

    def test_full_construction(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        content = "US equity markets rose as tech earnings beat expectations."
        s = ReportSection(
            **{
                **report_section_kwargs,
                "content": content,
                "asset_class": AssetClass.EQUITY,
                "region": MarketRegion.US,
                "word_count": len(content),
                "event_count": 3,
            }
        )
        assert s.content == content
        assert s.word_count == len(content)
        assert s.event_count == 3

    def test_negative_order_raises(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            ReportSection(**{**report_section_kwargs, "order": -1})

    def test_order_zero_valid(self, report_id: uuid.UUID) -> None:
        s = ReportSection(report_id=report_id, title="Executive Summary", order=0)
        assert s.order == 0

    def test_negative_word_count_raises(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="word_count"):
            ReportSection(**{**report_section_kwargs, "word_count": -1})

    def test_negative_event_count_raises(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            ReportSection(**{**report_section_kwargs, "event_count": -1})

    def test_title_empty_raises(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            ReportSection(**{**report_section_kwargs, "title": ""})

    def test_title_max_length_raises(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            ReportSection(**{**report_section_kwargs, "title": "x" * 201})

    def test_content_max_length_raises(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            ReportSection(**{**report_section_kwargs, "content": "x" * 20_001})

    def test_with_theme_id(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        theme_id = uuid.uuid4()
        s = ReportSection(**{**report_section_kwargs, "theme_id": theme_id})
        assert s.theme_id == theme_id

    def test_word_count_stores_char_count(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        content = "Ten chars."
        s = ReportSection(
            **{**report_section_kwargs, "content": content, "word_count": len(content)}
        )
        assert s.word_count == 10

    def test_json_serialization(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = ReportSection(**report_section_kwargs)
        data = s.model_dump(mode="json")
        assert data["title"] == "US Equities"
        assert data["order"] == 2
        assert isinstance(data["id"], str)

    def test_content_and_word_count_both_none_valid(self, report_section_kwargs: dict) -> None:  # type: ignore[type-arg]
        s = ReportSection(**{**report_section_kwargs, "content": None, "word_count": None})
        assert s.content is None
        assert s.word_count is None


# -- SentinelModel base -------------------------------------------------------


@pytest.mark.unit
class TestSentinelModelBase:
    def test_model_dump_json_safe(self) -> None:
        pr = PipelineRun()
        data = pr.model_dump_json_safe()
        assert isinstance(data["id"], str)
        assert isinstance(data["created_at"], str)
