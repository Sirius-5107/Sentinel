"""PipelineRun domain model.

A PipelineRun is the operational record of one full execution cycle of the
Sentinel data pipeline: collect -> process -> synthesise -> publish. It is the
audit log and health indicator for the platform.
"""

from __future__ import annotations

from datetime import UTC, datetime
import uuid

from pydantic import Field, field_validator, model_validator

from sentinel_core.enums import PipelineStatus
from sentinel_core.models._base import SentinelModel

_TERMINAL_STATUSES = frozenset(
    {PipelineStatus.SUCCESS, PipelineStatus.PARTIAL, PipelineStatus.FAILED}
)
_ALLOWED_TRIGGERS = frozenset({"scheduler", "manual", "api"})


class PipelineRun(SentinelModel):
    """An end-to-end execution record of the Sentinel data pipeline.

    PipelineRuns act as the audit log for the platform. Every Task executed
    within a run is linked to its PipelineRun. Operators query PipelineRuns
    to understand system health, latency, and output volume.

    duration_seconds is a computed property — it is derived from
    (completed_at - started_at) and must NOT be stored as a database column.

    Note on circular dependency with DailyReport:
        PipelineRun holds a nullable daily_report_id FK. DailyReport holds a
        nullable pipeline_run_id FK. Both sides are nullable; the application
        layer sets both after both records exist. See contracts §6 for rationale.

    Validation rules:
        - started_at must be None when status=PENDING.
        - completed_at must be None when status is PENDING or RUNNING.
        - completed_at must be >= started_at when non-None.
        - articles_ingested >= articles_processed.
        - trigger must be one of 'scheduler', 'manual', 'api'.
        - All datetime fields must be UTC-aware.

    Fields:
        id: UUID v4 primary key.
        status: Execution state; defaults to PENDING.
        started_at: UTC time the run began executing. None until RUNNING.
        completed_at: UTC time the run reached a terminal state. None until done.
        articles_ingested: Articles collected in this run (>= 0).
        articles_processed: Articles that completed classification (>= 0).
        articles_deduplicated: Articles identified as duplicates (>= 0).
        events_synthesised: MarketEvents created or updated (>= 0).
        error_count: Non-fatal errors across all tasks (>= 0).
        fatal_error: Error that halted the run when status=FAILED; max 5000 chars.
        trigger: What initiated this run: 'scheduler', 'manual', or 'api'.
        daily_report_id: FK to the DailyReport produced by this run. Optional.
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        PipelineRun(trigger="scheduler")
    """

    status: PipelineStatus = Field(
        default=PipelineStatus.PENDING,
        description="Current execution state of the pipeline run.",
    )
    started_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the run transitioned to RUNNING.",
    )
    completed_at: datetime | None = Field(
        default=None,
        description=(
            "UTC timestamp when the run reached a terminal state (SUCCESS, PARTIAL, or FAILED)."
        ),
    )
    articles_ingested: int = Field(
        default=0,
        ge=0,
        description="Count of articles collected in this run.",
    )
    articles_processed: int = Field(
        default=0,
        ge=0,
        description="Count of articles that completed classification.",
    )
    articles_deduplicated: int = Field(
        default=0,
        ge=0,
        description="Count of articles identified as duplicates.",
    )
    events_synthesised: int = Field(
        default=0,
        ge=0,
        description="Count of MarketEvents created or updated by this run.",
    )
    error_count: int = Field(
        default=0,
        ge=0,
        description="Total non-fatal errors across all tasks in this run.",
    )
    fatal_error: str | None = Field(
        default=None,
        max_length=5000,
        description="The error that halted the run. Set when status=FAILED.",
    )
    trigger: str = Field(
        default="scheduler",
        max_length=50,
        description="What initiated this run. Allowed values: 'scheduler', 'manual', 'api'.",
    )
    daily_report_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "FK to the DailyReport produced by this run. Set after the report record is created."
        ),
    )

    @property
    def duration_seconds(self) -> float | None:
        """Elapsed time in seconds between started_at and completed_at.

        Returns None if either timestamp is not set. This is a computed
        property — it must NOT be stored as a database column.
        """
        if self.started_at is None or self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    @field_validator("started_at", "completed_at", mode="before")
    @classmethod
    def _require_utc(cls, v: datetime | None) -> datetime | None:
        """Ensure timestamp fields are UTC-aware when provided."""
        if v is None:
            return None
        if v.tzinfo is None:
            raise ValueError("Timestamp fields must be UTC-aware (tzinfo must not be None).")
        return v.astimezone(UTC)

    @field_validator("trigger")
    @classmethod
    def _validate_trigger(cls, v: str) -> str:
        """Enforce trigger is one of the documented allowed values."""
        if v not in _ALLOWED_TRIGGERS:
            raise ValueError(f"trigger must be one of {sorted(_ALLOWED_TRIGGERS)!r}; got {v!r}.")
        return v

    @model_validator(mode="after")
    def _validate_state_machine_rules(self) -> PipelineRun:
        """Enforce temporal consistency between status and timestamps."""
        # started_at must be None when PENDING
        if self.status == PipelineStatus.PENDING and self.started_at is not None:
            raise ValueError("started_at must be None when status=PENDING.")

        # completed_at must be None when PENDING or RUNNING
        if self.status not in _TERMINAL_STATUSES and self.completed_at is not None:
            raise ValueError(f"completed_at must be None when status={self.status!r}.")

        # completed_at >= started_at
        if (
            self.completed_at is not None
            and self.started_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at must be >= started_at.")

        # articles_ingested >= articles_processed
        if self.articles_processed > self.articles_ingested:
            raise ValueError(
                f"articles_processed ({self.articles_processed}) must not exceed "
                f"articles_ingested ({self.articles_ingested})."
            )

        return self
