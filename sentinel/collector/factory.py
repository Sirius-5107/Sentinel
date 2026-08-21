"""Collector factory for selecting the application collector for a Source.

Centralizes selection of RSS vs SCRAPE vs other collectors.
"""

from __future__ import annotations

from sentinel.collector.rss import RSSCollector
from sentinel.collector.scraper import StaticHTMLCollector
from sentinel.collector.base import BaseCollector
from sentinel_core.models.source import Source
from sentinel_core.enums import SourceType
from sentinel_core.exceptions.base import ConfigurationError
from typing import Any, cast


def get_collector_for_source(source: Source) -> Any:
    """Return an application collector instance appropriate for the Source.

    Raises ConfigurationError for unsupported source types.
    """
    if source.source_type == SourceType.RSS:
        return RSSCollector()
    if source.source_type == SourceType.SCRAPE:
        return StaticHTMLCollector()

    raise ConfigurationError(f"Unsupported source type for collection: {source.source_type}")


__all__ = ["get_collector_for_source"]
