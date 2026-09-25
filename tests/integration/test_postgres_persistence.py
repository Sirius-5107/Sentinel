"""PostgreSQL integration tests for the Phase 2 persistence baseline."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
import os

from alembic import command
from alembic.config import Config
import feedparser
from pydantic import HttpUrl
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from sentinel.collector.rss import RSSCollector
from sentinel.db.models import ArticleORM, SourceORM
from sentinel.db.repository import ArticleRepository, DuplicateArticleError, SourceRepository
from sentinel.services.ingestion import IngestionService
from sentinel_core.enums import AssetClass, MarketRegion, SourceStatus, SourceType
from sentinel_core.models.article import Article
from sentinel_core.models.source import Source

pytestmark = pytest.mark.integration


def _require_postgres_url() -> str:
    database_url = os.getenv("SENTINEL_DB_URL")
    if not database_url:
        pytest.skip(
            "Skipping PostgreSQL integration tests: set SENTINEL_DB_URL to "
            "postgresql+psycopg://... before running the integration suite."
        )
    if not database_url.startswith("postgresql+psycopg://"):
        pytest.fail(
            "PostgreSQL integration tests require SENTINEL_DB_URL to use the "
            "canonical format: postgresql+psycopg://..."
        )
    return database_url


def _admin_database_url(database_url: str) -> str:
    return database_url.rsplit("/", 1)[0] + "/postgres"


def _db_for_test(database_url: str, database_name: str) -> str:
    prefix = database_url.rsplit("/", 1)[0]
    return f"{prefix}/{database_name}"


def _build_source(name: str = "Postgres Feed") -> Source:
    return Source(
        name=name,
        url=HttpUrl("https://example.com/rss.xml"),
        source_type=SourceType.RSS,
        status=SourceStatus.ACTIVE,
        region=MarketRegion.GLOBAL,
        asset_class=AssetClass.MACRO,
        language="en",
        weight=1.0,
        fetch_interval_minutes=60,
    )


def _reset_test_database(database_url: str, database_name: str) -> str:
    admin_url = _admin_database_url(database_url)
    admin_engine = create_engine(admin_url, future=True)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {database_name}"))
        conn.execute(text(f"CREATE DATABASE {database_name}"))
    admin_engine.dispose()
    return _db_for_test(database_url, database_name)


@pytest.fixture
def postgres_engine() -> Iterator[Engine]:
    database_url = _require_postgres_url()
    target_db = "sentinel_test_postgres"
    target_url = _reset_test_database(database_url, target_db)
    engine = create_engine(target_url, future=True)
    yield engine
    engine.dispose()


def test_postgres_alembic_upgrade_from_clean_database(postgres_engine: Engine) -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", str(postgres_engine.url))
    command.upgrade(cfg, "head")

    with Session(postgres_engine) as session:
        tables = session.connection().dialect.get_table_names(session.connection())
    assert {"sources", "articles"}.issubset(set(tables))


def test_postgres_source_and_article_persistence(postgres_engine: Engine) -> None:
    session_local = sessionmaker(
        bind=postgres_engine, autoflush=False, expire_on_commit=False, future=True
    )
    source_repo = SourceRepository(lambda: session_local())
    article_repo = ArticleRepository(lambda: session_local())

    source = _build_source("Postgres Source")
    saved_source = source_repo.save_source(source)
    assert saved_source.name == source.name

    article = Article(
        source_id=saved_source.id,
        title="Postgres article",
        url=HttpUrl("https://example.com/postgres-article"),
        content="Body text",
        content_hash="d" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    saved_article = article_repo.save_article(article)
    assert saved_article.id is not None
    assert article_repo.get_by_url(str(saved_article.url)) is not None

    with Session(postgres_engine) as session:
        source_row = session.get(SourceORM, str(saved_source.id))
        article_row = session.get(ArticleORM, str(saved_article.id))
        assert source_row is not None
        assert article_row is not None
        assert article_row.source_id == str(saved_source.id)


def test_postgres_duplicate_url_and_hash_are_rejected(postgres_engine: Engine) -> None:
    session_local = sessionmaker(
        bind=postgres_engine, autoflush=False, expire_on_commit=False, future=True
    )
    source_repo = SourceRepository(lambda: session_local())
    article_repo = ArticleRepository(lambda: session_local())

    source = _build_source("Postgres Duplicate Source")
    saved_source = source_repo.save_source(source)

    first = Article(
        source_id=saved_source.id,
        title="Original",
        url=HttpUrl("https://example.com/duplicate"),
        content="Body text",
        content_hash="e" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    article_repo.save_article(first)

    duplicate_url = Article(
        source_id=saved_source.id,
        title="Different title",
        url=HttpUrl("https://example.com/duplicate"),
        content="Body text 2",
        content_hash="f" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    with pytest.raises(DuplicateArticleError):
        article_repo.save_article(duplicate_url)

    same_hash = Article(
        source_id=saved_source.id,
        title="Same hash",
        url=HttpUrl("https://example.com/another"),
        content="Body text 3",
        content_hash="e" * 64,
        fetched_at=datetime.now(tz=UTC),
    )
    with pytest.raises(DuplicateArticleError):
        article_repo.save_article(same_hash)


@pytest.mark.asyncio
async def test_postgres_rss_ingestion_to_postgres(postgres_engine: Engine) -> None:
    session_local = sessionmaker(
        bind=postgres_engine, autoflush=False, expire_on_commit=False, future=True
    )
    source_repo = SourceRepository(lambda: session_local())
    article_repo = ArticleRepository(lambda: session_local())
    collector = RSSCollector(
        parser=lambda _: feedparser.parse(
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
            <rss version=\"2.0\"><channel><title>Example</title><link>https://example.com</link>
            <item><title>Fed holds rates steady</title><link>https://example.com/articles/fed-rates</link>
            <guid>fed-rates</guid><pubDate>Mon, 19 Aug 2026 10:00:00 +0000</pubDate>
            <description>Rates remain steady.</description></item>
            </channel></rss>"""
        )
    )
    service = IngestionService(source_repo, article_repo, collector)

    source = _build_source("RSS Postgres Source")
    saved = await service.ingest_source(source)
    assert len(saved) == 1

    with Session(postgres_engine) as session:
        count = session.execute(text("SELECT COUNT(*) FROM articles")).scalar_one()
        assert count == 1
