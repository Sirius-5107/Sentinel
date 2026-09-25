"""Protocol definitions for Sentinel pipeline stage contracts.

These protocols define the interface that application-layer implementations
must satisfy. They are structural (typing.Protocol), so no explicit
inheritance is required — any class that implements the required methods
is a valid implementation.

Implementation phases
---------------------
CollectorProtocol  — Phase 2 (sentinel/collector/)
ProcessorProtocol  — Phase 3 (sentinel/processing/)
PublisherProtocol  — Phase 7 (sentinel/publish/)
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Protocol, runtime_checkable

from sentinel_core.models import Article, DailyReport, PipelineRun, Source, Task


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Minimal protocol for a text-generation provider used by the processing stage."""

    async def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> str:
        """Return a model-generated completion for the supplied prompt."""
        ...  # pragma: no cover


@runtime_checkable
class EmbeddingProviderProtocol(Protocol):
    """Minimal protocol for a text embedding provider used for deduplication."""

    async def embed(self, text: str) -> Sequence[float]:
        """Return an embedding vector for the supplied text."""
        ...  # pragma: no cover


@runtime_checkable
class CollectorProtocol(Protocol):
    """Contract for all content collectors.

    A Collector fetches raw content from a configured Source and yields
    Article objects in INGESTED status. The collector is responsible for:

    - Respecting the Source's fetch_interval_minutes
    - Setting article.fetched_at to the current UTC time
    - Computing article.content_hash from (title + url)
    - Yielding only Article objects — no persistence

    Persistence (writing Articles to the database) is the responsibility
    of the application layer that calls the collector, not the collector itself.

    Example implementation (Phase 2)::

        class RSSCollector:
            async def collect(
                self, source: Source, run: PipelineRun
            ) -> AsyncIterator[Article]:
                ...
    """

    async def collect(
        self,
        source: Source,
        run: PipelineRun,
    ) -> AsyncIterator[Article]:
        """Fetch content from source and yield Article objects.

        Args:
            source: The Source to collect from. Must have status=ACTIVE.
            run: The PipelineRun this collection belongs to.

        Yields:
            Article objects with status=INGESTED. Not yet persisted.

        Raises:
            CollectionError: If the source cannot be reached or returns
                an unexpected response.

        """
        ...  # pragma: no cover


@runtime_checkable
class ProcessorProtocol(Protocol):
    """Contract for all article processors.

    A Processor takes an Article in INGESTED or PROCESSING status,
    classifies it, scores it, and returns an enriched Article in
    PROCESSED status. The processor may also extract entity references.

    Processors must be idempotent: processing the same Article twice
    must produce the same result.

    Example implementation (Phase 3)::

        class ArticleClassifier:
            async def process(
                self, article: Article, task: Task
            ) -> Article:
                ...
    """

    async def process(
        self,
        article: Article,
        task: Task,
    ) -> Article:
        """Classify and score an Article.

        Args:
            article: The Article to process. Must have status=INGESTED
                or status=PROCESSING.
            task: The Task this processing step belongs to.

        Returns:
            A new Article instance with status=PROCESSED and all derived
            fields populated (asset_class, region, sector, sentiment,
            sentiment_confidence, importance_score, importance_confidence).

        Raises:
            ProcessingError: If classification or scoring fails.

        """
        ...  # pragma: no cover


@runtime_checkable
class PublisherProtocol(Protocol):
    """Contract for all report publishers.

    A Publisher takes a DailyReport in APPROVED status and distributes
    it to a configured channel (e.g. Notion). Returns the report with
    status=PUBLISHED and any channel-specific identifiers set.

    Publishers must be idempotent: publishing the same report twice
    must not create duplicate output.

    Example implementation (Phase 7)::

        class NotionPublisher:
            async def publish(
                self, report: DailyReport, task: Task
            ) -> DailyReport:
                ...
    """

    async def publish(
        self,
        report: DailyReport,
        task: Task,
    ) -> DailyReport:
        """Publish a DailyReport to a configured channel.

        Args:
            report: The DailyReport to publish. Must have status=APPROVED.
            task: The Task this publishing step belongs to.

        Returns:
            A new DailyReport instance with status=PUBLISHED and any
            channel-specific identifiers populated (e.g. notion_page_id).

        Raises:
            PublishingError: If the channel rejects the report or is
                unavailable.

        """
        ...  # pragma: no cover
