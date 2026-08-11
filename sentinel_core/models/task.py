"""Task domain model.

A Task is a single unit of work within a PipelineRun — the atomic audit unit
of the pipeline (e.g. 'collect.reuters_rss', 'process.classify', 'publish.notion').
"""

from __future__ import annotations

from datetime import datetime
import uuid

from pydantic import Field, field_validator, model_validator

from sentinel_core.enums import TaskStatus
from sentinel_core.models._base import SentinelModel

_TERMINAL_TASK_STATUSES = frozenset({TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED})


class Task(SentinelModel):
    """A single unit of work within a PipelineRun.

    Tasks enable fine-grained observability: an operator can identify exactly
    which step in a run failed, how long each step took, and what it produced.

    Name convention:
        Use dot-separated namespacing: 'stage.task_name'.
        Examples: 'collect.reuters_rss', 'process.classify', 'publish.notion'.

    duration_seconds is a computed property — it is derived from
    (completed_at - started_at) and must NOT be stored as a database column.

    Validation rules:
        - completed_at must be None when status is PENDING or RUNNING.
        - completed_at must be >= started_at when non-None.
        - items_failed <= items_processed.
        - metadata values must all be strings (enforced by the type annotation).
        - All datetime fields must be UTC-aware.

    Fields:
        id: UUID v4 primary key.
        pipeline_run_id: FK to the owning PipelineRun.
        name: Human-readable task name using dot notation; 1-200 chars.
        status: Execution state; defaults to PENDING.
        started_at: UTC time the task began. None until RUNNING.
        completed_at: UTC time the task reached a terminal state. None until done.
        items_processed: Count of items operated on (>= 0).
        items_failed: Count of items that failed within this task (>= 0).
        error_message: Error detail when status=FAILED; max 5000 chars.
        metadata: String key-value pairs for task-specific context.
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        Task(
            pipeline_run_id=uuid.UUID("..."),
            name="collect.reuters_rss",
            status=TaskStatus.SUCCESS,
            items_processed=42,
            items_failed=0,
            metadata={"source": "Reuters Business", "batch_size": "50"},
        )
    """

    pipeline_run_id: uuid.UUID = Field(
        description="FK to the PipelineRun that owns this task.",
    )
    name: str = Field(
        min_length=1,
        max_length=200,
        description=(
            "Human-readable task name using dot-separated namespacing. "
            "Convention: 'stage.task_name' (e.g. 'collect.reuters_rss')."
        ),
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current execution state of this task.",
    )
    started_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the task began executing.",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the task reached a terminal state.",
    )
    items_processed: int = Field(
        default=0,
        ge=0,
        description="Count of items (articles, events, etc.) this task operated on.",
    )
    items_failed: int = Field(
        default=0,
        ge=0,
        description="Count of items that failed during this task's execution.",
    )
    error_message: str | None = Field(
        default=None,
        max_length=5000,
        description="Error detail set when status=FAILED.",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Arbitrary string key-value pairs for task-specific context. "
            "All keys and values must be strings. Nested objects are not permitted; "
            "flatten them before storing."
        ),
    )

    @property
    def duration_seconds(self) -> float | None:
        """Elapsed time in seconds between started_at and completed_at.

        Returns None if either timestamp is not set. Computed property —
        must NOT be stored as a database column.
        """
        if self.started_at is None or self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    @field_validator("started_at", "completed_at", mode="before")
    @classmethod
    def _require_utc(cls, v: datetime | None) -> datetime | None:
        """Ensure timestamp fields are UTC-aware when provided."""
        if v is not None and v.tzinfo is None:
            raise ValueError("Timestamp fields must be UTC-aware (tzinfo must not be None).")
        return v

    @model_validator(mode="after")
    def _validate_state_machine_rules(self) -> Task:
        """Enforce temporal consistency between status and timestamps."""
        # completed_at must be None when PENDING or RUNNING
        if self.status not in _TERMINAL_TASK_STATUSES and self.completed_at is not None:
            raise ValueError(f"completed_at must be None when status={self.status!r}.")

        # completed_at >= started_at
        if (
            self.completed_at is not None
            and self.started_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("completed_at must be >= started_at.")

        # items_failed <= items_processed
        if self.items_failed > self.items_processed:
            raise ValueError(
                f"items_failed ({self.items_failed}) must not exceed "
                f"items_processed ({self.items_processed})."
            )

        return self
