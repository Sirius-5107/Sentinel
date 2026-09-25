"""Thin orchestration layer for article processing."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
import inspect

from sentinel.processing.classifier import ArticleClassifier, ClassificationResult
from sentinel.processing.dedup import SemanticDeduplicator
from sentinel.processing.extractor import EntityExtractor
from sentinel.processing.scorer import ArticleScorer, ScoreResult
from sentinel_core.enums import ArticleStatus
from sentinel_core.exceptions.base import ProcessingError
from sentinel_core.interfaces.protocols import ProcessorProtocol
from sentinel_core.models import Article, Task

CandidateSequence = Sequence[Article]
CandidateProvider = Callable[[Article], CandidateSequence | Awaitable[CandidateSequence]]


class ArticleProcessor(ProcessorProtocol):
    """Process ingested articles into enriched Article snapshots."""

    def __init__(
        self,
        classifier: ArticleClassifier | None = None,
        scorer: ArticleScorer | None = None,
        extractor: EntityExtractor | None = None,
        deduplicator: SemanticDeduplicator | None = None,
        candidate_provider: CandidateProvider | None = None,
    ) -> None:
        """Create a processor using deterministic, testable stage components."""
        self.classifier = classifier or ArticleClassifier()
        self.scorer = scorer or ArticleScorer()
        self.extractor = extractor or EntityExtractor()
        self.deduplicator = deduplicator or SemanticDeduplicator()
        self.candidate_provider = candidate_provider

    async def _get_candidates(self, article: Article) -> Sequence[Article]:
        """Resolve candidate articles for deduplication from optional dependency injection."""
        if self.candidate_provider is None:
            return []
        candidates = self.candidate_provider(article)
        if inspect.isawaitable(candidates):
            candidates = await candidates
        return list(candidates)

    @staticmethod
    def _build_processed_article(
        article: Article,
        *,
        classification: ClassificationResult,
        score_result: ScoreResult,
    ) -> Article:
        """Construct a validated processed Article without mutating the original snapshot."""
        data = article.model_dump(mode="python")
        data["status"] = ArticleStatus.PROCESSED
        data["asset_class"] = classification.asset_class
        data["region"] = classification.region
        data["sector"] = classification.sector
        data["sentiment"] = classification.sentiment
        data["sentiment_confidence"] = classification.sentiment_confidence
        data["importance_score"] = score_result.importance_score
        data["importance_confidence"] = score_result.importance_confidence
        data["duplicate_of_id"] = None
        return Article(**data)

    @staticmethod
    def _build_duplicate_article(
        article: Article,
        *,
        canonical: Article,
        classification: ClassificationResult,
        score_result: ScoreResult,
    ) -> Article:
        """Construct a validated deduplicated Article while preserving raw evidence."""
        data = article.model_dump(mode="python")
        data["status"] = ArticleStatus.DEDUPLICATED
        data["asset_class"] = classification.asset_class
        data["region"] = classification.region
        data["sector"] = classification.sector
        data["sentiment"] = classification.sentiment
        data["sentiment_confidence"] = classification.sentiment_confidence
        data["importance_score"] = score_result.importance_score
        data["importance_confidence"] = score_result.importance_confidence
        data["duplicate_of_id"] = canonical.id
        return Article(**data)

    async def process(self, article: Article, task: Task) -> Article:
        """Classify, score, extract entities, and deduplicate an Article in one pass."""
        del task

        if article.status in {ArticleStatus.PROCESSED, ArticleStatus.DEDUPLICATED}:
            return article
        if article.status == ArticleStatus.PUBLISHED:
            raise ProcessingError(f"Cannot process a published article: {article.id}")
        if article.status == ArticleStatus.FAILED:
            raise ProcessingError(f"Cannot re-process a failed article: {article.id}")
        if article.status not in {ArticleStatus.INGESTED, ArticleStatus.PROCESSING}:
            raise ProcessingError(f"Unsupported article status for processing: {article.status!r}")

        processing_data = article.model_dump(mode="python")
        processing_data["status"] = ArticleStatus.PROCESSING
        processing_article = Article(**processing_data)
        classification = await self.classifier.classify(processing_article)
        score_result = await self.scorer.score(processing_article)
        await self.extractor.extract(processing_article)

        processed = self._build_processed_article(
            processing_article,
            classification=classification,
            score_result=score_result,
        )

        candidates = await self._get_candidates(processed)
        canonical = await self.deduplicator.deduplicate(processed, candidates)
        if canonical is not None:
            return self._build_duplicate_article(
                processed,
                canonical=canonical,
                classification=classification,
                score_result=score_result,
            )

        return processed


__all__ = ["ArticleProcessor"]
