"""Repositories for persisting Phase 2 Source and Article records."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sentinel.db.models import ArticleORM, SourceORM
from sentinel_core.models.article import Article
from sentinel_core.models.source import Source


class DuplicateArticleError(ValueError):
    """Raised when a persisted Article would violate URL or content-hash uniqueness."""


class SourceRepository:
    """Application-layer persistence for Source records."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def save_source(self, source: Source) -> Source:
        with self._session_factory() as session:
            existing = session.scalar(
                select(SourceORM).where(SourceORM.name == source.name)
            )
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
        with self._session_factory() as session:
            row = session.scalar(select(SourceORM).where(SourceORM.name == name))
            return row.to_domain() if row is not None else None


class ArticleRepository:
    """Application-layer persistence for Article records."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def save_article(self, article: Article) -> Article:
        with self._session_factory() as session:
            if session.scalar(
                select(ArticleORM.id).where(ArticleORM.url == str(article.url))
            ) is not None:
                raise DuplicateArticleError(f"Article URL already exists: {article.url}")

            if session.scalar(
                select(ArticleORM.id).where(ArticleORM.content_hash == article.content_hash)
            ) is not None:
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
        with self._session_factory() as session:
            row = session.scalar(select(ArticleORM).where(ArticleORM.url == url))
            return row.to_domain() if row is not None else None

    def get_by_content_hash(self, content_hash: str) -> Article | None:
        with self._session_factory() as session:
            row = session.scalar(select(ArticleORM).where(ArticleORM.content_hash == content_hash))
            return row.to_domain() if row is not None else None


__all__ = ["ArticleRepository", "DuplicateArticleError", "SourceRepository"]
