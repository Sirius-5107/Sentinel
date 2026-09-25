"""SQLAlchemy ORM models for the Phase 2 persistence baseline."""

from __future__ import annotations

from datetime import UTC, date, datetime
import uuid

from pydantic import HttpUrl
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from sentinel_core.enums import (
    ArticleStatus,
    AssetClass,
    EventSeverity,
    MarketRegion,
    ReportStatus,
    ReportType,
    Sector,
    Sentiment,
    SourceStatus,
    SourceType,
)
from sentinel_core.models.article import Article
from sentinel_core.models.daily_report import DailyReport
from sentinel_core.models.market_event import MarketEvent
from sentinel_core.models.report_section import ReportSection
from sentinel_core.models.source import Source


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _required_utc(value: datetime | None) -> datetime:
    result = _as_utc(value)
    if result is None:
        raise ValueError("UTC datetime value was unexpectedly null.")
    return result


class Base(DeclarativeBase):
    """Declarative base for the application persistence layer."""


class SourceORM(Base):
    """SQLAlchemy representation of a Source."""

    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("name", name="uq_source_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SourceStatus.ACTIVE.value
    )
    region: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(32), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    fetch_interval_minutes: Mapped[int] = mapped_column(default=60, nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    consecutive_errors: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    articles: Mapped[list[ArticleORM]] = relationship(
        back_populates="source",
        cascade="all, delete",
    )

    @classmethod
    def from_domain(cls, source: Source) -> SourceORM:
        """Create a SourceORM row from a Source domain model."""
        return cls(
            id=str(source.id),
            name=source.name,
            url=str(source.url),
            source_type=source.source_type.value,
            status=source.status.value,
            region=source.region.value,
            asset_class=source.asset_class.value,
            language=source.language,
            weight=float(source.weight),
            fetch_interval_minutes=source.fetch_interval_minutes,
            last_fetched_at=source.last_fetched_at,
            last_error=source.last_error,
            consecutive_errors=source.consecutive_errors,
            created_at=_required_utc(source.created_at),
            updated_at=_required_utc(source.updated_at),
        )

    def to_domain(self) -> Source:
        """Convert the database row back to a Source domain model."""
        return Source(
            id=uuid.UUID(self.id),
            name=self.name,
            url=HttpUrl(self.url),
            source_type=SourceType(self.source_type),
            status=SourceStatus(self.status),
            region=MarketRegion(self.region),
            asset_class=AssetClass(self.asset_class),
            language=self.language,
            weight=self.weight,
            fetch_interval_minutes=self.fetch_interval_minutes,
            last_fetched_at=_as_utc(self.last_fetched_at),
            last_error=self.last_error,
            consecutive_errors=self.consecutive_errors,
            created_at=_required_utc(self.created_at),
            updated_at=_required_utc(self.updated_at),
        )


class ArticleORM(Base):
    """SQLAlchemy representation of an Article."""

    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("url", name="uq_article_url"),
        UniqueConstraint("content_hash", name="uq_article_content_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ArticleStatus.INGESTED.value
    )
    asset_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sentiment_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    importance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    importance_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    duplicate_of_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    source: Mapped[SourceORM] = relationship(back_populates="articles")

    @classmethod
    def from_domain(cls, article: Article) -> ArticleORM:
        """Create an ArticleORM row from an Article domain model."""
        return cls(
            id=str(article.id),
            source_id=str(article.source_id),
            title=article.title,
            url=str(article.url),
            content=article.content,
            summary=article.summary,
            published_at=article.published_at,
            fetched_at=article.fetched_at,
            language=article.language,
            status=article.status.value,
            asset_class=article.asset_class.value if article.asset_class is not None else None,
            region=article.region.value if article.region is not None else None,
            sector=article.sector.value if article.sector is not None else None,
            sentiment=article.sentiment.value if article.sentiment is not None else None,
            sentiment_confidence=article.sentiment_confidence,
            importance_score=article.importance_score,
            importance_confidence=article.importance_confidence,
            content_hash=article.content_hash,
            embedding_id=str(article.embedding_id) if article.embedding_id is not None else None,
            duplicate_of_id=(
                str(article.duplicate_of_id) if article.duplicate_of_id is not None else None
            ),
            error_message=article.error_message,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    def to_domain(self) -> Article:
        """Convert the database row back to an Article domain model."""
        return Article(
            id=uuid.UUID(self.id),
            source_id=uuid.UUID(self.source_id),
            title=self.title,
            url=HttpUrl(self.url),
            content=self.content,
            summary=self.summary,
            published_at=_as_utc(self.published_at),
            fetched_at=_required_utc(self.fetched_at),
            language=self.language,
            status=ArticleStatus(self.status),
            asset_class=AssetClass(self.asset_class) if self.asset_class is not None else None,
            region=MarketRegion(self.region) if self.region is not None else None,
            sector=Sector(self.sector) if self.sector is not None else None,
            sentiment=Sentiment(self.sentiment) if self.sentiment is not None else None,
            sentiment_confidence=self.sentiment_confidence,
            importance_score=self.importance_score,
            importance_confidence=self.importance_confidence,
            content_hash=self.content_hash,
            embedding_id=uuid.UUID(self.embedding_id) if self.embedding_id is not None else None,
            duplicate_of_id=(
                uuid.UUID(self.duplicate_of_id) if self.duplicate_of_id is not None else None
            ),
            error_message=self.error_message,
            created_at=_required_utc(self.created_at),
            updated_at=_required_utc(self.updated_at),
        )


article_market_event_table = Table(
    "article_market_event",
    Base.metadata,
    Column("article_id", String(36), ForeignKey("articles.id"), primary_key=True),
    Column("market_event_id", String(36), ForeignKey("market_events.id"), primary_key=True),
)

market_event_report_section_table = Table(
    "market_event_report_section",
    Base.metadata,
    Column("market_event_id", String(36), ForeignKey("market_events.id"), primary_key=True),
    Column("report_section_id", String(36), ForeignKey("report_sections.id"), primary_key=True),
)


class MarketEventORM(Base):
    """SQLAlchemy representation of a MarketEvent."""

    __tablename__ = "market_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    asset_class: Mapped[str] = mapped_column(String(32), nullable=False)
    region: Mapped[str] = mapped_column(String(32), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(32), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(32), nullable=False)
    sentiment_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False)
    importance_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    market_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    articles: Mapped[list[ArticleORM]] = relationship(
        secondary=article_market_event_table,
        back_populates="market_events",
    )
    report_sections: Mapped[list[ReportSectionORM]] = relationship(
        secondary=market_event_report_section_table,
        back_populates="market_events",
    )

    @classmethod
    def from_domain(cls, event: MarketEvent) -> MarketEventORM:
        """Create a MarketEventORM from a MarketEvent domain model."""
        return cls(
            id=str(event.id),
            title=event.title,
            summary=event.summary,
            asset_class=event.asset_class.value,
            region=event.region.value,
            sector=event.sector.value if event.sector is not None else None,
            severity=event.severity.value,
            sentiment=event.sentiment.value,
            sentiment_confidence=float(event.sentiment_confidence),
            importance_score=float(event.importance_score),
            importance_confidence=float(event.importance_confidence),
            occurred_at=_required_utc(event.occurred_at),
            market_id=str(event.market_id) if event.market_id is not None else None,
            embedding_id=str(event.embedding_id) if event.embedding_id is not None else None,
            created_at=_required_utc(event.created_at),
            updated_at=_required_utc(event.updated_at),
        )

    def to_domain(self) -> MarketEvent:
        """Convert the database row back to a MarketEvent domain model."""
        return MarketEvent(
            id=uuid.UUID(self.id),
            title=self.title,
            summary=self.summary,
            asset_class=AssetClass(self.asset_class),
            region=MarketRegion(self.region),
            sector=Sector(self.sector) if self.sector is not None else None,
            severity=EventSeverity(self.severity),
            sentiment=Sentiment(self.sentiment),
            sentiment_confidence=float(self.sentiment_confidence),
            importance_score=float(self.importance_score),
            importance_confidence=float(self.importance_confidence),
            occurred_at=_required_utc(self.occurred_at),
            market_id=uuid.UUID(self.market_id) if self.market_id is not None else None,
            embedding_id=uuid.UUID(self.embedding_id) if self.embedding_id is not None else None,
            created_at=_required_utc(self.created_at),
            updated_at=_required_utc(self.updated_at),
        )


class DailyReportORM(Base):
    """SQLAlchemy representation of a DailyReport."""

    __tablename__ = "daily_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    coverage_date: Mapped[date] = mapped_column(DateTime, nullable=False)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    pipeline_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    article_count: Mapped[int] = mapped_column(default=0, nullable=False)
    event_count: Mapped[int] = mapped_column(default=0, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notion_page_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sections: Mapped[list[ReportSectionORM]] = relationship(back_populates="report")

    @classmethod
    def from_domain(cls, report: DailyReport) -> DailyReportORM:
        """Create a DailyReportORM from a DailyReport domain model."""
        return cls(
            id=str(report.id),
            report_type=report.report_type.value,
            status=report.status.value,
            coverage_date=report.coverage_date,
            title=report.title,
            executive_summary=report.executive_summary,
            pipeline_run_id=(
                str(report.pipeline_run_id) if report.pipeline_run_id is not None else None
            ),
            article_count=report.article_count,
            event_count=report.event_count,
            published_at=_as_utc(report.published_at),
            notion_page_id=report.notion_page_id,
            error_message=report.error_message,
            created_at=_required_utc(report.created_at),
            updated_at=_required_utc(report.updated_at),
        )

    def to_domain(self) -> DailyReport:
        """Convert the database row back to a DailyReport domain model."""
        return DailyReport(
            id=uuid.UUID(self.id),
            report_type=ReportType(self.report_type),
            status=ReportStatus(self.status),
            coverage_date=self.coverage_date,
            title=self.title,
            executive_summary=self.executive_summary,
            pipeline_run_id=(
                uuid.UUID(self.pipeline_run_id) if self.pipeline_run_id is not None else None
            ),
            article_count=self.article_count,
            event_count=self.event_count,
            published_at=_as_utc(self.published_at),
            notion_page_id=self.notion_page_id,
            error_message=self.error_message,
            created_at=_required_utc(self.created_at),
            updated_at=_required_utc(self.updated_at),
        )


class ReportSectionORM(Base):
    """SQLAlchemy representation of a ReportSection."""

    __tablename__ = "report_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str] = mapped_column(ForeignKey("daily_reports.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order: Mapped[int] = mapped_column(default=0, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    theme_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    asset_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    region: Mapped[str | None] = mapped_column(String(32), nullable=True)
    word_count: Mapped[int | None] = mapped_column(default=None, nullable=True)
    event_count: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    report: Mapped[DailyReportORM] = relationship(back_populates="sections")
    market_events: Mapped[list[MarketEventORM]] = relationship(
        secondary=market_event_report_section_table,
        back_populates="report_sections",
    )

    @classmethod
    def from_domain(cls, section: ReportSection) -> ReportSectionORM:
        """Create a ReportSectionORM from a ReportSection domain model."""
        return cls(
            id=str(section.id),
            report_id=str(section.report_id),
            title=section.title,
            order=section.order,
            content=section.content,
            theme_id=str(section.theme_id) if section.theme_id is not None else None,
            asset_class=section.asset_class.value if section.asset_class is not None else None,
            region=section.region.value if section.region is not None else None,
            word_count=section.word_count,
            event_count=section.event_count,
            created_at=_required_utc(section.created_at),
            updated_at=_required_utc(section.updated_at),
        )

    def to_domain(self) -> ReportSection:
        """Convert the database row back to a ReportSection domain model."""
        return ReportSection(
            id=uuid.UUID(self.id),
            report_id=uuid.UUID(self.report_id),
            title=self.title,
            order=self.order,
            content=self.content,
            theme_id=uuid.UUID(self.theme_id) if self.theme_id is not None else None,
            asset_class=AssetClass(self.asset_class) if self.asset_class is not None else None,
            region=MarketRegion(self.region) if self.region is not None else None,
            word_count=self.word_count,
            event_count=self.event_count,
            created_at=_required_utc(self.created_at),
            updated_at=_required_utc(self.updated_at),
        )


ArticleORM.market_events = relationship(
    "MarketEventORM",
    secondary=article_market_event_table,
    back_populates="articles",
)

__all__ = [
    "ArticleORM",
    "Base",
    "DailyReportORM",
    "MarketEventORM",
    "ReportSectionORM",
    "SourceORM",
]
