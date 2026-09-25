"""Repositories for persisting application-domain data."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sentinel.db.models import (
    ArticleORM,
    DailyReportORM,
    MarketEventORM,
    ReportSectionORM,
    SourceORM,
)
from sentinel_core.models.article import Article
from sentinel_core.models.daily_report import DailyReport
from sentinel_core.models.market_event import MarketEvent
from sentinel_core.models.report_section import ReportSection
from sentinel_core.models.source import Source


class DuplicateArticleError(ValueError):
    """Raised when a persisted Article would violate URL or content-hash uniqueness."""


class SourceRepository:
    """Application-layer persistence for Source records."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        """Create a repository using a SQLAlchemy session factory."""
        self._session_factory = session_factory

    def save_source(self, source: Source) -> Source:
        """Save a source or return the existing persisted row for the same name."""
        with self._session_factory() as session:
            existing = session.scalar(select(SourceORM).where(SourceORM.name == source.name))
            if existing is not None:
                return existing.to_domain()

            orm = SourceORM.from_domain(source)
            session.add(orm)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise DuplicateArticleError("Source name already exists in the database.") from exc
            session.refresh(orm)
            return orm.to_domain()

    def get_by_name(self, name: str) -> Source | None:
        """Return a persisted source by name, if it exists."""
        with self._session_factory() as session:
            row = session.scalar(select(SourceORM).where(SourceORM.name == name))
            return row.to_domain() if row is not None else None


class ArticleRepository:
    """Application-layer persistence for Article records."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        """Create a repository using a SQLAlchemy session factory."""
        self._session_factory = session_factory

    def save_article(self, article: Article) -> Article:
        """Persist a new article unless URL or hash already exists."""
        with self._session_factory() as session:
            if (
                session.scalar(select(ArticleORM.id).where(ArticleORM.url == str(article.url)))
                is not None
            ):
                raise DuplicateArticleError(f"Article URL already exists: {article.url}")

            if (
                session.scalar(
                    select(ArticleORM.id).where(ArticleORM.content_hash == article.content_hash)
                )
                is not None
            ):
                raise DuplicateArticleError(
                    f"Article content hash already exists: {article.content_hash}"
                )

            orm = ArticleORM.from_domain(article)
            session.add(orm)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise DuplicateArticleError(
                    "Article duplicate rejected by database uniqueness constraint."
                ) from exc
            session.refresh(orm)
            return orm.to_domain()

    def get_by_url(self, url: str) -> Article | None:
        """Return a persisted article by URL, if it exists."""
        with self._session_factory() as session:
            row = session.scalar(select(ArticleORM).where(ArticleORM.url == url))
            return row.to_domain() if row is not None else None

    def get_by_content_hash(self, content_hash: str) -> Article | None:
        """Return a persisted article by content hash, if it exists."""
        with self._session_factory() as session:
            row = session.scalar(select(ArticleORM).where(ArticleORM.content_hash == content_hash))
            return row.to_domain() if row is not None else None


class MarketEventRepository:
    """Persist a validated MarketEvent and its supporting Article provenance."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        """Create a repository around the configured SQLAlchemy session factory."""
        self._session_factory = session_factory

    def save_market_event(
        self,
        event: MarketEvent,
        *,
        source_article_ids: Sequence[uuid.UUID],
    ) -> MarketEvent:
        """Persist a MarketEvent with its supporting Article provenance."""
        normalized = list(dict.fromkeys(uuid.UUID(str(item)) for item in source_article_ids))
        if not normalized:
            raise ValueError("A persisted MarketEvent requires at least one supporting Article.")

        with self._session_factory() as session:
            article_rows = session.scalars(
                select(ArticleORM).where(ArticleORM.id.in_([str(item) for item in normalized]))
            ).all()
            if len(article_rows) != len(normalized):
                found = {uuid.UUID(row.id) for row in article_rows}
                missing = [str(item) for item in normalized if item not in found]
                raise ValueError(
                    "MarketEvent provenance references Article IDs that do not exist "
                    f"in the database: {', '.join(missing)}"
                )

            event_orm = session.get(MarketEventORM, str(event.id))
            if event_orm is None:
                event_orm = MarketEventORM.from_domain(event)
                session.add(event_orm)
            else:
                event_orm.title = event.title
                event_orm.summary = event.summary
                event_orm.asset_class = event.asset_class.value
                event_orm.region = event.region.value
                event_orm.sector = event.sector.value if event.sector is not None else None
                event_orm.severity = event.severity.value
                event_orm.sentiment = event.sentiment.value
                event_orm.sentiment_confidence = float(event.sentiment_confidence)
                event_orm.importance_score = float(event.importance_score)
                event_orm.importance_confidence = float(event.importance_confidence)
                event_orm.occurred_at = event.occurred_at
                event_orm.market_id = str(event.market_id) if event.market_id is not None else None
                event_orm.embedding_id = (
                    str(event.embedding_id) if event.embedding_id is not None else None
                )
                event_orm.updated_at = event.updated_at

            event_orm.articles = list(article_rows)
            session.commit()
            session.refresh(event_orm)
            return event_orm.to_domain()


class ReportSectionRepository:
    """Persist a ReportSection and the MarketEvent membership relation."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        """Create a repository around the configured SQLAlchemy session factory."""
        self._session_factory = session_factory

    def save_report_section(
        self,
        section: ReportSection,
        *,
        market_event_ids: Sequence[uuid.UUID],
    ) -> ReportSection:
        """Persist a report section with its supporting MarketEvents."""
        normalized = list(dict.fromkeys(uuid.UUID(str(item)) for item in market_event_ids))
        if not normalized:
            raise ValueError("A persisted ReportSection requires at least one MarketEvent.")

        with self._session_factory() as session:
            event_rows = session.scalars(
                select(MarketEventORM).where(
                    MarketEventORM.id.in_([str(item) for item in normalized])
                )
            ).all()
            if len(event_rows) != len(normalized):
                found = {uuid.UUID(row.id) for row in event_rows}
                missing = [str(item) for item in normalized if item not in found]
                raise ValueError(
                    "ReportSection provenance references MarketEvent IDs not present "
                    f"in the database: {', '.join(missing)}"
                )

            section_orm = session.get(ReportSectionORM, str(section.id))
            if section_orm is None:
                section_orm = ReportSectionORM.from_domain(section)
                session.add(section_orm)
            else:
                section_orm.report_id = str(section.report_id)
                section_orm.title = section.title
                section_orm.order = section.order
                section_orm.content = section.content
                section_orm.theme_id = (
                    str(section.theme_id) if section.theme_id is not None else None
                )
                section_orm.asset_class = (
                    section.asset_class.value if section.asset_class is not None else None
                )
                section_orm.region = section.region.value if section.region is not None else None
                section_orm.word_count = section.word_count
                section_orm.event_count = section.event_count
                section_orm.updated_at = section.updated_at

            section_orm.market_events = list(event_rows)
            session.commit()
            session.refresh(section_orm)
            return section_orm.to_domain()


class DailyBriefRepository:
    """Persist a report, sections, and provenance across the intelligence chain."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        """Create a repository around the configured SQLAlchemy session factory."""
        self._session_factory = session_factory

    def save_daily_report(
        self,
        report: DailyReport,
        *,
        sections: Sequence[ReportSection],
        section_event_ids: Mapping[uuid.UUID, Sequence[uuid.UUID]] | None = None,
        event_article_ids: Mapping[uuid.UUID, Sequence[uuid.UUID]] | None = None,
    ) -> DailyReport:
        """Persist the whole brief while maintaining the article/event/section chain."""
        with self._session_factory() as session:
            report_orm = session.get(DailyReportORM, str(report.id))
            if report_orm is None:
                report_orm = DailyReportORM.from_domain(report)
                session.add(report_orm)
            else:
                report_orm.report_type = report.report_type.value
                report_orm.status = report.status.value
                report_orm.coverage_date = report.coverage_date
                report_orm.title = report.title
                report_orm.executive_summary = report.executive_summary
                report_orm.pipeline_run_id = (
                    str(report.pipeline_run_id) if report.pipeline_run_id is not None else None
                )
                report_orm.article_count = report.article_count
                report_orm.event_count = report.event_count
                report_orm.published_at = report.published_at
                report_orm.notion_page_id = report.notion_page_id
                report_orm.error_message = report.error_message
                report_orm.updated_at = report.updated_at

            for section in sections:
                section_orm = session.get(ReportSectionORM, str(section.id))
                if section_orm is None:
                    section_orm = ReportSectionORM.from_domain(section)
                    session.add(section_orm)
                else:
                    section_orm.report_id = str(section.report_id)
                    section_orm.title = section.title
                    section_orm.order = section.order
                    section_orm.content = section.content
                    section_orm.theme_id = (
                        str(section.theme_id) if section.theme_id is not None else None
                    )
                    section_orm.asset_class = (
                        section.asset_class.value if section.asset_class is not None else None
                    )
                    section_orm.region = (
                        section.region.value if section.region is not None else None
                    )
                    section_orm.word_count = section.word_count
                    section_orm.event_count = section.event_count
                    section_orm.updated_at = section.updated_at

                section_orm.report = report_orm
                if section_event_ids is not None:
                    event_ids = list(section_event_ids.get(section.id, ()))
                    if event_ids:
                        market_event_rows = session.scalars(
                            select(MarketEventORM).where(
                                MarketEventORM.id.in_([str(item) for item in event_ids])
                            )
                        ).all()
                        if len(market_event_rows) != len(set(event_ids)):
                            known_ids = {row.id for row in market_event_rows}
                            missing = [
                                str(item) for item in set(event_ids) if str(item) not in known_ids
                            ]
                            raise ValueError(
                                "Section provenance references MarketEvent IDs not "
                                f"present in the database: {', '.join(missing)}"
                            )
                        section_orm.market_events = list(market_event_rows)

            if event_article_ids is not None:
                for event_id, article_ids in event_article_ids.items():
                    normalized = list(dict.fromkeys(uuid.UUID(str(item)) for item in article_ids))
                    if not normalized:
                        continue
                    market_event_orm = session.get(MarketEventORM, str(event_id))
                    if market_event_orm is None:
                        raise ValueError(
                            "Report provenance references MarketEvent "
                            f"{event_id} without a persisted row."
                        )
                    article_rows = session.scalars(
                        select(ArticleORM).where(
                            ArticleORM.id.in_([str(item) for item in normalized])
                        )
                    ).all()
                    if len(article_rows) != len(normalized):
                        found = {uuid.UUID(row.id) for row in article_rows}
                        missing = [str(item) for item in normalized if item not in found]
                        raise ValueError(
                            "Daily brief provenance references Article IDs not present "
                            f"in the database: {', '.join(missing)}"
                        )
                    market_event_orm.articles = list(article_rows)

            session.commit()
            session.refresh(report_orm)
            return report_orm.to_domain()


__all__ = [
    "ArticleRepository",
    "DailyBriefRepository",
    "DuplicateArticleError",
    "MarketEventRepository",
    "ReportSectionRepository",
    "SourceRepository",
]
