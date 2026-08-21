"""Orchestration layer for loading configured sources and running collectors.

Responsibilities:
- load configured sources
- validate and persist source records via SourceRepository
- select collector per source via factory
- collect articles and persist via ArticleRepository
- return structured results per source (success/failure, counts)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List

from sentinel.config.loaders import load_sources
from sentinel.collector.factory import get_collector_for_source
from sentinel.db.repository import ArticleRepository, DuplicateArticleError, SourceRepository
from sentinel_core.exceptions.base import CollectionError
from sentinel_core.models.pipeline_run import PipelineRun
from sentinel_core.models.source import Source
from sentinel_core.models.article import Article
from sentinel_core.enums import SourceStatus


@dataclass
class SourceResult:
    source_name: str
    success: bool
    error: str | None
    collected: int
    persisted: int


@dataclass
class OrchestrationResult:
    total_sources: int
    source_results: List[SourceResult]
    total_collected: int
    total_persisted: int


class CollectionOrchestrator:
    """High-level orchestration for a single collection run.

    Keeps orchestration separate from collectors and repositories.
    """

    def __init__(
        self,
        source_repository: SourceRepository,
        article_repository: ArticleRepository,
    ) -> None:
        self._source_repository = source_repository
        self._article_repository = article_repository

    def run_once(self, path: str | None = None) -> OrchestrationResult:
        """Load sources, run collectors, persist articles, and return a summary.

        This is synchronous at the application-layer surface: collectors provide
        async iterators; those are driven synchronously using their returned
        async iterator objects where the collectors themselves implement the
        async generator protocol. For simplicity and to keep the API small we
        leverage the collectors' coroutine-returning pattern already used in
        the codebase (collect returns an AsyncIterator when awaited).
        """
        sources = load_sources(path or "configs/sources.yaml")
        total_collected = 0
        total_persisted = 0
        results: List[SourceResult] = []

        for src in sources:
            # Skip inactive sources early (do not persist or create collectors)
            if src.status != SourceStatus.ACTIVE:
                # intentionally skip paused/inactive sources
                continue

            # Persist or reuse existing Source record
            try:
                persisted = self._source_repository.save_source(src)
            except Exception as exc:  # keep error surface small; record and continue
                results.append(
                    SourceResult(
                        source_name=src.name,
                        success=False,
                        error=f"Failed to persist source: {exc}",
                        collected=0,
                        persisted=0,
                    )
                )
                continue

            # Select collector
            try:
                collector = get_collector_for_source(persisted)
            except Exception as exc:
                results.append(
                    SourceResult(
                        source_name=src.name,
                        success=False,
                        error=str(exc),
                        collected=0,
                        persisted=0,
                    )
                )
                continue

            # Run collection and persist articles
            collected_count = 0
            persisted_count = 0
            try:
                run = PipelineRun(trigger="manual")
                import asyncio

                async def _drive_and_persist():
                    nonlocal collected_count, persisted_count
                    # await the collector coroutine to obtain an async iterator
                    async_iter = await collector.collect(persisted, run)
                    async for article in async_iter:
                        collected_count += 1
                        try:
                            self._article_repository.save_article(article)
                        except DuplicateArticleError:
                            continue
                        persisted_count += 1

                asyncio.run(_drive_and_persist())

                results.append(
                    SourceResult(
                        source_name=src.name,
                        success=True,
                        error=None,
                        collected=collected_count,
                        persisted=persisted_count,
                    )
                )
            except CollectionError as coll_err:
                results.append(
                    SourceResult(
                        source_name=src.name,
                        success=False,
                        error=f"Collection error: {coll_err}",
                        collected=collected_count,
                        persisted=persisted_count,
                    )
                )
            except Exception as exc:
                results.append(
                    SourceResult(
                        source_name=src.name,
                        success=False,
                        error=f"Unexpected error: {exc}",
                        collected=collected_count,
                        persisted=persisted_count,
                    )
                )
            # Always include the counts (even if the source failed part-way)
            total_collected += collected_count
            total_persisted += persisted_count

        return OrchestrationResult(
            total_sources=len(sources),
            source_results=results,
            total_collected=total_collected,
            total_persisted=total_persisted,
        )


__all__ = ["CollectionOrchestrator", "OrchestrationResult", "SourceResult"]
