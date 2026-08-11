"""Article-related enumerations."""

from enum import StrEnum


class ArticleStatus(StrEnum):
    """Tracks where an Article is in the processing pipeline.

    An Article is created with status INGESTED and transitions through
    PROCESSING → PROCESSED, or branches to DEDUPLICATED or FAILED.
    Only PROCESSED articles are eligible for inclusion in reports.
    """

    INGESTED = "ingested"
    """Raw — received from source, not yet submitted to the classifier."""

    PROCESSING = "processing"
    """Currently being classified and scored by the processing pipeline."""

    PROCESSED = "processed"
    """Classification, scoring, and entity extraction are complete."""

    DEDUPLICATED = "deduplicated"
    """Identified as a near-duplicate of another article; merged."""

    PUBLISHED = "published"
    """Cited in at least one published report section."""

    FAILED = "failed"
    """Processing failed; see the article's error_message field."""
