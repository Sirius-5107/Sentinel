"""Deterministic article classification helpers for Phase 3."""

from __future__ import annotations

from dataclasses import dataclass

from sentinel_core.enums import AssetClass, MarketRegion, Sector, Sentiment
from sentinel_core.exceptions.base import ProcessingError
from sentinel_core.interfaces.protocols import LLMProviderProtocol
from sentinel_core.models import Article
from sentinel_core.types import ConfidenceScore


@dataclass(frozen=True)
class ClassificationResult:
    """Representative output of a deterministic classifier."""

    asset_class: AssetClass
    region: MarketRegion
    sector: Sector
    sentiment: Sentiment
    sentiment_confidence: ConfidenceScore


class ArticleClassifier:
    """Classify article metadata without introducing a production AI dependency."""

    def __init__(self, provider: LLMProviderProtocol | None = None) -> None:
        """Create a classifier, optionally backed by a provider implementation."""
        self.provider = provider

    async def classify(
        self,
        article: Article,
        provider: LLMProviderProtocol | None = None,
    ) -> ClassificationResult:
        """Return a deterministic classification for a single article.

        A provider may be supplied for a future model-backed implementation, but the
        default path intentionally remains deterministic and testable.
        """
        effective_provider = provider or self.provider
        text = "\n".join(part for part in (article.title, article.summary, article.content) if part)
        if effective_provider is not None and hasattr(effective_provider, "complete"):
            prompt = (
                "Classify this article as JSON with keys asset_class, region, sector, "
                "sentiment. Keep values to the Sentinel enum vocabulary.\n\n"
                f"{text[:4000]}"
            )
            try:
                raw = await effective_provider.complete(prompt, max_tokens=256, temperature=0.0)
            except Exception as exc:
                raise ProcessingError(
                    "Classification provider failed while classifying article."
                ) from exc

            parsed = self._parse_provider_result(raw)
            if parsed is not None:
                return parsed

        asset_class = self._classify_asset_class(text)
        region = self._classify_region(text)
        sector = self._classify_sector(text)
        sentiment, confidence = self._classify_sentiment(text)
        return ClassificationResult(
            asset_class=asset_class,
            region=region,
            sector=sector,
            sentiment=sentiment,
            sentiment_confidence=confidence,
        )

    @staticmethod
    def _parse_provider_result(raw: str) -> ClassificationResult | None:
        """Best-effort parse for a provider result represented as JSON-like text."""
        try:
            payload = raw.strip()
            if payload.startswith("{"):
                import json

                data = json.loads(payload)
            else:
                return None
        except (TypeError, ValueError):
            return None

        asset_class = data.get("asset_class")
        region = data.get("region")
        sector = data.get("sector")
        sentiment = data.get("sentiment")
        if not all([asset_class, region, sector, sentiment]):
            return None

        try:
            return ClassificationResult(
                asset_class=AssetClass(asset_class),
                region=MarketRegion(region),
                sector=Sector(sector),
                sentiment=Sentiment(sentiment),
                sentiment_confidence=float(data.get("sentiment_confidence", 0.5)),
            )
        except ValueError:
            return None

    @staticmethod
    def _classify_asset_class(text: str) -> AssetClass:
        lower = text.lower()
        if any(
            token in lower
            for token in ("fed", "rate", "inflation", "treasury", "central bank", "policy")
        ):
            return AssetClass.MACRO
        if any(
            token in lower
            for token in ("equity", "stock", "earnings", "share", "market cap", "portfolio")
        ):
            return AssetClass.EQUITY
        if any(
            token in lower for token in ("bond", "yield", "credit", "loan", "mortgage", "default")
        ):
            return AssetClass.FIXED_INCOME
        if any(token in lower for token in ("commodity", "oil", "gas", "gold", "copper", "wheat")):
            return AssetClass.COMMODITIES
        if any(
            token in lower
            for token in ("currency", "forex", "dollar", "rupee", "yuan", "exchange rate")
        ):
            return AssetClass.CURRENCIES
        if any(token in lower for token in ("crypto", "bitcoin", "ethereum", "blockchain")):
            return AssetClass.CRYPTO
        return AssetClass.OTHER

    @staticmethod
    def _classify_region(text: str) -> MarketRegion:
        lower = text.lower()
        if any(
            token in lower
            for token in ("federal reserve", "u.s.", "washington", "nasdaq", "nyse", "wall street")
        ):
            return MarketRegion.US
        if any(token in lower for token in ("india", "nse", "bse", "rbi", "mumbai")):
            return MarketRegion.INDIA
        if any(token in lower for token in ("europe", "eu", "ecb", "london", "frankfurt", "paris")):
            return MarketRegion.EUROPE
        if any(
            token in lower
            for token in ("asia", "china", "japan", "hong kong", "tokyo", "singapore")
        ):
            return MarketRegion.ASIA_PACIFIC
        if any(token in lower for token in ("middle east", "uae", "saudi", "gulf", "qatar")):
            return MarketRegion.MIDDLE_EAST
        if any(token in lower for token in ("latin america", "brazil", "mexico", "argentina")):
            return MarketRegion.LATIN_AMERICA
        if any(token in lower for token in ("africa", "south africa", "nigeria")):
            return MarketRegion.AFRICA
        return MarketRegion.GLOBAL

    @staticmethod
    def _classify_sector(text: str) -> Sector:
        lower = text.lower()
        if any(
            token in lower
            for token in ("chip", "semiconductor", "ai", "cloud", "software", "cybersecurity")
        ):
            return Sector.TECHNOLOGY
        if any(
            token in lower
            for token in ("bank", "insurance", "mortgage", "credit", "lending", "capital markets")
        ):
            return Sector.FINANCIALS
        if any(
            token in lower
            for token in ("pharma", "drug", "biotech", "healthcare", "hospital", "medical")
        ):
            return Sector.HEALTHCARE
        if any(
            token in lower for token in ("automotive", "retail", "consumer", "travel", "ecommerce")
        ):
            return Sector.CONSUMER_DISCRETIONARY
        if any(token in lower for token in ("food", "beverage", "grocery", "household", "staples")):
            return Sector.CONSUMER_STAPLES
        if any(
            token in lower
            for token in ("rail", "industrial", "manufacturing", "infrastructure", "shipping")
        ):
            return Sector.INDUSTRIALS
        if any(token in lower for token in ("oil", "gas", "energy", "pipeline", "drilling")):
            return Sector.ENERGY
        if any(token in lower for token in ("metal", "mining", "commodity", "steel", "lithium")):
            return Sector.MATERIALS
        if any(token in lower for token in ("real estate", "property", "reit", "housing")):
            return Sector.REAL_ESTATE
        if any(
            token in lower for token in ("telecom", "media", "internet", "network", "broadcast")
        ):
            return Sector.COMMUNICATION_SERVICES
        return Sector.UNKNOWN

    @staticmethod
    def _classify_sentiment(text: str) -> tuple[Sentiment, ConfidenceScore]:
        lower = text.lower()
        positive_hits = sum(
            1
            for token in (
                "surge",
                "gain",
                "strong",
                "beat",
                "rally",
                "upgrade",
                "growth",
                "bullish",
            )
            if token in lower
        )
        negative_hits = sum(
            1
            for token in (
                "fall",
                "drop",
                "weak",
                "miss",
                "slump",
                "downgrade",
                "recession",
                "bearish",
            )
            if token in lower
        )
        if positive_hits == negative_hits == 0:
            return Sentiment.NEUTRAL, 0.45
        if positive_hits > negative_hits:
            confidence = min(0.95, 0.55 + 0.1 * positive_hits)
            return Sentiment.BULLISH, float(confidence)
        if negative_hits > positive_hits:
            confidence = min(0.95, 0.55 + 0.1 * negative_hits)
            return Sentiment.BEARISH, float(confidence)
        return Sentiment.MIXED, 0.6


__all__ = ["ArticleClassifier", "ClassificationResult"]
