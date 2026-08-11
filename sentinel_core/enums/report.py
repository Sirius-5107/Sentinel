"""Report and pipeline enumerations."""

from enum import StrEnum


class ReportType(StrEnum):
    """Classifies the format and cadence of a DailyReport.

    Only DAILY_BRIEF is used in Phase 3. The remaining values are
    pre-declared to avoid a future migration when Phase 6 is implemented.
    """

    DAILY_BRIEF = "daily_brief"
    """Standard daily intelligence brief; produced once per day."""

    WEEKLY_OUTLOOK = "weekly_outlook"
    """Weekly synthesis report (Phase 6)."""

    MONTHLY_OUTLOOK = "monthly_outlook"
    """Monthly strategic review (Phase 6)."""

    COMPANY_DOSSIER = "company_dossier"
    """Company deep-dive research document (Phase 6)."""

    THEME_REPORT = "theme_report"
    """Investment theme analysis report (Phase 6)."""

    SECTOR_REPORT = "sector_report"
    """Sector analysis report (Phase 6)."""


class ReportStatus(StrEnum):
    """Publication state of a DailyReport.

    A report progresses from DRAFT through APPROVED before being PUBLISHED.
    FAILED indicates that a publication attempt was made but did not succeed.
    """

    DRAFT = "draft"
    """Being assembled; sections may be incomplete."""

    REVIEW = "review"
    """Assembly complete; awaiting quality review."""

    APPROVED = "approved"
    """Quality review passed; ready for publication."""

    PUBLISHED = "published"
    """Sent to all configured channels (e.g. Notion)."""

    FAILED = "failed"
    """Publication attempt failed; see error_message."""


class PipelineStatus(StrEnum):
    """Execution state of a PipelineRun.

    PARTIAL indicates the run completed but with non-fatal errors;
    some articles or events may not have been processed.
    """

    PENDING = "pending"
    """Scheduled; not yet started."""

    RUNNING = "running"
    """Currently executing."""

    SUCCESS = "success"
    """Completed without errors."""

    PARTIAL = "partial"
    """Completed with non-fatal errors; output may be incomplete."""

    FAILED = "failed"
    """Terminated due to a fatal error; output is unreliable."""


class TaskStatus(StrEnum):
    """Execution state of an individual Task within a PipelineRun.

    SKIPPED indicates the task was not attempted because a dependency
    task had already failed.
    """

    PENDING = "pending"
    """Queued; not yet started."""

    RUNNING = "running"
    """Currently executing."""

    SUCCESS = "success"
    """Completed without errors."""

    FAILED = "failed"
    """Terminated due to an error; see error_message."""

    SKIPPED = "skipped"
    """Not attempted because a dependency task failed."""
