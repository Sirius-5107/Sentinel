"""Unit tests for the Phase 4 intelligence pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import uuid

from pydantic import HttpUrl, ValidationError
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sentinel.db.models import Base, DailyReportORM, MarketEventORM, ReportSectionORM
from sentinel.db.repository import (
    ArticleRepository,
    DailyBriefRepository,
    MarketEventRepository,
    ReportSectionRepository,
    SourceRepository,
)
from sentinel.intelligence.analyst import Analyst
from sentinel.intelligence.daily_brief import DailyBriefAssembler
from sentinel.intelligence.synthesiser import EventSynthesiser, MarketEventCandidate
from sentinel_core.enums import (
    ArticleStatus,
    AssetClass,
    EventSeverity,
    MarketRegion,
    ReportStatus,
    ReportType,
    Sector,
    Sentiment,
    SourceStatus,
    SourceType,
)
from sentinel_core.models import Article, DailyReport, MarketEvent, ReportSection, Source
from sentinel_core.types import Url


def _make_article(
    *,
    title: str,
    summary: str,
    content: str,
    region: MarketRegion,
    asset_class: AssetClass,
    sector: Sector,
) -> Article:
    return Article(
        source_id=uuid.uuid4(),
        title=title,
        url=Url(f"https://example.com/{title.lower().replace(' ', '-')}-{uuid.uuid4()}"),
        content=content,
        summary=summary,
        published_at=datetime.now(tz=UTC),
        fetched_at=datetime.now(tz=UTC),
        language="en",
        status=ArticleStatus.PROCESSED,
        asset_class=asset_class,
        region=region,
        sector=sector,
        content_hash=hashlib.sha256(f"{title}{summary}".encode()).hexdigest(),
    )


class _MalformedLLMProvider:
    async def complete(
        self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.0
    ) -> str:
        del prompt, max_tokens, temperature
        return "{not-json"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_synthesiser_creates_deterministic_market_event() -> None:
    articles = [
        _make_article(
            title="Fed holds rates as inflation remains sticky",
            summary=(
                "The Federal Reserve kept borrowing costs steady after inflation stayed elevated."
            ),
            content=(
                "The Federal Reserve kept borrowing costs steady as inflation "
                "remained elevated and officials signaled that policy would remain "
                "restrictive for longer than markets had expected."
            ),
            region=MarketRegion.US,
            asset_class=AssetClass.MACRO,
            sector=Sector.FINANCIALS,
        ),
        _make_article(
            title="Treasury yields rise after central bank signal",
            summary=(
                "Treasury yields moved higher after the central bank signaled a "
                "slower pace of rate cuts."
            ),
            content=(
                "Treasury yields moved higher as bond markets reacted to the central "
                "bank signal that inflation remained sticky and rate cuts were "
                "unlikely to arrive quickly."
            ),
            region=MarketRegion.US,
            asset_class=AssetClass.MACRO,
            sector=Sector.FINANCIALS,
        ),
    ]

    synthesiser = EventSynthesiser()
    events = await synthesiser.synthesise(articles)

    assert len(events) == 1
    assert events[0].asset_class == AssetClass.MACRO
    assert events[0].region == MarketRegion.US
    assert len(events[0].summary) >= 100
    assert list(synthesiser.provenance) == [events[0].id]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_synthesiser_requires_provenance() -> None:
    with pytest.raises(ValidationError):
        MarketEventCandidate.model_validate(
            {
                "title": "Fed confirms steady policy path",
                "summary": (
                    "The Federal Reserve kept rates unchanged and policymakers "
                    "signaled that inflation remains elevated, supporting a "
                    "higher-for-longer stance that matters for rates and growth "
                    "expectations across the US economy."
                ),
                "asset_class": "macro",
                "region": "us",
                "severity": "high",
                "sentiment": "neutral",
                "sentiment_confidence": 0.75,
                "importance_score": 7.5,
                "importance_confidence": 0.8,
                "occurred_at": datetime.now(tz=UTC),
                "source_article_ids": [],
            }
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_synthesiser_falls_back_on_malformed_provider_output() -> None:
    article = _make_article(
        title="Fed rate decision shapes growth outlook",
        summary="The Federal Reserve kept rates steady while describing inflation as sticky.",
        content=(
            "Officials said inflation remained sticky after the latest rate "
            "decision, keeping pressure on growth expectations in the US economy."
        ),
        region=MarketRegion.US,
        asset_class=AssetClass.MACRO,
        sector=Sector.FINANCIALS,
    )

    events = await EventSynthesiser(provider=_MalformedLLMProvider()).synthesise([article])

    assert len(events) == 1
    assert events[0].summary
    assert events[0].asset_class == AssetClass.MACRO


@pytest.mark.unit
@pytest.mark.asyncio
async def test_analyst_keeps_analysis_grounded_in_evidence() -> None:
    article = _make_article(
        title="AI infrastructure spending rises after chip orders surge",
        summary="Chip and infrastructure spending accelerated after a major order book update.",
        content=(
            "Chip makers reported a new order surge and AI infrastructure "
            "spending accelerated, raising expectations for semiconductor demand."
        ),
        region=MarketRegion.US,
        asset_class=AssetClass.EQUITY,
        sector=Sector.TECHNOLOGY,
    )
    event = MarketEvent(
        title="AI infrastructure spending accelerates",
        summary=(
            "The acceleration in AI infrastructure spending matters because it "
            "signals stronger demand for chips and data-center equipment across US "
            "technology markets, with implications for capex expectations and sector "
            "earnings."
        ),
        asset_class=AssetClass.EQUITY,
        region=MarketRegion.US,
        sector=Sector.TECHNOLOGY,
        severity=EventSeverity.HIGH,
        sentiment=Sentiment.BULLISH,
        sentiment_confidence=0.86,
        importance_score=8.2,
        importance_confidence=0.9,
        occurred_at=datetime.now(tz=UTC),
    )

    result = await Analyst().analyse(event, [article])

    assert result.market_event_id == event.id
    assert result.supporting_article_ids == (article.id,)
    assert "because" in result.text.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_daily_brief_is_deterministic_and_tracks_provenance() -> None:
    article = _make_article(
        title="India growth outlook firm as manufacturing expands",
        summary="Manufacturing output rose, supporting a firmer India growth outlook.",
        content=(
            "Manufacturing output expanded in India, supporting a more "
            "constructive outlook for growth and domestic consumption."
        ),
        region=MarketRegion.INDIA,
        asset_class=AssetClass.EQUITY,
        sector=Sector.INDUSTRIALS,
    )
    other = _make_article(
        title="US inflation cools as policy remains restrictive",
        summary="US inflation eased while policy remained restrictive.",
        content=(
            "US inflation eased while the policy backdrop remained restrictive, "
            "increasing expectations for slower growth and more cautious risk-taking."
        ),
        region=MarketRegion.US,
        asset_class=AssetClass.MACRO,
        sector=Sector.FINANCIALS,
    )
    event_one = MarketEvent(
        title="India manufacturing improves",
        summary=(
            "India manufacturing improvement matters because it supports output and "
            "domestic demand expectations across the broader equity complex, "
            "reinforcing a constructive growth narrative for the region."
        ),
        asset_class=AssetClass.EQUITY,
        region=MarketRegion.INDIA,
        sector=Sector.INDUSTRIALS,
        severity=EventSeverity.MEDIUM,
        sentiment=Sentiment.BULLISH,
        sentiment_confidence=0.8,
        importance_score=7.0,
        importance_confidence=0.9,
        occurred_at=datetime.now(tz=UTC),
    )
    event_two = MarketEvent(
        title="US inflation cools",
        summary=(
            "A cooling inflation print matters to markets because it reduces "
            "near-term pressure on the policy path and alters expectations for "
            "growth and risk-taking across the US macro backdrop."
        ),
        asset_class=AssetClass.MACRO,
        region=MarketRegion.US,
        sector=Sector.FINANCIALS,
        severity=EventSeverity.HIGH,
        sentiment=Sentiment.BULLISH,
        sentiment_confidence=0.8,
        importance_score=8.5,
        importance_confidence=0.9,
        occurred_at=datetime.now(tz=UTC),
    )

    brief = DailyBriefAssembler.assemble(
        [event_two, event_one],
        event_provenance={event_one.id: [article.id], event_two.id: [other.id]},
    )

    assert brief.report.event_count == 2
    assert brief.report.report_type == ReportType.DAILY_BRIEF
    assert len(brief.sections) == 2
    assert brief.event_article_ids[event_one.id] == (article.id,)
    assert brief.event_article_ids[event_two.id] == (other.id,)


def test_market_event_repository_persists_article_provenance_round_trip() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    source_repo = SourceRepository(lambda: session_local())
    article_repo = ArticleRepository(lambda: session_local())
    market_repo = MarketEventRepository(lambda: session_local())
    section_repo = ReportSectionRepository(lambda: session_local())
    brief_repo = DailyBriefRepository(lambda: session_local())

    source = Source(
        name="Fed Watch",
        url=HttpUrl("https://example.com/fed-watch"),
        source_type=SourceType.RSS,
        status=SourceStatus.ACTIVE,
        region=MarketRegion.US,
        asset_class=AssetClass.MACRO,
        language="en",
        weight=1.0,
        fetch_interval_minutes=60,
    )
    saved_source = source_repo.save_source(source)

    article_one = Article(
        source_id=saved_source.id,
        title="Fed holds rates steady",
        url=HttpUrl("https://example.com/fed-rates"),
        content="The central bank kept rates steady as inflation remained elevated.",
        content_hash="a" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    article_two = Article(
        source_id=saved_source.id,
        title="Treasury yields climb after rate signal",
        url=HttpUrl("https://example.com/treasury-yields"),
        content="Bond yields rose after policymakers signaled a higher-for-longer path.",
        content_hash="b" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    saved_article_one = article_repo.save_article(article_one)
    saved_article_two = article_repo.save_article(article_two)

    event = MarketEvent(
        title="Fed policy path remains restrictive",
        summary=(
            "The Federal Reserve signaled that inflation remains elevated and rates are "
            "likely to stay higher for longer, a development that matters for growth "
            "expectations, bond yields, and the overall macro backdrop across US "
            "markets."
        ),
        asset_class=AssetClass.MACRO,
        region=MarketRegion.US,
        sector=Sector.FINANCIALS,
        severity=EventSeverity.HIGH,
        sentiment=Sentiment.NEUTRAL,
        sentiment_confidence=0.8,
        importance_score=8.1,
        importance_confidence=0.85,
        occurred_at=datetime.now(tz=UTC),
    )
    saved_event = market_repo.save_market_event(
        event,
        source_article_ids=[saved_article_one.id, saved_article_two.id],
    )

    with session_local() as session:
        event_row = session.get(MarketEventORM, str(saved_event.id))
        assert event_row is not None
        event_article_ids = {uuid.UUID(article_row.id) for article_row in event_row.articles}
        assert event_article_ids == {saved_article_one.id, saved_article_two.id}

    report = DailyReport(
        coverage_date=datetime.now(tz=UTC).date(),
        report_type=ReportType.DAILY_BRIEF,
        status=ReportStatus.DRAFT,
        title="Daily Brief",
        executive_summary="A brief summary for the day.",
        article_count=2,
        event_count=1,
    )
    section = ReportSection(
        report_id=report.id,
        title="Macro",
        order=0,
        content="The most important development is the restrictive Fed policy path.",
        asset_class=AssetClass.MACRO,
        region=MarketRegion.US,
        event_count=1,
    )
    saved_section = section_repo.save_report_section(
        section,
        market_event_ids=[saved_event.id],
    )

    with session_local() as session:
        section_row = session.get(ReportSectionORM, str(saved_section.id))
        assert section_row is not None
        section_event_ids = {uuid.UUID(event_row.id) for event_row in section_row.market_events}
        assert section_event_ids == {saved_event.id}

    brief = DailyBriefAssembler.assemble(
        [saved_event],
        coverage_date=report.coverage_date,
        event_provenance={saved_event.id: (saved_article_one.id, saved_article_two.id)},
    )
    persisted_report = brief_repo.save_daily_report(
        brief.report,
        sections=brief.sections,
        section_event_ids=brief.section_event_ids,
        event_article_ids=brief.event_article_ids,
    )

    with session_local() as session:
        daily_row = session.get(DailyReportORM, str(persisted_report.id))
        assert daily_row is not None
        assert len(daily_row.sections) == 1
        reloaded_section = daily_row.sections[0]
        reloaded_event_ids = {
            uuid.UUID(event_row.id) for event_row in reloaded_section.market_events
        }
        assert reloaded_event_ids == {saved_event.id}
        reloaded_event = reloaded_section.market_events[0]
        reloaded_article_ids = {
            uuid.UUID(article_row.id) for article_row in reloaded_event.articles
        }
        assert reloaded_article_ids == {saved_article_one.id, saved_article_two.id}

    engine.dispose()


def test_market_event_repository_rejects_zero_supporting_articles() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    market_repo = MarketEventRepository(lambda: session_local())

    event = MarketEvent(
        title="Policy path remains restrictive",
        summary=(
            "The Federal Reserve signaled that inflation remains elevated and rates are "
            "likely to stay higher for longer, which matters to expectations for growth "
            "and bond yields across US markets."
        ),
        asset_class=AssetClass.MACRO,
        region=MarketRegion.US,
        sector=Sector.FINANCIALS,
        severity=EventSeverity.HIGH,
        sentiment=Sentiment.NEUTRAL,
        sentiment_confidence=0.8,
        importance_score=8.1,
        importance_confidence=0.85,
        occurred_at=datetime.now(tz=UTC),
    )

    with pytest.raises(ValueError, match="at least one supporting Article"):
        market_repo.save_market_event(event, source_article_ids=[])

    engine.dispose()
