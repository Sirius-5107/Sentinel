"""Session and engine configuration for the application database."""

from __future__ import annotations

import os
from typing import Any, Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sentinel.db.models import Base


def get_database_url() -> str:
    """Return the configured database URL.

    When PostgreSQL environment variables are present, prefer the canonical
    SQLAlchemy PostgreSQL DSN format used by the local development stack:
    postgresql+psycopg://user:password@host:port/dbname
    """

    configured_url = os.getenv("SENTINEL_DB_URL")
    if configured_url:
        return configured_url

    db_host = os.getenv("SENTINEL_DB_HOST")
    db_port = os.getenv("SENTINEL_DB_PORT")
    db_name = os.getenv("SENTINEL_DB_NAME")
    db_user = os.getenv("SENTINEL_DB_USER")
    db_password = os.getenv("SENTINEL_DB_PASSWORD")

    if db_host and db_name and db_user:
        return (
            f"postgresql+psycopg://{db_user}:{db_password or ''}@{db_host}:{db_port or 5432}/{db_name}"
        )

    return "sqlite:///./sentinel_phase2.db"


def _build_engine() -> Any:
    database_url = get_database_url()
    engine_kwargs: dict[str, Any] = {"future": True}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **engine_kwargs)


engine = _build_engine()
session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def create_all() -> None:
    """Create the application schema bound to the configured database URL."""

    Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session for repository operations."""

    session = session_factory()
    try:
        yield session
    finally:
        session.close()


__all__ = ["create_all", "engine", "get_database_url", "get_session", "session_factory"]
