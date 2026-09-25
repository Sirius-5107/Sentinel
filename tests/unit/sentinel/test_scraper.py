"""Unit tests for StaticHTMLCollector (Phase 2 milestone)."""

from __future__ import annotations

from datetime import UTC
import hashlib
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from sentinel.collector.scraper import StaticHTMLCollector
from sentinel_core.enums import AssetClass, MarketRegion, SourceStatus, SourceType
from sentinel_core.exceptions.base import CollectionError
from sentinel_core.models import PipelineRun, Source
from sentinel_core.types import Url


@pytest.fixture
def scrape_source() -> Source:
    return Source(
        name="Example Scrape Source",
        url=Url("https://example.com/story"),
        source_type=SourceType.SCRAPE,
        status=SourceStatus.ACTIVE,
        region=MarketRegion.GLOBAL,
        asset_class=AssetClass.MACRO,
        language="en",
    )


@pytest.fixture
def pipeline_run() -> PipelineRun:
    return PipelineRun(trigger="manual")


@pytest.fixture
def collector() -> StaticHTMLCollector:
    return StaticHTMLCollector(timeout=5.0)


async def _collect_all(collector: StaticHTMLCollector, source: Source, run: PipelineRun) -> list:
    async_iter = await collector.collect(source, run)
    return [article async for article in async_iter]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_collect_extracts_valid_article(collector, scrape_source, pipeline_run):
    html = """
    <html>
      <head>
        <link rel="canonical" href="https://example.com/canonical-story" />
        <meta property="og:title" content="Fed Holds Rates Steady" />
        <meta property="og:description" content="Summary text" />
        <meta property="article:published_time" content="2026-08-20T08:30:00-04:00" />
        <title>Example</title>
      </head>
      <body>
        <article>
          <h1>Fed Holds Rates Steady</h1>
          <p>First paragraph about the rate decision.</p>
          <p>Second paragraph explaining the macro backdrop.</p>
        </article>
      </body>
    </html>
    """
    response = httpx.Response(200, text=html, request=httpx.Request("GET", str(scrape_source.url)))

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        articles = await _collect_all(collector, scrape_source, pipeline_run)

    assert len(articles) == 1
    article = articles[0]
    assert article.title == "Fed Holds Rates Steady"
    assert str(article.url) == "https://example.com/canonical-story"
    assert article.content is not None
    assert "First paragraph about the rate decision." in article.content
    assert article.summary == "Summary text"
    assert article.published_at is not None
    assert article.published_at.tzinfo is not None
    assert article.published_at.astimezone(UTC).isoformat() == "2026-08-20T12:30:00+00:00"
    assert article.status == "ingested"
    assert article.fetched_at.tzinfo is not None
    assert (
        article.content_hash
        == hashlib.sha256(b"Fed Holds Rates Steadyhttps://example.com/canonical-story").hexdigest()
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_title_and_fallbacks(collector, scrape_source, pipeline_run):
    html = (
        "<html><head><title>Fallback Title</title></head>"
        "<body><h1>Heading Fallback</h1><article><p>Body text.</p></article></body></html>"
    )
    response = httpx.Response(200, text=html, request=httpx.Request("GET", str(scrape_source.url)))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        articles = await _collect_all(collector, scrape_source, pipeline_run)
    assert len(articles) == 1
    assert articles[0].title == "Fallback Title"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_canonical_and_fallback_url(collector, scrape_source, pipeline_run):
    html = (
        '<html><head><meta property="og:url" content="https://example.com/og-url" /></head>'
        "<body><article><h1>Example</h1><p>Body text.</p></article></body></html>"
    )
    response = httpx.Response(200, text=html, request=httpx.Request("GET", str(scrape_source.url)))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        articles = await _collect_all(collector, scrape_source, pipeline_run)
    assert str(articles[0].url) == "https://example.com/og-url"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_summary_only_content_allowed(collector, scrape_source, pipeline_run):
    html = (
        '<html><head><meta property="og:title" content="No Full Content" />'
        '<meta property="og:description" content="A summary only." /></head>'
        "<body><main><nav>Links</nav><p>Navigation text.</p></main></body></html>"
    )
    response = httpx.Response(200, text=html, request=httpx.Request("GET", str(scrape_source.url)))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        articles = await _collect_all(collector, scrape_source, pipeline_run)
    assert len(articles) == 1
    assert articles[0].content is None
    assert articles[0].summary == "A summary only."


@pytest.mark.asyncio
@pytest.mark.unit
async def test_skip_when_no_title_or_content(collector, scrape_source, pipeline_run):
    html = "<html><body><div>There is no article.</div></body></html>"
    response = httpx.Response(200, text=html, request=httpx.Request("GET", str(scrape_source.url)))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        articles = await _collect_all(collector, scrape_source, pipeline_run)
    assert articles == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_missing_publication_date_allowed(collector, scrape_source, pipeline_run):
    html = (
        "<html><head><title>Article without date</title></head>"
        "<body><article><h1>Article without date</h1><p>Body text.</p></article></body></html>"
    )
    response = httpx.Response(200, text=html, request=httpx.Request("GET", str(scrape_source.url)))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        articles = await _collect_all(collector, scrape_source, pipeline_run)
    assert len(articles) == 1
    assert articles[0].published_at is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_invalid_or_missing_title_skipped(collector, scrape_source, pipeline_run):
    html = (
        '<html><head><meta property="og:url" content="https://example.com/article" /></head>'
        "<body><div>Just a page.</div></body></html>"
    )
    response = httpx.Response(200, text=html, request=httpx.Request("GET", str(scrape_source.url)))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        articles = await _collect_all(collector, scrape_source, pipeline_run)
    assert articles == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_http_error_raises_collection_error(collector, scrape_source, pipeline_run):
    response = httpx.Response(500, text="err", request=httpx.Request("GET", str(scrape_source.url)))
    with (
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response),
        pytest.raises(CollectionError),
    ):
        await _collect_all(collector, scrape_source, pipeline_run)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_timeout_raises_collection_error(collector, scrape_source, pipeline_run):
    with (
        patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.TimeoutException(
                "timed out", request=httpx.Request("GET", str(scrape_source.url))
            ),
        ),
        pytest.raises(CollectionError),
    ):
        await _collect_all(collector, scrape_source, pipeline_run)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_invalid_source_url_raises_collection_error(collector, scrape_source, pipeline_run):
    # Simulate httpx raising an InvalidURL when attempting to fetch the source
    with (
        patch(
            "httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=httpx.InvalidURL("invalid url"),
        ),
        pytest.raises(CollectionError),
    ):
        await _collect_all(collector, scrape_source, pipeline_run)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_malformed_html_handled(collector, scrape_source, pipeline_run):
    html = (
        '<html><head><meta property="og:title" content="Broken">'
        "<body><article><p>Missing closing tag"
    )
    response = httpx.Response(200, text=html, request=httpx.Request("GET", str(scrape_source.url)))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        articles = await _collect_all(collector, scrape_source, pipeline_run)
    assert len(articles) == 1
    assert articles[0].title == "Broken"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_respects_source_status_and_type(collector, scrape_source, pipeline_run):
    paused = Source(**{**scrape_source.model_dump(), "status": SourceStatus.PAUSED})
    articles = await _collect_all(collector, paused, pipeline_run)
    assert articles == []

    rss = Source(**{**scrape_source.model_dump(), "source_type": SourceType.RSS})
    with pytest.raises(CollectionError):
        await _collect_all(collector, rss, pipeline_run)
