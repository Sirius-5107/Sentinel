"""Sentinel domain enumerations.

All enums inherit from (str, Enum) so they serialise naturally to JSON
and are stored as plain strings in PostgreSQL. No integer codes are used.

Exported enums
--------------
SourceType, SourceStatus          — source / collector lifecycle
ArticleStatus                     — article processing pipeline state
Sentiment                         — market sentiment direction
AssetClass                        — financial asset class
MarketRegion                      — geographic market region
Sector                            — GICS-aligned industry sector
EventSeverity                     — market event impact level
EntityType                        — named-entity category
ReportType, ReportStatus          — report format and publication state
PipelineStatus, TaskStatus        — operational pipeline execution state
"""

from sentinel_core.enums.article import ArticleStatus
from sentinel_core.enums.financial import (
    AssetClass,
    EntityType,
    EventSeverity,
    MarketRegion,
    Sector,
    Sentiment,
)
from sentinel_core.enums.report import (
    PipelineStatus,
    ReportStatus,
    ReportType,
    TaskStatus,
)
from sentinel_core.enums.source import SourceStatus, SourceType

__all__ = [
    "ArticleStatus",
    "AssetClass",
    "EntityType",
    "EventSeverity",
    "MarketRegion",
    "PipelineStatus",
    "ReportStatus",
    "ReportType",
    "Sector",
    "Sentiment",
    "SourceStatus",
    "SourceType",
    "TaskStatus",
]
