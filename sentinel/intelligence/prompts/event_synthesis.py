"""Prompt template for market-event synthesis."""

from __future__ import annotations

from collections.abc import Sequence

from sentinel_core.models import Article


def event_synthesis_prompt(articles: Sequence[Article]) -> str:
    """Build a deterministic event-synthesis prompt from supporting evidence."""
    evidence: list[str] = []
    for index, article in enumerate(articles, start=1):
        lines = [f"Article {index}:", f"Title: {article.title}"]
        if article.summary:
            lines.append(f"Summary: {article.summary}")
        if article.content:
            content = article.content.strip().replace("\n", " ")
            lines.append(f"Content: {content[:1200]}")
        evidence.append("\n".join(lines))

    return (
        "Synthesize one MarketEvent from the following processed Articles. "
        "Return valid JSON only with keys: title, summary, asset_class, region, "
        "sector, severity, sentiment, sentiment_confidence, importance_score, "
        "importance_confidence, occurred_at, source_article_ids. "
        "Use the Sentinel enum vocabulary exactly. "
        "The summary must explain why the development matters for markets. "
        "source_article_ids must contain the UUIDs of the Articles that support the event. "
        "Do not invent unsupported facts.\n\n" + "\n\n---\n\n".join(evidence)
    )
