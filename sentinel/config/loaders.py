"""Runtime configuration loaders for Phase 2 bootstrap.

This package is intentionally outside sentinel_core. Phase 1 remains frozen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, HttpUrl, field_validator

from sentinel_core.enums import AssetClass, MarketRegion, SourceStatus, SourceType
from sentinel_core.models.source import Source


class SourceConfig(BaseModel):
    """Bootstrap configuration for a single source entry in configs/sources.yaml."""

    name: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1, max_length=2048)
    enabled: bool = True
    category: str = "macro"
    weight: float = 1.0

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        return value.strip()

    @field_validator("category")
    @classmethod
    def _validate_category(cls, value: str) -> str:
        return value.strip().lower()


def _category_to_region(category: str) -> MarketRegion:
    mapping: dict[str, MarketRegion] = {
        "macro": MarketRegion.GLOBAL,
        "india": MarketRegion.INDIA,
        "us": MarketRegion.US,
        "europe": MarketRegion.EUROPE,
        "asia": MarketRegion.ASIA_PACIFIC,
        "asia_pacific": MarketRegion.ASIA_PACIFIC,
        "latin_america": MarketRegion.LATIN_AMERICA,
        "latin": MarketRegion.LATIN_AMERICA,
        "africa": MarketRegion.AFRICA,
        "middle_east": MarketRegion.MIDDLE_EAST,
        "global": MarketRegion.GLOBAL,
    }
    return mapping.get(category.lower(), MarketRegion.GLOBAL)


def _category_to_asset_class(category: str) -> AssetClass:
    mapping: dict[str, AssetClass] = {
        "macro": AssetClass.MACRO,
        "equity": AssetClass.EQUITY,
        "fixed_income": AssetClass.FIXED_INCOME,
        "credit": AssetClass.PRIVATE_CREDIT,
        "private_credit": AssetClass.PRIVATE_CREDIT,
        "private_equity": AssetClass.PRIVATE_EQUITY,
        "real_estate": AssetClass.REAL_ESTATE,
        "commodities": AssetClass.COMMODITIES,
        "currencies": AssetClass.CURRENCIES,
        "crypto": AssetClass.CRYPTO,
        "other": AssetClass.OTHER,
        "india": AssetClass.MACRO,
        "us": AssetClass.MACRO,
        "global": AssetClass.MACRO,
    }
    return mapping.get(category.lower(), AssetClass.OTHER)


def load_source_configs(path: str | Path = "configs/sources.yaml") -> list[SourceConfig]:
    """Load source bootstrap definitions from a YAML file.

    The YAML is intentionally config-only; it is not part of sentinel_core.
    """

    config_path = Path(path)
    if not config_path.exists():
        return []

    raw_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw_data, dict):
        return []

    sources_section = raw_data.get("sources", {})
    if not isinstance(sources_section, dict):
        return []

    entries: list[SourceConfig] = []
    for group_name in ("rss", "scrape", "dynamic", "api", "manual"):
        group_items = sources_section.get(group_name, [])
        if not isinstance(group_items, list):
            continue
        for item in group_items:
            if not isinstance(item, dict):
                continue
            candidate = SourceConfig(
                name=item.get("name", ""),
                url=item.get("url", ""),
                enabled=bool(item.get("enabled", True)),
                category=str(item.get("category", group_name)),
                weight=float(item.get("weight", 1.0)),
            )
            if candidate.enabled:
                entries.append(candidate)
    return entries


def load_sources(path: str | Path = "configs/sources.yaml") -> list[Source]:
    """Resolve runtime source YAML into immutable sentinel_core Source models."""

    resolved: list[Source] = []
    for config in load_source_configs(path):
        category = config.category.lower()
        source_type: SourceType
        if category == "rss":
            source_type = SourceType.RSS
        elif category == "scrape":
            source_type = SourceType.SCRAPE
        elif category == "dynamic":
            source_type = SourceType.DYNAMIC
        elif category == "api":
            source_type = SourceType.API
        else:
            source_type = SourceType.RSS

        resolved.append(
            Source(
                name=config.name,
                url=HttpUrl(config.url),
                source_type=source_type,
                status=SourceStatus.ACTIVE,
                region=_category_to_region(category),
                asset_class=_category_to_asset_class(category),
                language="en",
                weight=config.weight,
                fetch_interval_minutes=60,
                last_fetched_at=None,
                last_error=None,
                consecutive_errors=0,
            )
        )
    return resolved


__all__ = ["SourceConfig", "load_source_configs", "load_sources"]
