"""Base collector definitions for Phase 2 collection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from sentinel_core.interfaces.protocols import CollectorProtocol
from sentinel_core.models.article import Article
from sentinel_core.models.pipeline_run import PipelineRun
from sentinel_core.models.source import Source


class BaseCollector(CollectorProtocol, ABC):
    """Shared base class for application-layer collectors."""

    @abstractmethod
    async def collect(
        self,
        source: Source,
        run: PipelineRun,
    ) -> AsyncIterator[Article]:
        """Yield ingested Article objects from a source."""
        raise NotImplementedError
