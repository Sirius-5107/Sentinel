"""Phase 2 milestone tests for config loading, RSS collection, and persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
import feedparser
from pydantic import HttpUrl
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sentinel.collector.rss import RSSCollector
from sentinel.config import load_sources
from sentinel.db.models import Base
from sentinel.db.repository import ArticleRepository, DuplicateArticleError, SourceRepository
from sentinel.services.ingestion import IngestionService
from sentinel_core.enums import AssetClass, MarketRegion, SourceStatus, SourceType
from sentinel_core.models.article import Article
from sentinel_core.models.pipeline_run import PipelineRun
from sentinel_core.models.source import Source

TEST_RSS_XML = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\">
  <channel>
    <title>Example Market News</title>
    <link>https://example.com/</link>
    <description>Example feed</description>
    <item>
      <title>Fed holds rates steady</title>
      <link>https://example.com/articles/fed-rates</link>
      <guid>fed-rates</guid>
      <pubDate>Mon, 19 Aug 2026 10:00:00 +0000</pubDate>
      <description>Rates remain steady as inflation cools.</description>
    </item>
    <item>
      <title>Bank of England warns on inflation</title>
      <link>https://example.com/articles/boe-inflation</link>
      <guid>boe-inflation</guid>
      <pubDate>Mon, 19 Aug 2026 11:00:00 +0000</pubDate>
      <description>Inflation remains elevated.</description>
    </item>
  </channel>
</rss>
"""


def _build_source(url: str = "https://example.com/rss.xml") -> Source:
    return Source(
        name="Example Feed",
        url=HttpUrl(url),
        source_type=SourceType.RSS,
        status=SourceStatus.ACTIVE,
        region=MarketRegion.GLOBAL,
        asset_class=AssetClass.MACRO,
        language="en",
        weight=1.0,
        fetch_interval_minutes=60,
    )


def test_load_sources_from_yaml() -> None:
    sources = load_sources(Path("configs/sources.yaml"))
    assert sources
    assert all(source.source_type == SourceType.RSS for source in sources)
    assert all(source.status == SourceStatus.ACTIVE for source in sources)


@pytest.mark.asyncio
async def test_rss_collector_yields_valid_article_objects() -> None:
    collector = RSSCollector(parser=lambda _: feedparser.parse(TEST_RSS_XML))
    source = _build_source()
    articles: list[Article] = []
    collected = await collector.collect(source, PipelineRun(trigger="manual"))
    async for article in collected:
        articles.append(article)

    assert len(articles) == 2
    assert all(article.source_id == source.id for article in articles)
    assert all(article.status == "ingested" for article in articles)
    assert all(len(article.content_hash) == 64 for article in articles)


@pytest.mark.asyncio
async def test_rss_collector_skips_invalid_entries() -> None:
    invalid_rss = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <rss version=\"2.0\"><channel><title>Bad Feed</title>
    <item><description>No title or link</description></item>
    <item><title>Valid title</title><link>https://example.com/valid</link></item>
    </channel></rss>"""
    collector = RSSCollector(parser=lambda _: feedparser.parse(invalid_rss))
    source = _build_source()
    articles: list[Article] = []
    collected = await collector.collect(source, PipelineRun(trigger="manual"))
    async for article in collected:
        articles.append(article)
    assert len(articles) == 1
    assert articles[0].title == "Valid title"


def test_repository_rejects_duplicate_url_and_hash() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    repo = ArticleRepository(lambda: session_local())
    source = _build_source()
    source_repo = SourceRepository(lambda: session_local())
    source_repo.save_source(source)

    first = Article(
        source_id=source.id,
        title="Original article",
        url=HttpUrl("https://example.com/original"),
        content="Body text",
        content_hash="a" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    repo.save_article(first)

    duplicate_url = Article(
        source_id=source.id,
        title="Different title",
        url=HttpUrl("https://example.com/original"),
        content="Body text 2",
        content_hash="b" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    with pytest.raises(DuplicateArticleError):
        repo.save_article(duplicate_url)

    same_hash = Article(
        source_id=source.id,
        title="Different path same hash",
        url=HttpUrl("https://example.com/duplicate-hash"),
        content="Body text 3",
        content_hash="a" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    with pytest.raises(DuplicateArticleError):
        repo.save_article(same_hash)
    engine.dispose()


def test_source_and_article_repository_persistence() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    source_repo = SourceRepository(lambda: session_local())
    article_repo = ArticleRepository(lambda: session_local())

    source = _build_source()
    saved_source = source_repo.save_source(source)
    assert saved_source.name == source.name

    article = Article(
        source_id=saved_source.id,
        title="Fed policy update",
        url=HttpUrl("https://example.com/fed-policy"),
        content="A market update from the central bank.",
        content_hash="c" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    saved_article = article_repo.save_article(article)
    assert saved_article.id is not None
    assert article_repo.get_by_url(str(saved_article.url)) is not None
    engine.dispose()


def test_alembic_initial_schema_creates_tables() -> None:
    db_path = Path(".tmp_alembic_test.db")
    if db_path.exists():
        db_path.unlink()
    db_url = f"sqlite:///{db_path.resolve().as_posix()}"
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_engine(db_url, future=True)
    with Session(engine) as session:
        tables = session.connection().dialect.get_table_names(session.connection())
    assert {"sources", "articles"}.issubset(set(tables))
    engine.dispose()
    db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_ingestion_service_persists_articles_from_rss_feed() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    source_repo = SourceRepository(lambda: session_local())
    article_repo = ArticleRepository(lambda: session_local())
    collector = RSSCollector(parser=lambda _: feedparser.parse(TEST_RSS_XML))
    service = IngestionService(source_repo, article_repo, collector)

    source = _build_source()
    saved = await service.ingest_source(source)

    assert len(saved) == 2
    rows = source_repo.get_by_name(source.name)
    assert rows is not None
    assert article_repo.get_by_url("https://example.com/articles/fed-rates") is not None
    engine.dispose()
