"""Minimal ingestion orchestration for the Phase 2 vertical slice."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sentinel.collector.rss import RSSCollector
from sentinel.db.repository import ArticleRepository, DuplicateArticleError, SourceRepository
from sentinel_core.models.article import Article
from sentinel_core.models.pipeline_run import PipelineRun
from sentinel_core.models.source import Source


class IngestionService:
    """Bridge configured sources, collectors, and the application repository."""

    def __init__(
        self,
        source_repository: SourceRepository,
        article_repository: ArticleRepository,
        collector: RSSCollector | None = None,
    ) -> None:
        """Create an ingestion service bound to repositories and a collector."""
        self._source_repository = source_repository
        self._article_repository = article_repository
        self._collector = collector or RSSCollector()

    async def ingest_source(self, source: Source) -> list[Article]:
        """Persist a source's collected articles and return the saved article list."""
        persisted_source = self._source_repository.save_source(source)
        run = PipelineRun(trigger="manual")
        saved_articles: list[Article] = []
        articles = await self._collector.collect(persisted_source, run)
        async for article in articles:
            try:
                saved = self._article_repository.save_article(article)
            except DuplicateArticleError:
                continue
            saved_articles.append(saved)
        return saved_articles

    async def scan(self, source: Source) -> AsyncIterator[Article]:
        """Yield each persisted article for a source while skipping duplicates."""
        persisted_source = self._source_repository.save_source(source)
        run = PipelineRun(trigger="manual")
        articles = await self._collector.collect(persisted_source, run)
        async for article in articles:
            try:
                yield self._article_repository.save_article(article)
            except DuplicateArticleError:
                continue


__all__ = ["IngestionService"]
