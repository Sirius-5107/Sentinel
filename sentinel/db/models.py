"""SQLAlchemy ORM models for the Phase 2 persistence baseline."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import HttpUrl
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from sentinel_core.enums import (
    ArticleStatus,
    AssetClass,
    MarketRegion,
    Sector,
    Sentiment,
    SourceStatus,
    SourceType,
)
from sentinel_core.models.article import Article
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
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=SourceStatus.ACTIVE.value)
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

    articles: Mapped[list[ArticleORM]] = relationship(back_populates="source", cascade="all, delete")

    @classmethod
    def from_domain(cls, source: Source) -> SourceORM:
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
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ArticleStatus.INGESTED.value)
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
            duplicate_of_id=str(article.duplicate_of_id) if article.duplicate_of_id is not None else None,
            error_message=article.error_message,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    def to_domain(self) -> Article:
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
            duplicate_of_id=uuid.UUID(self.duplicate_of_id) if self.duplicate_of_id is not None else None,
            error_message=self.error_message,
            created_at=_required_utc(self.created_at),
            updated_at=_required_utc(self.updated_at),
        )


__all__ = ["ArticleORM", "Base", "SourceORM"]
