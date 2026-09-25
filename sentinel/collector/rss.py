"""RSS collector implementation for the Phase 2 ingestion milestone."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
import hashlib
from time import mktime, struct_time

import feedparser
from pydantic import HttpUrl

from sentinel.collector.base import BaseCollector
from sentinel_core.enums import ArticleStatus
from sentinel_core.models.article import Article
from sentinel_core.models.pipeline_run import PipelineRun
from sentinel_core.models.source import Source


class RSSCollector(BaseCollector):
    """Collect Articles from an RSS or Atom source.

    The collector itself does not persist Articles; it yields ingested Article
    domain objects for the application layer to save to the repository.
    """

    def __init__(self, parser: Callable[..., object] | None = None) -> None:
        """Create a collector bound to an RSS parser implementation."""
        self._parser = parser or feedparser.parse

    def _coerce_datetime(self, value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                raise ValueError("RSS entry datetimes must be timezone-aware.")
            return value.astimezone(UTC)
        if isinstance(value, struct_time):
            return datetime.fromtimestamp(mktime(value), tz=UTC)
        if isinstance(value, str):
            try:
                parsed = parsedate_to_datetime(value)
            except (TypeError, ValueError):
                return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        return None

    async def collect(
        self,
        source: Source,
        run: PipelineRun,
    ) -> AsyncIterator[Article]:
        """Parse an RSS feed and return an async iterator of Article objects."""
        del run

        async def _generate() -> AsyncIterator[Article]:
            parsed = self._parser(str(source.url))
            entries = getattr(parsed, "entries", [])
            for entry in entries:
                title = str(entry.get("title") or "").strip()
                link = str(entry.get("link") or entry.get("id") or "").strip()
                if not title or not link:
                    continue

                raw_summary = entry.get("summary") or entry.get("description")
                summary = str(raw_summary).strip() if isinstance(raw_summary, str) else None
                raw_content = None
                if isinstance(entry.get("content"), list) and entry["content"]:
                    first_content = entry["content"][0]
                    if isinstance(first_content, dict):
                        raw_content = first_content.get("value")
                content = str(raw_content).strip() if isinstance(raw_content, str) else None
                if content is None and summary is not None:
                    content = summary

                published_at = None
                for candidate_key in ("published_parsed", "updated_parsed", "created_parsed"):
                    candidate = entry.get(candidate_key)
                    if candidate is None:
                        continue
                    try:
                        published_at = self._coerce_datetime(candidate)
                    except ValueError:
                        published_at = None
                    if published_at is not None:
                        break
                if published_at is None:
                    published_text = (
                        entry.get("published") or entry.get("updated") or entry.get("created")
                    )
                    if isinstance(published_text, str):
                        published_at = self._coerce_datetime(published_text)

                yield Article(
                    source_id=source.id,
                    title=title,
                    url=HttpUrl(link),
                    content=content,
                    summary=summary,
                    published_at=published_at,
                    fetched_at=datetime.now(tz=UTC),
                    language=source.language,
                    status=ArticleStatus.INGESTED,
                    content_hash=hashlib.sha256(f"{title}{link}".encode()).hexdigest(),
                )

        return _generate()


__all__ = ["RSSCollector"]
