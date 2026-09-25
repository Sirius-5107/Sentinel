"""Daily brief assembly with deterministic ordering and provenance tracking."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
import uuid

from sentinel_core.enums import AssetClass, MarketRegion, ReportStatus, ReportType
from sentinel_core.models import DailyReport, MarketEvent, ReportSection


@dataclass(frozen=True)
class DailyBriefResult:
    """Result of assembling a daily brief."""

    report: DailyReport
    sections: tuple[ReportSection, ...]
    section_event_ids: dict[uuid.UUID, tuple[uuid.UUID, ...]]
    event_article_ids: dict[uuid.UUID, tuple[uuid.UUID, ...]]


class DailyBriefAssembler:
    """Assemble daily report sections from validated market events."""

    @staticmethod
    def assemble(
        events: Sequence[MarketEvent],
        *,
        coverage_date: date | None = None,
        title: str | None = None,
        event_provenance: Mapping[uuid.UUID, Sequence[uuid.UUID]] | None = None,
    ) -> DailyBriefResult:
        """Construct a deterministic DailyReport plus the sections it contains."""
        report_date = coverage_date or datetime.now(tz=UTC).date()
        if not events:
            report = DailyReport(
                coverage_date=report_date,
                report_type=ReportType.DAILY_BRIEF,
                status=ReportStatus.DRAFT,
                title=title or "Daily Brief",
                executive_summary=(
                    "No validated market events were identified for this coverage window."
                ),
                article_count=0,
                event_count=0,
            )
            return DailyBriefResult(
                report=report,
                sections=(),
                section_event_ids={},
                event_article_ids={},
            )

        grouped: dict[tuple[AssetClass, MarketRegion], list[MarketEvent]] = defaultdict(list)
        for event in sorted(
            events,
            key=lambda item: (-item.importance_score, item.occurred_at, item.title),
        ):
            grouped[(event.asset_class, event.region)].append(event)

        default_title = title or "Daily Brief"
        report = DailyReport(
            report_type=ReportType.DAILY_BRIEF,
            status=ReportStatus.DRAFT,
            coverage_date=report_date,
            title=default_title,
            executive_summary=(
                "Deterministic market brief assembled from validated event synthesis."
            ),
            article_count=0,
            event_count=len(events),
        )

        sections: list[ReportSection] = []
        section_event_ids: dict[uuid.UUID, tuple[uuid.UUID, ...]] = {}
        event_article_ids: dict[uuid.UUID, tuple[uuid.UUID, ...]] = {}
        for order, ((asset_class, region), region_events) in enumerate(
            sorted(
                grouped.items(),
                key=lambda item: (item[0][1].value, item[0][0].value),
            )
        ):
            title = DailyBriefAssembler._section_title(asset_class, region)
            narrative = "\n\n".join(
                f"{event.title}: {event.summary}"
                for event in sorted(region_events, key=lambda item: item.occurred_at)
            )
            section = ReportSection(
                report_id=report.id,
                title=title,
                order=order,
                content=narrative[:20_000],
                asset_class=asset_class,
                region=region,
                event_count=len(region_events),
            )
            sections.append(section)
            section_event_ids[section.id] = tuple(event.id for event in region_events)
            for event in region_events:
                event_article_ids[event.id] = tuple((event_provenance or {}).get(event.id, ()))

        report = report.model_copy(
            update={
                "title": default_title,
                "executive_summary": DailyBriefAssembler._executive_summary(events),
                "article_count": sum(
                    len(article_ids) for article_ids in event_article_ids.values()
                ),
                "event_count": len(events),
            }
        )
        return DailyBriefResult(
            report=report,
            sections=tuple(sections),
            section_event_ids=section_event_ids,
            event_article_ids=event_article_ids,
        )

    @staticmethod
    def _section_title(asset_class: AssetClass, region: MarketRegion) -> str:
        """Generate a deterministic section title from event metadata."""
        if asset_class == AssetClass.MACRO:
            return "Macro"
        if region == MarketRegion.US and asset_class == AssetClass.EQUITY:
            return "US Equities"
        if region == MarketRegion.INDIA:
            return "India"
        if asset_class == AssetClass.CRYPTO:
            return "Crypto"
        if asset_class == AssetClass.PRIVATE_CREDIT:
            return "Private Credit"
        if asset_class == AssetClass.PRIVATE_EQUITY:
            return "Private Equity"
        if asset_class == AssetClass.FIXED_INCOME:
            return "Fixed Income"
        if asset_class == AssetClass.COMMODITIES:
            return "Commodities"
        return f"{region.value.title()} {asset_class.value.replace('_', ' ').title()}"

    @staticmethod
    def _executive_summary(events: Sequence[MarketEvent]) -> str:
        """Compose a brief summary from the highest-impact validated events."""
        top_events = sorted(events, key=lambda item: (-item.importance_score, item.occurred_at))[:3]
        if not top_events:
            return "No validated market events were identified for this coverage window."
        summaries = ", ".join(event.title for event in top_events)
        return (
            "This brief is driven by the most material developments in the "
            f"coverage window: {summaries}. The current event set highlights "
            f"{len(events)} validated market developments with relevance to "
            f"{', '.join(sorted({event.region.value for event in events}))}."
        )


__all__ = ["DailyBriefAssembler", "DailyBriefResult"]
