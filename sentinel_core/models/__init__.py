"""Sentinel domain models.

All models are immutable Pydantic v2 BaseModel subclasses. They represent
the canonical domain contracts for Phase 1 of the Sentinel platform.

Import order follows the dependency graph in docs/05-contracts.md §5:

    Level 0  Value objects and enums (sentinel_core.types / sentinel_core.enums)
    Level 1  Market, Organization, Theme
    Level 2  Company, Person
    Level 3  Source, Article
    Level 4  MarketEvent
    Level 5  PipelineRun, Task
    Level 6  DailyReport, ReportSection
"""

from sentinel_core.models.article import Article
from sentinel_core.models.company import Company
from sentinel_core.models.daily_report import DailyReport
from sentinel_core.models.market import Market
from sentinel_core.models.market_event import MarketEvent
from sentinel_core.models.organization import Organization
from sentinel_core.models.person import Person
from sentinel_core.models.pipeline_run import PipelineRun
from sentinel_core.models.report_section import ReportSection
from sentinel_core.models.source import Source
from sentinel_core.models.task import Task
from sentinel_core.models.theme import Theme

__all__ = [
    "Article",
    "Company",
    "DailyReport",
    "Market",
    "MarketEvent",
    "Organization",
    "Person",
    "PipelineRun",
    "ReportSection",
    "Source",
    "Task",
    "Theme",
]
