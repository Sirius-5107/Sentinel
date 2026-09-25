"""Static HTML collector for SourceType.SCRAPE (Phase 2 milestone).

This collector fetches a single static page and attempts to extract an
Article domain object. It implements the CollectorProtocol contract by
providing an async collect(...) that yields Article objects and performs
no persistence.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
import hashlib
from typing import Final
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser, Node

from sentinel_core.enums import ArticleStatus, SourceStatus, SourceType
from sentinel_core.exceptions.base import CollectionError
from sentinel_core.models import Article, PipelineRun, Source
from sentinel_core.types import Url

_DEFAULT_TIMEOUT: Final[float] = 15.0


class StaticHTMLCollector:
    """Collect static HTML content from SourceType.SCRAPE sources.

    The collector is intentionally small and conservative: it extracts title,
    canonical URL, summary metadata, publication date, and article body text.
    It yields at most one Article per page and never performs persistence.
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        """Initialise the collector with an HTTP request timeout in seconds."""
        self.timeout = timeout

    async def collect(
        self,
        source: Source,
        run: PipelineRun,
    ) -> AsyncIterator[Article]:
        """Return an async iterator that yields Article objects if extraction succeeds.

        The collector follows the same pattern as RSSCollector: collect is an async
        function that returns an async iterator when awaited. This keeps the
        collector API uniform so the orchestrator can await the coroutine to
        obtain an async iterator.
        """
        del run

        async def _generate() -> AsyncIterator[Article]:
            if source.source_type != SourceType.SCRAPE:
                raise CollectionError(
                    f"StaticHTMLCollector requires source_type=SCRAPE; got {source.source_type!r}."
                )

            if source.status != SourceStatus.ACTIVE:
                return

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(str(source.url))
            except (httpx.InvalidURL, httpx.HTTPError, ValueError) as exc:
                raise CollectionError(f"Failed to fetch source URL {source.url!s}: {exc}") from exc

            if response.status_code >= 400:
                raise CollectionError(
                    f"Failed to fetch source URL {source.url!s}: HTTP {response.status_code}."
                )

            if not response.text:
                return

            try:
                document = HTMLParser(response.text)
            except Exception:  # selectolax may raise on malformed content
                # Treat parse errors as non-fatal: no article yielded
                return

            article = self._build_article(document, source)
            if article is not None:
                yield article

        return _generate()

    def _build_article(self, document: HTMLParser, source: Source) -> Article | None:
        title = self._extract_title(document)
        if not title:
            return None

        url = self._extract_canonical_url(document, source)
        if not url:
            return None

        content = self._extract_content(document)
        summary = self._extract_summary(document)

        # Require meaningful content or a summary
        if content is None and summary is None:
            return None

        published_at = self._extract_published_at(document)

        # Build Article using the Url value object to validate
        try:
            article = Article(
                source_id=source.id,
                title=title,
                url=Url(url),
                content=content,
                summary=summary,
                published_at=published_at,
                fetched_at=datetime.now(tz=UTC),
                language=source.language,
                status=ArticleStatus.INGESTED,
                content_hash=self._hash_content(title, url),
            )
        except Exception:
            # If Pydantic validation fails, do not yield an invalid Article
            return None

        return article

    def _extract_title(self, document: HTMLParser) -> str | None:
        # Priority: og:title, twitter:title, <title>, first <h1>
        selectors = (
            ('meta[property="og:title"]', "content"),
            ('meta[name="twitter:title"]', "content"),
            ("title", None),
            ("h1", None),
        )
        for selector, attr in selectors:
            node = document.css_first(selector)
            if node is None:
                continue
            value = node.attributes.get(attr) if attr else node.text()
            clean = self._clean_text(value)
            if clean:
                return clean
        return None

    def _extract_canonical_url(self, document: HTMLParser, source: Source) -> str | None:
        # Priority: link[rel=canonical], og:url, twitter:url, fall back to source.url
        selectors = (
            ('link[rel="canonical"]', "href"),
            ('meta[property="og:url"]', "content"),
            ('meta[name="twitter:url"]', "content"),
        )
        for selector, attr in selectors:
            node = document.css_first(selector)
            if node is None:
                continue
            raw = node.attributes.get(attr)
            if not raw:
                continue
            resolved = self._resolve_url(raw, str(source.url))
            if resolved:
                return resolved

        # Fall back to the source URL
        return str(source.url)

    def _extract_summary(self, document: HTMLParser) -> str | None:
        selectors = (
            ('meta[property="og:description"]', "content"),
            ('meta[name="description"]', "content"),
            ('meta[name="twitter:description"]', "content"),
        )
        for selector, attr in selectors:
            node = document.css_first(selector)
            if node is None:
                continue
            value = node.attributes.get(attr)
            summary = self._clean_text(value)
            if summary:
                return summary
        return None

    def _extract_content(self, document: HTMLParser) -> str | None:
        # Candidate containers in order of preference
        selectors = (
            "article",
            "div.article-body",
            "section.article-body",
            "div.entry-content",
            "div.post-content",
            "div.story-content",
            ".article-content",
            ".content",
        )
        for sel in selectors:
            node = document.css_first(sel)
            if node is None:
                continue
            text = self._candidate_text(node)
            if text and len(text) >= 10:
                return text
        # Try to find longest paragraph cluster
        paras = [self._clean_text(n.text()) for n in document.css("p") if n and n.text()]
        paras = [p for p in paras if len(p) >= 20]
        if paras:
            return "\n\n".join(paras)
        return None

    def _extract_published_at(self, document: HTMLParser) -> datetime | None:
        selectors = (
            ('meta[property="article:published_time"]', "content"),
            ('meta[name="pubdate"]', "content"),
            ('meta[name="date"]', "content"),
            ("time[datetime]", "datetime"),
        )
        for selector, attr in selectors:
            node = document.css_first(selector)
            if node is None:
                continue
            raw = node.attributes.get(attr)
            if not raw:
                continue
            parsed = self._parse_datetime(raw)
            if parsed is not None:
                return parsed
        return None

    def _candidate_text(self, node: Node) -> str:
        # Collect text from paragraph-like children while avoiding nav/footer/script/style
        parts: list[str] = []
        for child in node.css("p, li, blockquote, h2, h3, h4"):
            text = self._clean_text(child.text())
            if not text:
                continue
            parts.append(text)
        if parts:
            return "\n\n".join(parts)
        # Fallback: plain node text
        return self._clean_text(node.text())

    def _parse_datetime(self, raw_value: str) -> datetime | None:
        v = (raw_value or "").strip()
        if not v:
            return None
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(v)
        except Exception:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(UTC)

    def _resolve_url(self, raw_url: str, base: str) -> str | None:
        if not raw_url:
            return None
        val = raw_url.strip()
        if val.startswith("//"):
            val = "https:" + val
        if val.startswith("http://") or val.startswith("https://"):
            return val
        try:
            return urljoin(base, val)
        except Exception:
            return None

    def _hash_content(self, title: str, url: str) -> str:
        raw = f"{title}{url}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _clean_text(self, value: str | None) -> str:
        if not value:
            return ""
        return " ".join(value.split())
