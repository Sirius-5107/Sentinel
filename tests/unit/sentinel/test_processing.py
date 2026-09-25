"""Unit tests for the Phase 3 processing layer."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import uuid

import pytest

from sentinel.processing.classifier import ArticleClassifier
from sentinel.processing.dedup import SemanticDeduplicator
from sentinel.processing.extractor import EntityExtractor
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
