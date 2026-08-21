"""Unit tests for the collection orchestration layer.

Tests are deterministic and do not perform network I/O. Repositories and
collectors are mocked to exercise orchestration logic and failure isolation.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sentinel.config.loaders import load_source_configs, load_sources
from sentinel.collector.factory import get_collector_for_source
from sentinel.services.collection import CollectionOrchestrator, OrchestrationResult
from sentinel_core.enums import SourceType, SourceStatus
from sentinel_core.models.source import Source
from sentinel_core.types import Url
from sentinel.db.repository import ArticleRepository, SourceRepository, DuplicateArticleError
from sentinel_core.models.article import Article
from datetime import UTC, datetime


from sentinel_core.enums import AssetClass, MarketRegion, ArticleStatus


def make_source(name: str, url: str, source_type: SourceType, enabled: bool = True) -> Source:
    return Source(
        name=name,
        url=Url(url),
        source_type=source_type,
        status=SourceStatus.ACTIVE if enabled else SourceStatus.PAUSED,
        region=MarketRegion.GLOBAL,
        asset_class=AssetClass.MACRO,
        language="en",
    )


class DummyCollector:
    def __init__(self, articles: list[Article] | None = None, raise_on_collect: Exception | None = None):
        self._articles = articles or []
        self._raise = raise_on_collect

    async def collect(self, source, run):
        if self._raise:
            raise self._raise

        async def _gen():
            for a in self._articles:
                yield a

        return _gen()


@pytest.mark.unit
def test_load_source_configs_and_load_sources(tmp_path, monkeypatch):
    # Ensure loaders return at least the default YAML entries
    configs = load_source_configs("configs/sources.yaml")
    assert isinstance(configs, list)
    sources = load_sources("configs/sources.yaml")
    assert isinstance(sources, list)
    # Each resolved source must be a Source instance
    for s in sources:
        assert isinstance(s, Source)


@pytest.mark.unit
def test_collector_factory_selection():
    rss = make_source("rss", "https://example.com/rss", SourceType.RSS)
    scrape = make_source("scrape", "https://example.com/page", SourceType.SCRAPE)
    assert "RSSCollector" in type(get_collector_for_source(rss)).__name__
    assert "StaticHTMLCollector" in type(get_collector_for_source(scrape)).__name__


@pytest.mark.unit
def test_orchestrator_success_and_failure(monkeypatch):
    # Two sources: one succeeds with 2 articles, one fails during collection
    s1 = make_source("S1", "https://s1.example", SourceType.RSS)
    s2 = make_source("S2", "https://s2.example", SourceType.SCRAPE)

    # Articles to return for s1
    a1 = Article(
        source_id=s1.id,
        title="A1",
        url=Url("https://s1.example/a1"),
        content="x",
        summary=None,
        published_at=None,
        fetched_at=datetime.now(tz=UTC),
        language="en",
        status=ArticleStatus.INGESTED,
        content_hash=__import__('hashlib').sha256(b'h1').hexdigest(),
    )
    a2 = Article(
        source_id=s1.id,
        title="A2",
        url=Url("https://s1.example/a2"),
        content="y",
        summary=None,
        published_at=None,
        fetched_at=datetime.now(tz=UTC),
        language="en",
        status=ArticleStatus.INGESTED,
        content_hash=__import__('hashlib').sha256(b'h2').hexdigest(),
    )

    # Mock load_sources (imported in the orchestrator module) to return s1 and s2
    import sentinel.services.collection as _svc
    monkeypatch.setattr(_svc, "load_sources", lambda path=None: [s1, s2])

    # Mock source repository to echo back the source
    src_repo = MagicMock(spec=SourceRepository)
    src_repo.save_source.side_effect = lambda s: s

    # Mock article repository: for s1 accept a1, for a2 raise DuplicateArticleError once
    art_repo = MagicMock(spec=ArticleRepository)

    def save_article_side(a):
        if a.content_hash == a1.content_hash:
            return a
        if a.content_hash == a2.content_hash:
            raise DuplicateArticleError("dup")
        return a

    art_repo.save_article.side_effect = save_article_side

    # Mock factory to return DummyCollectors
    from sentinel_core.exceptions.base import CollectionError
    # Patch the factory function used by the orchestrator module
    monkeypatch.setattr(
    _svc,
    "get_collector_for_source",
    lambda s: DummyCollector(articles=[a1, a2]) if s.name == "S1" else DummyCollector(raise_on_collect=CollectionError("fail")),
    )

    orchestrator = CollectionOrchestrator(src_repo, art_repo)
    result: OrchestrationResult = orchestrator.run_once()

    assert result.total_sources == 2
    # Find results by name
    res_map = {r.source_name: r for r in result.source_results}
    assert res_map["S1"].success is True
    assert res_map["S1"].collected == 2
    # one persisted (h1), one duplicate
    assert res_map["S1"].persisted == 1

    assert res_map["S2"].success is False
    assert "Collection error" in (res_map["S2"].error or "")


@pytest.mark.unit
def test_unsupported_source_type(monkeypatch):
    s = make_source("unsupported", "https://x", SourceType.API)
    import sentinel.services.collection as _svc
    monkeypatch.setattr(_svc, "load_sources", lambda path=None: [s])

    src_repo = MagicMock(spec=SourceRepository)
    src_repo.save_source.side_effect = lambda s: s
    art_repo = MagicMock(spec=ArticleRepository)

    orchestrator = CollectionOrchestrator(src_repo, art_repo)
    res = orchestrator.run_once()
    assert res.total_sources == 1
    assert res.source_results[0].success is False
    assert "Unsupported source type" in (res.source_results[0].error or "")


@pytest.mark.unit
def test_partial_collection_failure(monkeypatch):
    # Source S1 yields two articles then raises CollectionError during iteration
    s1 = make_source("S1", "https://s1.example", SourceType.SCRAPE)
    s2 = make_source("S2", "https://s2.example", SourceType.SCRAPE)

    a1 = Article(
        source_id=s1.id,
        title="P1",
        url=Url("https://s1.example/p1"),
        content="c1",
        summary=None,
        published_at=None,
        fetched_at=datetime.now(tz=UTC),
        language="en",
        status=ArticleStatus.INGESTED,
        content_hash=__import__('hashlib').sha256(b'p1').hexdigest(),
    )
    a2 = Article(
        source_id=s1.id,
        title="P2",
        url=Url("https://s1.example/p2"),
        content="c2",
        summary=None,
        published_at=None,
        fetched_at=datetime.now(tz=UTC),
        language="en",
        status=ArticleStatus.INGESTED,
        content_hash=__import__('hashlib').sha256(b'p2').hexdigest(),
    )
    b1 = Article(
        source_id=s2.id,
        title="B1",
        url=Url("https://s2.example/b1"),
        content="cb",
        summary=None,
        published_at=None,
        fetched_at=datetime.now(tz=UTC),
        language="en",
        status=ArticleStatus.INGESTED,
        content_hash=__import__('hashlib').sha256(b'b1').hexdigest(),
    )

    import sentinel.services.collection as _svc
    monkeypatch.setattr(_svc, "load_sources", lambda path=None: [s1, s2])

    src_repo = MagicMock(spec=SourceRepository)
    src_repo.save_source.side_effect = lambda s: s

    art_repo = MagicMock(spec=ArticleRepository)
    art_repo.save_article.side_effect = lambda a: a

    from sentinel_core.exceptions.base import CollectionError

    class PartialFailCollector:
        def __init__(self, articles_before_fail):
            self._articles = articles_before_fail

        async def collect(self, source, run):
            async def _gen():
                for x in self._articles:
                    yield x
                raise CollectionError("midstream-failure")

            return _gen()

    # s1 will partially fail after yielding a1,a2; s2 will succeed
    monkeypatch.setattr(
        _svc,
        "get_collector_for_source",
        lambda s: PartialFailCollector([a1, a2]) if s.name == "S1" else DummyCollector(articles=[b1]),
    )

    orchestrator = CollectionOrchestrator(src_repo, art_repo)
    res = orchestrator.run_once()

    assert res.total_sources == 2
    res_map = {r.source_name: r for r in res.source_results}

    # S1 should be marked failed with counts preserved
    assert res_map["S1"].success is False
    assert "Collection error" in (res_map["S1"].error or "") or "midstream-failure" in (res_map["S1"].error or "")
    assert res_map["S1"].collected == 2
    assert res_map["S1"].persisted == 2

    # S2 should succeed and its counts included in totals
    assert res_map["S2"].success is True
    assert res_map["S2"].collected == 1
    assert res_map["S2"].persisted == 1

    # Totals include partial counts from the failed source
    assert res.total_collected == 3
    assert res.total_persisted == 3


__all__ = [
    "test_load_source_configs_and_load_sources",
    "test_collector_factory_selection",
    "test_orchestrator_success_and_failure",
    "test_unsupported_source_type",
    "test_partial_collection_failure",
]
