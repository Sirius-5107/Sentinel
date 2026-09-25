"""Semantic deduplication helper for Phase 3 processing."""

from __future__ import annotations

from collections.abc import Sequence
import math

from sentinel_core.enums import ArticleStatus
from sentinel_core.interfaces.protocols import EmbeddingProviderProtocol
from sentinel_core.models import Article


class SemanticDeduplicator:
    """Determine duplicate relationships using deterministic similarity logic."""

    def __init__(self, provider: EmbeddingProviderProtocol | None = None) -> None:
        """Create a deduplicator optionally backed by an embedding provider."""
        self.provider = provider

    async def deduplicate(
        self,
        article: Article,
        candidates: Sequence[Article],
        provider: EmbeddingProviderProtocol | None = None,
    ) -> Article | None:
        """Return the canonical article for a duplicate or None when article is unique."""
        effective_provider = provider or self.provider
        if article.status == ArticleStatus.DEDUPLICATED:
            return article

        for candidate in candidates:
            if candidate.id == article.id:
                continue

            if effective_provider is not None and hasattr(effective_provider, "embed"):
                try:
                    article_embedding = await effective_provider.embed(
                        self._normalise_text(article)
                    )
                    candidate_embedding = await effective_provider.embed(
                        self._normalise_text(candidate)
                    )
                    similarity = self._cosine_similarity(article_embedding, candidate_embedding)
                    if similarity >= 0.88:
                        return candidate
                except Exception:
                    # Fall back to deterministic keyword-based overlap below.
                    _ = None

            if self._hash_signature(article) == self._hash_signature(candidate):
                return candidate

            if self._word_overlap(article, candidate) >= 0.25:
                return candidate

        return None

    @staticmethod
    def _normalise_text(article: Article) -> str:
        return "\n".join(part for part in (article.title, article.summary, article.content) if part)

    @staticmethod
    def _hash_signature(article: Article) -> tuple[str, ...]:
        text = SemanticDeduplicator._normalise_text(article).lower()
        tokens = [token for token in text.replace("/", " ").split() if len(token) > 3]
        return tuple(sorted(set(tokens)))

    @staticmethod
    def _word_overlap(article: Article, candidate: Article) -> float:
        left = set(SemanticDeduplicator._hash_signature(article))
        right = set(SemanticDeduplicator._hash_signature(candidate))
        if not left or not right:
            return 0.0
        overlap = len(left & right) / max(1, len(left | right))
        return float(overlap)

    @staticmethod
    def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
        if not left or not right:
            return 0.0
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(a * a for a in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot / (left_norm * right_norm)


__all__ = ["SemanticDeduplicator"]
