"""Event synthesis for the Phase 4 intelligence layer."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import uuid

from pydantic import BaseModel, Field, field_validator

from sentinel.intelligence.prompts.event_synthesis import event_synthesis_prompt
from sentinel_core.enums import AssetClass, EventSeverity, MarketRegion, Sector, Sentiment
from sentinel_core.exceptions.base import IntelligenceError
from sentinel_core.interfaces.protocols import LLMProviderProtocol
from sentinel_core.models import Article, MarketEvent
from sentinel_core.types import ConfidenceScore, ImportanceScore


class MarketEventCandidate(BaseModel):
    """Application-layer candidate schema for LLM-generated event synthesis."""

    title: str = Field(min_length=1, max_length=300)
    summary: str = Field(min_length=100, max_length=2000)
    asset_class: AssetClass
    region: MarketRegion
    sector: Sector | None = None
    severity: EventSeverity
    sentiment: Sentiment
    sentiment_confidence: ConfidenceScore
    importance_score: ImportanceScore
    importance_confidence: ConfidenceScore
    occurred_at: datetime
    source_article_ids: list[uuid.UUID] = Field(min_length=1)

    @field_validator("occurred_at")
    @classmethod
    def _normalise_occurred_at(cls, value: datetime) -> datetime:
        """Normalise candidate timestamps to UTC and reject naive values."""
        if value.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware.")
        return value.astimezone(UTC)

    @field_validator("source_article_ids")
    @classmethod
    def _validate_provenance(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        """Require a candidate to have at least one article support record."""
        if not value:
            raise ValueError("MarketEvent candidates require at least one source Article.")
        return value


@dataclass(frozen=True)
class SynthesisedMarketEvent:
    """A validated market event plus the provenance metadata used by the app layer."""

    market_event: MarketEvent
    source_article_ids: tuple[uuid.UUID, ...]


class EventSynthesiser:
    """Group processed articles into validated market events."""

    def __init__(self, provider: LLMProviderProtocol | None = None) -> None:
        """Create a synthesiser with an optional LLM provider boundary."""
        self.provider = provider
        self._provenance: dict[uuid.UUID, tuple[uuid.UUID, ...]] = {}

    @property
    def provenance(self) -> dict[uuid.UUID, tuple[uuid.UUID, ...]]:
        """Return the most recent event provenance map."""
        return dict(self._provenance)

    async def synthesise(
        self,
        articles: Sequence[Article],
        *,
        provider: LLMProviderProtocol | None = None,
    ) -> list[MarketEvent]:
        """Create a validated MarketEvent for each deterministic evidence group."""
        if not articles:
            return []

        self._provenance.clear()
        grouped = self._group_articles(articles)
        events: list[MarketEvent] = []
        for group in grouped:
            synthesised = await self._synthesise_group(group, provider=provider)
            events.append(synthesised.market_event)
            self._provenance[synthesised.market_event.id] = synthesised.source_article_ids
        return events

    def _group_articles(self, articles: Sequence[Article]) -> list[list[Article]]:
        """Deterministically group related articles by region and asset class."""
        buckets: dict[
            tuple[AssetClass | None, MarketRegion | None, Sector | None],
            list[Article],
        ] = {}
        for article in sorted(
            articles,
            key=lambda item: (item.published_at or item.fetched_at, item.id),
        ):
            key = (
                article.asset_class,
                article.region,
                article.sector,
            )
            buckets.setdefault(key, []).append(article)
        return [
            sorted(group, key=lambda item: item.published_at or item.fetched_at)
            for group in buckets.values()
        ]

    async def _synthesise_group(
        self,
        group: Sequence[Article],
        *,
        provider: LLMProviderProtocol | None = None,
    ) -> SynthesisedMarketEvent:
        """Validate one group into a single MarketEvent."""
        source_ids = tuple(article.id for article in group)
        if not source_ids:
            raise IntelligenceError(
                "Cannot construct a MarketEvent without source Article provenance."
            )

        effective_provider = provider or self.provider
        prompt = event_synthesis_prompt(group)
        candidate = None
        if effective_provider is not None:
            try:
                raw = await effective_provider.complete(
                    prompt,
                    max_tokens=400,
                    temperature=0.0,
                )
            except Exception as exc:  # pragma: no cover - provider failures are surfaced by tests
                raise IntelligenceError(
                    "LLM event synthesis failed for the supplied articles."
                ) from exc
            candidate = self._parse_candidate(raw)

        if candidate is None:
            candidate = self._fallback_candidate(group)

        valid = self._validate_candidate(candidate, group)
        event = MarketEvent(
            title=valid.title,
            summary=valid.summary,
            asset_class=valid.asset_class,
            region=valid.region,
            sector=valid.sector,
            severity=valid.severity,
            sentiment=valid.sentiment,
            sentiment_confidence=valid.sentiment_confidence,
            importance_score=valid.importance_score,
            importance_confidence=valid.importance_confidence,
            occurred_at=valid.occurred_at,
        )
        return SynthesisedMarketEvent(market_event=event, source_article_ids=source_ids)

    @staticmethod
    def _fallback_candidate(group: Sequence[Article]) -> MarketEventCandidate:
        """Create a deterministic fallback event from the evidence."""
        first = group[0]
        asset_class = first.asset_class or AssetClass.OTHER
        region = first.region or MarketRegion.GLOBAL
        sector = first.sector or Sector.UNKNOWN
        summary = (
            f"{first.title}. The development described across the supporting article "
            f"evidence is material for {region.value} {asset_class.value} markets "
            f"because it affects the {sector.value} landscape and may change "
            "expectations for market participants."
        )
        if len(summary) < 100:
            summary = (
                f"{summary} Market participants are tracking the implications of "
                "this development closely. Market participants are tracking the "
                "implications of this development closely."
            )
        return MarketEventCandidate(
            title=first.title,
            summary=summary,
            asset_class=asset_class,
            region=region,
            sector=sector,
            severity=EventSeverity.MEDIUM,
            sentiment=Sentiment.NEUTRAL,
            sentiment_confidence=0.5,
            importance_score=4.0,
            importance_confidence=0.5,
            occurred_at=(first.published_at or first.fetched_at).astimezone(UTC),
            source_article_ids=[item.id for item in group],
        )

    @staticmethod
    def _parse_candidate(raw: str) -> MarketEventCandidate | None:
        """Parse an LLM-produced JSON response into a validated candidate schema."""
        payload = raw.strip()
        if not payload:
            return None
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        try:
            return MarketEventCandidate.model_validate(data)
        except ValueError:
            return None

    @staticmethod
    def _validate_candidate(
        candidate: MarketEventCandidate,
        group: Sequence[Article],
    ) -> MarketEventCandidate:
        """Reject unsupported or inadequately evidenced events before domain construction."""
        if not group:
            raise IntelligenceError("A MarketEvent must have at least one source Article.")
        source_ids = {article.id for article in group}
        candidate_ids = set(candidate.source_article_ids)
        if not source_ids.issuperset(candidate_ids):
            raise IntelligenceError(
                "Candidate provenance references Article IDs not present in the evidence set."
            )
        if any(item not in source_ids for item in candidate_ids):
            raise IntelligenceError(
                "Candidate provenance must be limited to the supplied Articles."
            )
        if len(candidate.summary) < 100:
            raise IntelligenceError(
                "MarketEvent summary must exceed the minimum evidence threshold."
            )
        summary_text = candidate.summary.lower()
        if any(token in summary_text for token in ("i think", "probably", "maybe", "possibly")):
            raise IntelligenceError(
                "MarketEvent summary includes unsupported speculative language."
            )
        return candidate


__all__ = ["EventSynthesiser", "MarketEventCandidate", "SynthesisedMarketEvent"]
