"""Unit tests for the Phase 3 processing layer."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from typing import cast
import uuid

import pytest

from sentinel.processing.classifier import ArticleClassifier
from sentinel.processing.dedup import SemanticDeduplicator
from sentinel.processing.extractor import EntityExtractor, ExtractedEntity
from sentinel.processing.processor import ArticleProcessor
from sentinel.processing.scorer import ArticleScorer
from sentinel_core.enums import ArticleStatus, AssetClass, Sentiment
from sentinel_core.exceptions.base import ProcessingError
from sentinel_core.models import Article, Task
from sentinel_core.types import Url


def _make_article(
    title: str,
    content: str | None = None,
    *,
    url_suffix: str | None = None,
) -> Article:
    suffix = url_suffix or title.lower().replace(" ", "-")
    content_text = content or title
    return Article(
        source_id=uuid.uuid4(),
        title=title,
        url=Url(f"https://example.com/{suffix}"),
        content=content_text,
        summary=f"Summary for {title}",
        published_at=datetime.now(tz=UTC),
        fetched_at=datetime.now(tz=UTC),
        language="en",
        status=ArticleStatus.INGESTED,
        content_hash=hashlib.sha256(f"{title}https://example.com/{suffix}".encode()).hexdigest(),
    )


class _SyncCandidateProvider:
    def __init__(self, candidates: list[Article]) -> None:
        self.candidates = candidates
        self.calls: list[uuid.UUID] = []

    def __call__(self, article: Article) -> list[Article]:
        self.calls.append(article.id)
        return self.candidates


class _AsyncCandidateProvider:
    def __init__(self, candidates: list[Article]) -> None:
        self.candidates = candidates
        self.calls: list[uuid.UUID] = []

    async def __call__(self, article: Article) -> list[Article]:
        self.calls.append(article.id)
        return self.candidates


class _SpyExtractor:
    def __init__(self) -> None:
        self.calls: list[uuid.UUID] = []

    async def extract(self, article: Article) -> list[ExtractedEntity]:
        self.calls.append(article.id)
        return []


class _FailingLLMProvider:
    async def complete(
        self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.0
    ) -> str:
        del prompt, max_tokens, temperature
        raise RuntimeError("provider failed")


class _MalformedLLMProvider:
    async def complete(
        self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.0
    ) -> str:
        del prompt, max_tokens, temperature
        return "{not-json"


class _FailingEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        del text
        raise RuntimeError("embedding failed")


class _MalformedEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        del text
        return [float("nan"), float("nan")]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_classifier_classifies_macro_article() -> None:
    article = _make_article(
        "Fed holds rates steady as inflation remains sticky",
        "The Federal Reserve kept borrowing costs unchanged while inflation stayed elevated.",
    )

    result = await ArticleClassifier().classify(article)

    assert result.asset_class == AssetClass.MACRO
    assert result.sentiment in {Sentiment.BULLISH, Sentiment.BEARISH, Sentiment.NEUTRAL}
    assert 0.0 <= float(result.sentiment_confidence) <= 1.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scorer_produces_deterministic_importance() -> None:
    article = _make_article(
        "ECB warns of recession risk as inflation cools and growth slows",
        "The European Central Bank signaled concern over inflation, growth and recession risk.",
    )

    result = await ArticleScorer.score(article)

    assert 0.0 <= float(result.importance_score) <= 10.0
    assert 0.0 <= float(result.importance_confidence) <= 1.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extractor_collects_named_entities() -> None:
    article = _make_article(
        "Apple and Elon Musk meet Federal Reserve officials in Washington",
        "Apple executives discussed policy with Elon Musk and the Federal Reserve.",
    )

    entities = await EntityExtractor.extract(article)
    names = {entity.name for entity in entities}

    assert "Apple" in names
    assert "Elon Musk" in names
    assert "Federal Reserve" in names


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deduplicator_marks_semantic_duplicate() -> None:
    article = _make_article(
        "Fed holds rates while inflation stays elevated",
        "The Federal Reserve expects inflation to remain high and keeps rates unchanged.",
    )
    candidate = _make_article(
        "Fed keeps rates unchanged as inflation remains elevated",
        "The Federal Reserve keeps interest rates unchanged as inflation remains high.",
        url_suffix="fed-keeps-rates-unchanged",
    )

    result = await SemanticDeduplicator().deduplicate(article, [candidate])

    assert result is candidate


@pytest.mark.unit
@pytest.mark.asyncio
async def test_processor_processes_article_and_preserves_raw_fields() -> None:
    article = _make_article(
        "Fed says inflation remains sticky after rate decision",
        "Officials said inflation remained sticky after the latest rate decision.",
        url_suffix="fed-rate-decision",
    )
    task = Task(pipeline_run_id=uuid.uuid4(), name="process.classify")

    processed = await ArticleProcessor().process(article, task)

    assert processed.status == ArticleStatus.PROCESSED
    assert processed.asset_class is not None
    assert processed.region is not None
    assert processed.sentiment is not None
    assert processed.sentiment_confidence is not None
    assert processed.importance_score is not None
    assert processed.importance_confidence is not None
    assert processed.title == article.title
    assert processed.url == article.url
    assert processed.content == article.content
    assert processed.summary == article.summary


@pytest.mark.unit
@pytest.mark.asyncio
async def test_processor_uses_injected_sync_candidate_provider() -> None:
    article = _make_article(
        "Fed keeps rates unchanged as inflation remains elevated",
        "The Federal Reserve keeps rates unchanged as inflation remains elevated.",
        url_suffix="fed-keeps-rates",
    )
    candidate = _make_article(
        "Fed holds rates while inflation stays elevated",
        "The Federal Reserve keeps rates unchanged while inflation remains elevated.",
        url_suffix="fed-holds-rates",
    )
    provider = _SyncCandidateProvider([candidate])

    processed = await ArticleProcessor(candidate_provider=provider).process(
        article, Task(pipeline_run_id=uuid.uuid4(), name="process.classify")
    )

    assert provider.calls == [article.id]
    assert processed.status == ArticleStatus.DEDUPLICATED
    assert processed.duplicate_of_id == candidate.id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_processor_uses_injected_async_candidate_provider() -> None:
    article = _make_article(
        "Bank earnings beat estimates as growth accelerates",
        "Bank earnings beat estimates as growth accelerated across the sector.",
        url_suffix="bank-earnings",
    )
    candidate = _make_article(
        "Bank earnings outperform estimates as growth accelerates",
        "Banks reported better-than-expected earnings and accelerating growth.",
        url_suffix="bank-earnings-outperform",
    )
    provider = _AsyncCandidateProvider([candidate])

    processed = await ArticleProcessor(candidate_provider=provider).process(
        article, Task(pipeline_run_id=uuid.uuid4(), name="process.classify")
    )

    assert provider.calls == [article.id]
    assert processed.status == ArticleStatus.DEDUPLICATED
    assert processed.duplicate_of_id == candidate.id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_processor_keeps_unique_article_processed() -> None:
    article = _make_article(
        "Shipping costs rise sharply after supply chain disruption",
        "Shipping margins came under pressure after a severe supply chain disruption.",
        url_suffix="shipping-costs",
    )
    processor = ArticleProcessor(candidate_provider=lambda _article: [])

    processed = await processor.process(
        article, Task(pipeline_run_id=uuid.uuid4(), name="process.classify")
    )

    assert processed.status == ArticleStatus.PROCESSED
    assert processed.duplicate_of_id is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_classifier_provider_exception_raises_processing_error() -> None:
    article = _make_article(
        "Fed signals slower cuts as inflation cools",
        "The Federal Reserve may slow the pace of rate cuts as inflation cools.",
    )

    with pytest.raises(ProcessingError):
        await ArticleClassifier(provider=_FailingLLMProvider()).classify(article)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_classifier_malformed_provider_response_falls_back() -> None:
    article = _make_article(
        "Fed rate decision lifts growth outlook in the US",
        "The Fed moved to support growth as the US economy stayed resilient.",
    )

    result = await ArticleClassifier(provider=_MalformedLLMProvider()).classify(article)

    assert result.asset_class is not None
    assert result.sentiment is not None
    assert 0.0 <= float(result.sentiment_confidence) <= 1.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_processor_preserves_raw_fields_and_invariants() -> None:
    article = _make_article(
        "Inflation cools while the Fed stays patient",
        "Officials said inflation has cooled while the Fed remains patient.",
        url_suffix="fed-patient",
    )
    task = Task(pipeline_run_id=uuid.uuid4(), name="process.classify")

    processed = await ArticleProcessor().process(article, task)

    assert processed.title == article.title
    assert processed.url == article.url
    assert processed.content == article.content
    assert processed.summary == article.summary
    assert processed.published_at == article.published_at
    assert processed.fetched_at == article.fetched_at
    assert processed.language == article.language
    assert processed.content_hash == article.content_hash
    assert processed.duplicate_of_id is None
    assert (processed.sentiment is None) == (processed.sentiment_confidence is None)
    assert (processed.importance_score is None) == (processed.importance_confidence is None)
    assert processed.status == ArticleStatus.PROCESSED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_processor_invokes_entity_extractor() -> None:
    article = _make_article(
        "Apple and Elon Musk brief the Federal Reserve on AI investment",
        "Apple executives met Elon Musk and Federal Reserve officials to discuss AI investment.",
    )
    extractor = _SpyExtractor()
    processor = ArticleProcessor(extractor=cast("EntityExtractor", extractor))

    await processor.process(
        article,
        Task(pipeline_run_id=uuid.uuid4(), name="process.classify"),
    )

    assert len(extractor.calls) == 1
    assert extractor.calls[0] == article.id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scorer_clamps_upper_boundary() -> None:
    article = _make_article(
        "Fed market region rate inflation outlook forecast growth recession warning policy",
        "Fed market region rate inflation outlook forecast growth recession warning policy.",
        url_suffix="market-region-upper-bound",
    )

    result = await ArticleScorer.score(article)

    assert 0.0 <= float(result.importance_score) <= 10.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deduplicator_provider_exception_raises_processing_error() -> None:
    article = _make_article(
        "Fed keeps rates unchanged as inflation remains elevated",
        "The Federal Reserve keeps rates unchanged as inflation remains elevated.",
        url_suffix="dedup-provider-exception",
    )
    candidate = _make_article(
        "Fed keeps rates unchanged as inflation remains elevated too",
        "The Federal Reserve keeps rates unchanged while inflation remains elevated.",
        url_suffix="dedup-provider-exception-candidate",
    )

    with pytest.raises(ProcessingError):
        await SemanticDeduplicator(provider=_FailingEmbeddingProvider()).deduplicate(
            article, [candidate]
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deduplicator_invalid_embedding_falls_back_to_deterministic_match() -> None:
    article = _make_article(
        "Fed holds rates while inflation stays elevated",
        "The Federal Reserve expects inflation to remain high and keeps rates unchanged.",
        url_suffix="dedup-invalid-embedding",
    )
    candidate = _make_article(
        "Fed keeps rates unchanged as inflation remains elevated",
        "The Federal Reserve keeps interest rates unchanged as inflation remains high.",
        url_suffix="dedup-invalid-embedding-candidate",
    )

    result = await SemanticDeduplicator(provider=_MalformedEmbeddingProvider()).deduplicate(
        article,
        [candidate],
    )

    assert result is candidate


@pytest.mark.unit
@pytest.mark.asyncio
async def test_processor_rejects_invalid_status() -> None:
    article = _make_article("Published article", "Already processed", url_suffix="published")
    article = article.model_copy(update={"status": ArticleStatus.PUBLISHED})
    task = Task(pipeline_run_id=uuid.uuid4(), name="process.classify")

    with pytest.raises(ProcessingError):
        await ArticleProcessor().process(article, task)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_processor_is_idempotent_for_processed_article() -> None:
    article = _make_article("Rate cuts on the horizon as inflation eases", url_suffix="rate-cuts")
    task = Task(pipeline_run_id=uuid.uuid4(), name="process.classify")

    processed = await ArticleProcessor().process(article, task)
    second = await ArticleProcessor().process(processed, task)

    assert second == processed
