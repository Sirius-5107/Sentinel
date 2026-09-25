"""Importance scoring for Phase 3 article processing."""

from __future__ import annotations

from dataclasses import dataclass

from sentinel_core.models import Article
from sentinel_core.types import ConfidenceScore, ImportanceScore


@dataclass(frozen=True)
class ScoreResult:
    """Deterministic score output used by the processing pipeline."""

    importance_score: ImportanceScore
    importance_confidence: ConfidenceScore


class ArticleScorer:
    """Score article importance using a transparent rule set."""

    @staticmethod
    async def score(article: Article) -> ScoreResult:
        """Compute importance from the raw article evidence."""
        text = "\n".join(part for part in (article.title, article.summary, article.content) if part)
        lower = text.lower()

        signal_hits = 0
        for token in (
            "rate",
            "inflation",
            "fed",
            "central bank",
            "earnings",
            "merger",
            "bankruptcy",
            "outlook",
            "forecast",
            "policy",
            "sanction",
            "recession",
            "warning",
            "growth",
        ):
            if token in lower:
                signal_hits += 1

        length_factor = min(3.0, len(text) / 1500)
        score = 2.0 + (0.8 * signal_hits) + length_factor
        score = max(0.0, min(10.0, score))

        confidence = 0.45 + min(0.4, 0.05 * signal_hits) + min(0.1, length_factor / 20)
        confidence = max(0.0, min(1.0, confidence))

        if "market region" in lower:
            score += 0.2
        score = max(0.0, min(10.0, score))

        return ScoreResult(
            importance_score=float(round(score, 2)),
            importance_confidence=float(round(confidence, 4)),
        )


__all__ = ["ArticleScorer", "ScoreResult"]
