"""Shared Pydantic base model for all Sentinel domain models.

Every domain model inherits from SentinelModel, which provides:

- Strict Pydantic v2 configuration (no extra fields allowed).
- UUID v4 primary key generated at construction time.
- UTC-aware created_at / updated_at timestamps set at construction time.
- Immutable (frozen=True): all domain objects are immutable value snapshots.
  Mutations produce a new object; they do not modify an existing one.
- JSON serialisation helpers.

Immutability policy
-------------------
All SentinelModel subclasses are frozen. This means:

- Fields cannot be changed after construction.
- ``updated_at`` is set once at construction time and never changes on the
  object itself. It represents the timestamp of *this snapshot/version* of
  the domain object — i.e., "this record was last known to be in this state
  at this time". When a mutation is required (e.g., a status transition), the
  application layer constructs a *new* SentinelModel instance that carries
  the new field values and a fresh ``updated_at``. The old object is
  discarded.

This is consistent with the event-centric ADR-0001 philosophy: all state
changes are explicit, auditable, and produce new versions rather than
silently mutating existing records.

UTC policy
----------
All datetime fields must be timezone-aware and in UTC. Naive datetimes (those
with tzinfo=None) are rejected at validation time. Non-UTC timezone-aware
datetimes are *normalised* to UTC rather than rejected, so callers do not need
to pre-convert. Serialised datetimes are always ISO 8601 strings with the UTC
offset (``+00:00``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(tz=UTC)


def _new_uuid() -> uuid.UUID:
    """Generate a new UUID v4."""
    return uuid.uuid4()


class SentinelModel(BaseModel):
    """Immutable base model for all Sentinel domain objects.

    Provides a UUID v4 primary key and UTC-aware timestamps. All subclasses
    are frozen (immutable). See module docstring for the full immutability and
    UTC policies.

    Fields:
        id: UUID v4 primary key. Generated at construction if not provided.
        created_at: UTC datetime set at construction; never changes.
        updated_at: UTC datetime representing the version timestamp of this
            snapshot. Set at construction. To "update" a record, construct a
            new instance with the desired field values and a new updated_at.

    Notes:
        - Extra fields are forbidden (strict schema).
        - Enums are serialised by value, not by name.
        - Datetimes are serialised as ISO 8601 strings with UTC offset.

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
        description=(
            "UTC version timestamp of this snapshot. Set at construction. "
            "To record a mutation, construct a new instance with a fresh updated_at."
        ),
    )

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _normalise_to_utc(cls, v: datetime) -> datetime:
        """Reject naive datetimes; normalise aware datetimes to UTC."""
        if v.tzinfo is None:
            raise ValueError(
                f"datetime must be timezone-aware; got naive datetime {v!r}. "
                "All SentinelModel timestamps must be UTC-aware."
            )
        return v.astimezone(UTC)

    def model_dump_json_safe(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict with UUIDs and datetimes as strings."""
        return self.model_dump(mode="json")
