"""Thin orchestration layer for article processing."""

from __future__ import annotations

from sentinel.processing.classifier import ArticleClassifier
from sentinel.processing.dedup import SemanticDeduplicator
from sentinel.processing.extractor import EntityExtractor
from sentinel.processing.scorer import ArticleScorer
from sentinel_core.enums import ArticleStatus
from sentinel_core.exceptions.base import ProcessingError
from sentinel_core.interfaces.protocols import ProcessorProtocol
from sentinel_core.models import Article, Task


class ArticleProcessor(ProcessorProtocol):
    """Process ingested articles into enriched Article snapshots."""

    def __init__(
        self,
        classifier: ArticleClassifier | None = None,
        scorer: ArticleScorer | None = None,
        extractor: EntityExtractor | None = None,
        deduplicator: SemanticDeduplicator | None = None,
    ) -> None:
        """Create a processor using deterministic, testable stage components."""
        self.classifier = classifier or ArticleClassifier()
        self.scorer = scorer or ArticleScorer()
        self.extractor = extractor or EntityExtractor()
        self.deduplicator = deduplicator or SemanticDeduplicator()

    async def process(self, article: Article, task: Task) -> Article:
        """Classify, score, and deduplicate an Article in one pass."""
        del task

        if article.status in {ArticleStatus.PROCESSED, ArticleStatus.DEDUPLICATED}:
            return article
        if article.status == ArticleStatus.PUBLISHED:
            raise ProcessingError(f"Cannot process a published article: {article.id}")
        if article.status == ArticleStatus.FAILED:
            raise ProcessingError(f"Cannot re-process a failed article: {article.id}")
        if article.status not in {ArticleStatus.INGESTED, ArticleStatus.PROCESSING}:
            raise ProcessingError(f"Unsupported article status for processing: {article.status!r}")

        processing_article = article.model_copy(update={"status": ArticleStatus.PROCESSING})
        classification = await self.classifier.classify(processing_article)
        score_result = await self.scorer.score(processing_article)
        await self.extractor.extract(processing_article)

        candidate = processing_article.model_copy(
            update={
                "status": ArticleStatus.PROCESSED,
                "asset_class": classification.asset_class,
                "region": classification.region,
                "sector": classification.sector,
                "sentiment": classification.sentiment,
                "sentiment_confidence": classification.sentiment_confidence,
                "importance_score": score_result.importance_score,
                "importance_confidence": score_result.importance_confidence,
            }
        )

        duplicate = await self.deduplicator.deduplicate(candidate, [])
        if duplicate is not None:
            return candidate.model_copy(
                update={
                    "status": ArticleStatus.DEDUPLICATED,
                    "duplicate_of_id": duplicate.id,
                }
            )

        return candidate


__all__ = ["ArticleProcessor"]
