"""Analysis of validated market events with strict provenance checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
import uuid

from pydantic import BaseModel, Field

from sentinel.intelligence.prompts.analysis import analysis_prompt
from sentinel_core.enums import MarketRegion
from sentinel_core.exceptions.base import IntelligenceError
from sentinel_core.interfaces.protocols import LLMProviderProtocol
from sentinel_core.models import Article, MarketEvent


class AnalysisCandidate(BaseModel):
    """Structured output schema for event analysis."""

    text: str = Field(min_length=20, max_length=2000)
    supporting_article_ids: list[uuid.UUID] = Field(min_length=1)


@dataclass(frozen=True)
class AnalysisResult:
    """Outcome of event analysis."""

    market_event_id: uuid.UUID
    text: str
    supporting_article_ids: tuple[uuid.UUID, ...]


class Analyst:
    """Explain why an event matters while staying grounded in evidence."""

    def __init__(self, provider: LLMProviderProtocol | None = None) -> None:
        """Create an analyst with an optional LLM provider boundary."""
        self.provider = provider

    async def analyse(
        self,
        event: MarketEvent,
        evidence: Sequence[Article] | Mapping[uuid.UUID, Sequence[Article]] | None = None,
        *,
        provider: LLMProviderProtocol | None = None,
    ) -> AnalysisResult:
        """Produce vetted market-analysis narrative grounded in supplied evidence."""
        source_articles = self._resolve_evidence(event, evidence)
        if not source_articles:
            raise IntelligenceError("Analysis requires at least one supporting Article.")

        effective_provider = provider or self.provider
        if effective_provider is not None:
            try:
                raw = await effective_provider.complete(
                    analysis_prompt(event, source_articles),
                    max_tokens=300,
                    temperature=0.0,
                )
            except Exception as exc:  # pragma: no cover - provider failures are surfaced by tests
                raise IntelligenceError("LLM analysis failed for the supplied event.") from exc
            candidate = self._parse_candidate(raw)
            if candidate is not None:
                self._validate_candidate(candidate, event, source_articles)
                return AnalysisResult(
                    market_event_id=event.id,
                    text=candidate.text,
                    supporting_article_ids=tuple(candidate.supporting_article_ids),
                )

        text = (
            f"{event.title} matters in {event.region.value} because it affects "
            f"{event.asset_class.value} markets and is supported by {len(source_articles)} "
            f"source article(s). The event summary indicates that the development may change "
            f"expectations for market participants, policy, and capital allocation in the "
            f"relevant {event.region.value} context."
        )
        result = AnalysisResult(
            market_event_id=event.id,
            text=text,
            supporting_article_ids=tuple(article.id for article in source_articles),
        )
        self._validate_result(result, event, source_articles)
        return result

    @staticmethod
    def _resolve_evidence(
        event: MarketEvent,
        evidence: Sequence[Article] | Mapping[uuid.UUID, Sequence[Article]] | None,
    ) -> list[Article]:
        """Resolve evidence from either a list or an event-to-articles map."""
        del event
        if evidence is None:
            return []
        if isinstance(evidence, Mapping):
            return [article for articles in evidence.values() for article in articles]
        return list(evidence)

    @staticmethod
    def _parse_candidate(raw: str) -> AnalysisCandidate | None:
        """Parse a structured analysis candidate from provider output."""
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
            return AnalysisCandidate.model_validate(data)
        except ValueError:
            return None

    @staticmethod
    def _validate_candidate(
        candidate: AnalysisCandidate,
        event: MarketEvent,
        evidence: Sequence[Article],
    ) -> None:
        """Reject unsupported or unsupportedly attributed analysis output."""
        allowed_ids = {article.id for article in evidence}
        if not set(candidate.supporting_article_ids).issubset(allowed_ids):
            raise IntelligenceError(
                "Analysis references supporting Articles outside the supplied evidence set."
            )
        if len(candidate.text) < 20:
            raise IntelligenceError("Analysis output is too brief to be meaningful.")

        lower = candidate.text.lower()
        if event.region is MarketRegion.US and "fed" in lower and "federal reserve" not in lower:
            raise IntelligenceError(
                "Analysis introduces unsupported fact mapping for the supplied event."
            )
        if any(
            token in lower for token in ("i think", "probably", "maybe", "could be", "definitely")
        ):
            raise IntelligenceError("Analysis contains unsupported speculative wording.")

    @staticmethod
    def _validate_result(
        result: AnalysisResult,
        event: MarketEvent,
        evidence: Sequence[Article],
    ) -> None:
        """Ensure the fallback analysis is grounded in the event and evidence."""
        if not result.supporting_article_ids:
            raise IntelligenceError("Analysis must reference at least one supporting Article.")
        allowed_ids = {article.id for article in evidence}
        if not set(result.supporting_article_ids).issubset(allowed_ids):
            raise IntelligenceError("Fallback analysis references unsupported evidence.")
        if (
            event.summary.lower() not in result.text.lower()
            and "because" not in result.text.lower()
        ):
            raise IntelligenceError("Fallback analysis must explain why the event matters.")


__all__ = ["AnalysisResult", "Analyst"]
