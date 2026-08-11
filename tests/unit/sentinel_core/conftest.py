"""Shared pytest fixtures for sentinel_core unit tests."""

from __future__ import annotations

from datetime import UTC, date, datetime
import hashlib
import uuid

import pytest

from sentinel_core.enums import (
    AssetClass,
    EventSeverity,
    MarketRegion,
    Sentiment,
    SourceType,
)

# -- Helpers ------------------------------------------------------------------


def utcnow() -> datetime:
    """Return the current UTC time."""
    return datetime.now(tz=UTC)


def content_hash(title: str, url: str) -> str:
    """Compute a deterministic SHA-256 hex digest for an article."""
    return hashlib.sha256(f"{title}{url}".encode()).hexdigest()


# -- Common UUIDs -------------------------------------------------------------


@pytest.fixture()
def source_id() -> uuid.UUID:
    """A fixed UUID for a Source."""
    return uuid.UUID("a1b2c3d4-0000-4000-8000-000000000001")


@pytest.fixture()
def market_id() -> uuid.UUID:
    """A fixed UUID for a Market."""
    return uuid.UUID("b2c3d4e5-0000-4000-8000-000000000002")


@pytest.fixture()
def pipeline_run_id() -> uuid.UUID:
    """A fixed UUID for a PipelineRun."""
    return uuid.UUID("c3d4e5f6-0000-4000-8000-000000000003")


@pytest.fixture()
def report_id() -> uuid.UUID:
    """A fixed UUID for a DailyReport."""
    return uuid.UUID("d4e5f6a7-0000-4000-8000-000000000004")


# -- Minimal valid kwargs for each model --------------------------------------


@pytest.fixture()
def market_kwargs(market_id: uuid.UUID) -> dict:  # type: ignore[type-arg]
    """Minimal valid kwargs for a Market."""
    return {
        "id": market_id,
        "name": "New York Stock Exchange",
        "abbreviation": "NYSE",
        "country": "US",
        "region": MarketRegion.US,
        "currency": "USD",
        "timezone": "America/New_York",
    }


@pytest.fixture()
def source_kwargs(source_id: uuid.UUID) -> dict:  # type: ignore[type-arg]
    """Minimal valid kwargs for a Source."""
    return {
        "id": source_id,
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "source_type": SourceType.RSS,
        "region": MarketRegion.GLOBAL,
        "asset_class": AssetClass.MACRO,
    }


@pytest.fixture()
def article_kwargs(source_id: uuid.UUID) -> dict:  # type: ignore[type-arg]
    """Minimal valid kwargs for an Article."""
    title = "Fed holds rates steady"
    url = "https://feeds.reuters.com/article/fed-rates-2026"
    return {
        "source_id": source_id,
        "title": title,
        "url": url,
        "fetched_at": utcnow(),
        "content_hash": content_hash(title, url),
    }


@pytest.fixture()
def market_event_kwargs() -> dict:  # type: ignore[type-arg]
    """Minimal valid kwargs for a MarketEvent."""
    return {
        "title": "Federal Reserve holds rates at 5.25-5.50%",
        "summary": (
            "The Federal Reserve held the federal funds rate steady at 5.25-5.50% "
            "at its August 2026 meeting, citing continued progress on inflation "
            "while maintaining optionality for a September cut. This reinforces the "
            "higher-for-longer narrative."
        ),
        "asset_class": AssetClass.MACRO,
        "region": MarketRegion.US,
        "severity": EventSeverity.HIGH,
        "sentiment": Sentiment.NEUTRAL,
        "sentiment_confidence": 0.85,
        "importance_score": 7.5,
        "importance_confidence": 0.78,
        "occurred_at": utcnow(),
    }


@pytest.fixture()
def pipeline_run_kwargs(pipeline_run_id: uuid.UUID) -> dict:  # type: ignore[type-arg]
    """Minimal valid kwargs for a PipelineRun."""
    return {"id": pipeline_run_id}


@pytest.fixture()
def task_kwargs(pipeline_run_id: uuid.UUID) -> dict:  # type: ignore[type-arg]
    """Minimal valid kwargs for a Task."""
    return {
        "pipeline_run_id": pipeline_run_id,
        "name": "collect.reuters_rss",
    }


@pytest.fixture()
def daily_report_kwargs(pipeline_run_id: uuid.UUID) -> dict:  # type: ignore[type-arg]
    """Minimal valid kwargs for a DailyReport."""
    return {
        "coverage_date": date.today(),
        "pipeline_run_id": pipeline_run_id,
    }


@pytest.fixture()
def report_section_kwargs(report_id: uuid.UUID) -> dict:  # type: ignore[type-arg]
    """Minimal valid kwargs for a ReportSection."""
    return {
        "report_id": report_id,
        "title": "US Equities",
        "order": 2,
    }
