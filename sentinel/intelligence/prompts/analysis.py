"""Prompt template for event analysis."""

from __future__ import annotations

from collections.abc import Sequence

from sentinel_core.models import Article, MarketEvent


def analysis_prompt(event: MarketEvent, evidence: Sequence[Article]) -> str:
    """Build a prompt that keeps analysis grounded in supplied evidence."""
    evidence_lines: list[str] = []
    for index, article in enumerate(evidence, start=1):
        evidence_lines.append(
            f"Article {index}: {article.title}\nSummary: {article.summary or article.content or ''}"
        )

    return (
        "Write a concise explanation of why this market event matters. "
        "Base every factual claim on the supplied event summary and supporting "
        "article evidence. Do not invent unsupported facts. Return valid JSON "
        "only with keys: text and supporting_article_ids.\n\n"
        f"MarketEvent:\n{event.model_dump_json(indent=2, exclude_none=True)}\n\n"
        "Evidence:\n" + "\n\n".join(evidence_lines)
    )
