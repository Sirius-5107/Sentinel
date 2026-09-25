"""Lightweight extraction utilities for article entities."""

from __future__ import annotations

from dataclasses import dataclass

from sentinel_core.enums import EntityType
from sentinel_core.models import Article


@dataclass(frozen=True)
class ExtractedEntity:
    """A named entity extracted from article text."""

    name: str
    entity_type: EntityType


class EntityExtractor:
    """Extract company, person, and organisation references from article text."""

    @staticmethod
    async def extract(article: Article) -> list[ExtractedEntity]:
        """Extract entities using deterministic keyword and name matching."""
        text = "\n".join(part for part in (article.title, article.summary, article.content) if part)
        lower_text = text.lower()

        entities: list[ExtractedEntity] = []

        for person_name in (
            "Jerome Powell",
            "Janet Yellen",
            "Lagarde",
            "Elon Musk",
            "Tim Cook",
            "Sundar Pichai",
        ):
            if person_name.lower() in lower_text:
                entities.append(ExtractedEntity(name=person_name, entity_type=EntityType.PERSON))

        for company_name in (
            "Apple",
            "Microsoft",
            "NVIDIA",
            "Tesla",
            "Amazon",
            "Alphabet",
            "Meta",
            "Intel",
            "Goldman Sachs",
            "JPMorgan",
        ):
            if company_name.lower() in lower_text:
                entities.append(ExtractedEntity(name=company_name, entity_type=EntityType.COMPANY))

        for org_name in (
            "Federal Reserve",
            "SEC",
            "ECB",
            "IMF",
            "BOE",
            "RBI",
            "World Bank",
            "BIS",
        ):
            if org_name.lower() in lower_text:
                entities.append(ExtractedEntity(name=org_name, entity_type=EntityType.ORGANIZATION))

        deduped: list[ExtractedEntity] = []
        seen: set[tuple[str, str]] = set()
        for entity in entities:
            key = (entity.name.lower(), entity.entity_type.value)
            if key not in seen:
                seen.add(key)
                deduped.append(entity)
        return deduped


__all__ = ["EntityExtractor", "ExtractedEntity"]
