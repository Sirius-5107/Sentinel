"""Unit tests for sentinel_core.interfaces."""

from __future__ import annotations

import pytest

from sentinel_core.interfaces import (
    CollectorProtocol,
    ProcessorProtocol,
    PublisherProtocol,
)


@pytest.mark.unit
class TestProtocolsAreRuntime:
    """All protocols are @runtime_checkable."""

    def test_collector_protocol_is_runtime_checkable(self) -> None:
        """isinstance() checks must work for CollectorProtocol."""

        # A class without the method is not an instance
        class NotACollector:
            pass

        assert not isinstance(NotACollector(), CollectorProtocol)

    def test_processor_protocol_is_runtime_checkable(self) -> None:
        class NotAProcessor:
            pass

        assert not isinstance(NotAProcessor(), ProcessorProtocol)

    def test_publisher_protocol_is_runtime_checkable(self) -> None:
        class NotAPublisher:
            pass

        assert not isinstance(NotAPublisher(), PublisherProtocol)


@pytest.mark.unit
class TestProtocolMethodSignatures:
    """Protocols expose the expected method names."""

    def test_collector_has_collect_method(self) -> None:
        assert hasattr(CollectorProtocol, "collect")

    def test_processor_has_process_method(self) -> None:
        assert hasattr(ProcessorProtocol, "process")

    def test_publisher_has_publish_method(self) -> None:
        assert hasattr(PublisherProtocol, "publish")


@pytest.mark.unit
class TestProtocolConformance:
    """A class implementing the correct method satisfies the protocol."""

    def test_collector_conformance(self) -> None:
        """Any class with an async collect method satisfies CollectorProtocol."""
        from collections.abc import AsyncIterator

        from sentinel_core.models import Article, PipelineRun, Source

        class ConcreteCollector:
            async def collect(self, source: Source, run: PipelineRun) -> AsyncIterator[Article]:
                return  # type: ignore[return-value]

        assert isinstance(ConcreteCollector(), CollectorProtocol)

    def test_processor_conformance(self) -> None:
        from sentinel_core.models import Article, Task

        class ConcreteProcessor:
            async def process(self, article: Article, task: Task) -> Article:
                return article

        assert isinstance(ConcreteProcessor(), ProcessorProtocol)

    def test_publisher_conformance(self) -> None:
        from sentinel_core.models import DailyReport, Task

        class ConcretePublisher:
            async def publish(self, report: DailyReport, task: Task) -> DailyReport:
                return report

        assert isinstance(ConcretePublisher(), PublisherProtocol)
