"""Shared Pydantic base model for all Sentinel domain models.

Every domain model inherits from SentinelModel, which provides:

- Strict Pydantic v2 configuration (no extra fields allowed).
- UUID v4 primary key generated at construction time.
- UTC-aware created_at / updated_at timestamps set at construction time.
- Immutable (frozen=True) by default; subclasses that require mutation
  must set model_config explicitly and document the reason.
- JSON serialisation helpers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(tz=UTC)


def _new_uuid() -> uuid.UUID:
    """Generate a new UUID v4."""
    return uuid.uuid4()


class SentinelModel(BaseModel):
    """Immutable base model for all Sentinel domain objects.

    Provides a UUID v4 primary key and UTC-aware timestamps. All subclasses
    are frozen (immutable) unless they explicitly override model_config.

    Fields:
        id: UUID v4 primary key. Generated at construction if not provided.
        created_at: UTC datetime set at construction; never updated.
        updated_at: UTC datetime set at construction; updated on each mutation.

    Notes:
        - Extra fields are forbidden (strict schema).
        - Enums are serialised by value, not by name.
        - Datetimes are serialised as ISO 8601 strings.

    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
    )

    id: uuid.UUID = Field(
        default_factory=_new_uuid,
        description="UUID v4 primary key. Generated at construction if not supplied.",
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        description="UTC timestamp of record creation. Immutable after construction.",
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        description="UTC timestamp of the most recent mutation.",
    )

    def model_dump_json_safe(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict with UUIDs and datetimes as strings."""
        return self.model_dump(mode="json")
