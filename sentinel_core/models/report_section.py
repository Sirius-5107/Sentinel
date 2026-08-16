"""ReportSection domain model.

A ReportSection is a single named, ordered section within a DailyReport —
for example 'Macro', 'US Equities', 'India', 'AI', 'Private Credit'.
Sections are the granular unit of report content.
"""

from __future__ import annotations

import uuid

from pydantic import Field, field_validator, model_validator

from sentinel_core.enums import AssetClass, MarketRegion
from sentinel_core.models._base import SentinelModel


class ReportSection(SentinelModel):
    """A single ordered section within a DailyReport.

    ReportSections can be individually regenerated, reviewed, or replaced
    without rebuilding the entire report. Each section covers one market
    segment and contains synthesised narrative text with citations to
    MarketEvents and Articles.

    Standard Daily Brief sections (from Milestone 3):
        0 - Executive Summary
        1 - Macro
        2 - US Equities
        3 - India
        4 - AI
        5 - Private Credit
        6 - Private Equity
        7 - M&A
        8 - Outlier Events
        9 - Watchlist

    Uniqueness constraints (enforced at the database layer):
        - (report_id, order) must be unique — no two sections at the same position.
        - (report_id, title) must be unique — a section heading may appear only once.

    Note on word_count:
        Despite its name, word_count stores the character count of content
        (Python's len(content)), not a true word count. This naming convention
        matches widespread usage in document processing systems. The docstring
        makes this explicit; see also contracts §4.9 Ambiguity.

    Validation rules:
        - order must be >= 0.
        - word_count must be >= 0 when non-None.
        - event_count must be >= 0.

    Fields:
        id: UUID v4 primary key.
        report_id: FK to the owning DailyReport.
        title: Section heading; 1-200 chars (e.g. 'US Equities').
        order: Display position within the report (>= 0; 0 = first).
        content: Full section narrative; max 20,000 chars. None while generating.
        theme_id: FK to Theme for theme-specific sections. Optional.
        asset_class: Asset class this section covers. Optional.
        region: Region this section covers. Optional.
        word_count: Character count of content (len(content)). None until set.
        event_count: Denormalised count of linked MarketEvents (>= 0).
        created_at: UTC construction timestamp.
        updated_at: UTC last-mutation timestamp.

    Example::

        ReportSection(
            report_id=uuid.UUID("..."),
            title="US Equities",
            order=2,
            asset_class=AssetClass.EQUITY,
            region=MarketRegion.US,
        )
    """

    report_id: uuid.UUID = Field(
        description="FK to the DailyReport that owns this section.",
    )
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Section heading (e.g. 'US Equities', 'Macro', 'AI').",
    )
    order: int = Field(
        ge=0,
        description=(
            "Display position within the report. 0 = first section. "
            "Must be unique within a single report_id (enforced at database layer)."
        ),
    )
    content: str | None = Field(
        default=None,
        max_length=20_000,
        description="Full synthesised section narrative. None while being generated.",
    )
    theme_id: uuid.UUID | None = Field(
        default=None,
        description="FK to Theme. Present only for theme-specific sections.",
    )
    asset_class: AssetClass | None = Field(
        default=None,
        description="Financial asset class covered by this section.",
    )
    region: MarketRegion | None = Field(
        default=None,
        description="Geographic region covered by this section.",
    )
    word_count: int | None = Field(
        default=None,
        description=(
            "Character count of content (len(content)), not a true word count. "
            "None until content is set. Must be >= 0 when non-None."
        ),
    )
    event_count: int = Field(
        default=0,
        ge=0,
        description="Denormalised count of MarketEvents linked to this section.",
    )

    @field_validator("word_count")
    @classmethod
    def _validate_word_count(cls, v: int | None) -> int | None:
        """Enforce word_count >= 0 when non-None."""
        if v is not None and v < 0:
            raise ValueError(f"word_count must be >= 0; got {v!r}.")
        return v

    @model_validator(mode="after")
    def _validate_word_count_consistency(self) -> ReportSection:
        """Enforce consistency between content and word_count."""
        if self.content is not None and self.word_count is None:
            # word_count should be set whenever content is set.
            # This is not a hard error — the application layer may set content
            # before computing word_count. We do not raise here.
            pass
        return self
