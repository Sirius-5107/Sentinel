"""Unit tests for Market, Organization, and Theme models."""

from __future__ import annotations

from datetime import UTC, datetime
import uuid

from pydantic import ValidationError
import pytest

from sentinel_core.enums import AssetClass, MarketRegion
from sentinel_core.models import Market, Organization, Theme

# -- Market -------------------------------------------------------------------


@pytest.mark.unit
class TestMarket:
    def test_minimal_construction(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        m = Market(**market_kwargs)
        assert m.name == "New York Stock Exchange"
        assert m.abbreviation == "NYSE"
        assert m.country == "US"
        assert m.region == MarketRegion.US
        assert m.currency == "USD"
        assert m.timezone == "America/New_York"
        assert m.is_active is True
        assert m.mic is None

    def test_with_mic(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        m = Market(**{**market_kwargs, "mic": "XNYS"})
        assert m.mic == "XNYS"

    def test_is_frozen(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        m = Market(**market_kwargs)
        with pytest.raises((TypeError, ValidationError)):
            m.name = "Changed"  # type: ignore[misc]

    def test_id_generated(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        market_kwargs.pop("id", None)
        m = Market(**market_kwargs)
        assert isinstance(m.id, uuid.UUID)

    def test_timestamps_utc_aware(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        m = Market(**market_kwargs)
        assert m.created_at.tzinfo is not None
        assert m.updated_at.tzinfo is not None

    def test_invalid_country_code(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="CountryCode"):
            Market(**{**market_kwargs, "country": "usa"})

    def test_invalid_currency_code(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="CurrencyCode"):
            Market(**{**market_kwargs, "currency": "us"})

    def test_invalid_timezone(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="IANA"):
            Market(**{**market_kwargs, "timezone": "Not/Real"})

    def test_invalid_mic(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError, match="MicCode"):
            Market(**{**market_kwargs, "mic": "XN"})

    def test_name_too_long(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        with pytest.raises(ValidationError):
            Market(**{**market_kwargs, "name": "x" * 201})

    def test_inactive_market(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        m = Market(**{**market_kwargs, "is_active": False})
        assert m.is_active is False

    def test_json_serialization(self, market_kwargs: dict) -> None:  # type: ignore[type-arg]
        m = Market(**market_kwargs)
        data = m.model_dump(mode="json")
        assert data["abbreviation"] == "NYSE"
        assert data["region"] == "us"
        assert isinstance(data["id"], str)


# -- Organization -------------------------------------------------------------


@pytest.mark.unit
class TestOrganization:
    def test_minimal_construction(self) -> None:
        org = Organization(name="Federal Reserve System")
        assert org.name == "Federal Reserve System"
        assert org.abbreviation is None
        assert org.country is None
        assert org.region is None
        assert org.is_verified is False
        assert org.mention_count == 0
        assert org.last_mentioned_at is None

    def test_full_construction(self) -> None:
        org = Organization(
            name="Federal Reserve System",
            abbreviation="Fed",
            country="US",
            region=MarketRegion.US,
            description="The central banking system of the United States.",
            is_verified=True,
            mention_count=42,
            last_mentioned_at=datetime(2026, 8, 7, tzinfo=UTC),
        )
        assert org.abbreviation == "Fed"
        assert org.mention_count == 42

    def test_is_frozen(self) -> None:
        org = Organization(name="SEC")
        with pytest.raises((TypeError, ValidationError)):
            org.name = "Changed"  # type: ignore[misc]

    def test_negative_mention_count_raises(self) -> None:
        with pytest.raises(ValidationError):
            Organization(name="SEC", mention_count=-1)

    def test_naive_datetime_raises(self) -> None:
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            Organization(name="SEC", last_mentioned_at=dt(2026, 8, 7))

    def test_description_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Organization(name="SEC", description="x" * 2001)

    def test_abbreviation_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Organization(name="SEC", abbreviation="x" * 21)

    def test_supranational_no_country(self) -> None:
        org = Organization(name="International Monetary Fund", abbreviation="IMF")
        assert org.country is None

    def test_json_serialization(self) -> None:
        org = Organization(name="Federal Reserve", abbreviation="Fed", country="US")
        data = org.model_dump(mode="json")
        assert data["name"] == "Federal Reserve"
        assert isinstance(data["id"], str)


# -- Theme --------------------------------------------------------------------


@pytest.mark.unit
class TestTheme:
    def test_minimal_construction(self) -> None:
        t = Theme(name="AI Capex Cycle", slug="ai-capex-cycle")
        assert t.name == "AI Capex Cycle"
        assert t.slug == "ai-capex-cycle"
        assert t.is_active is True
        assert t.article_count == 0
        assert t.asset_class is None
        assert t.region is None

    def test_full_construction(self) -> None:
        t = Theme(
            name="AI Capex Cycle",
            slug="ai-capex-cycle",
            description="Tracks accelerating AI infrastructure investment.",
            asset_class=AssetClass.EQUITY,
            region=MarketRegion.GLOBAL,
            is_active=True,
            article_count=150,
            last_signal_at=datetime(2026, 8, 7, tzinfo=UTC),
        )
        assert t.article_count == 150
        assert t.asset_class == AssetClass.EQUITY

    def test_is_frozen(self) -> None:
        t = Theme(name="AI", slug="ai")
        with pytest.raises((TypeError, ValidationError)):
            t.name = "Changed"  # type: ignore[misc]

    def test_invalid_slug_uppercase(self) -> None:
        with pytest.raises(ValidationError, match="Slug"):
            Theme(name="AI", slug="AI-Capex")

    def test_invalid_slug_leading_hyphen(self) -> None:
        with pytest.raises(ValidationError, match="Slug"):
            Theme(name="AI", slug="-ai-capex")

    def test_invalid_slug_trailing_hyphen(self) -> None:
        with pytest.raises(ValidationError, match="Slug"):
            Theme(name="AI", slug="ai-capex-")

    def test_invalid_slug_double_hyphen(self) -> None:
        with pytest.raises(ValidationError, match="Slug"):
            Theme(name="AI", slug="ai--capex")

    def test_slug_too_long(self) -> None:
        with pytest.raises(ValidationError):
            Theme(name="AI", slug="a" * 101)

    def test_negative_article_count_raises(self) -> None:
        with pytest.raises(ValidationError):
            Theme(name="AI", slug="ai", article_count=-1)

    def test_naive_last_signal_at_raises(self) -> None:
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            Theme(name="AI", slug="ai", last_signal_at=dt(2026, 8, 7))

    def test_description_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Theme(name="AI", slug="ai", description="x" * 5001)

    def test_archived_theme(self) -> None:
        t = Theme(name="AI", slug="ai", is_active=False)
        assert t.is_active is False

    def test_json_serialization(self) -> None:
        t = Theme(name="AI Capex Cycle", slug="ai-capex-cycle")
        data = t.model_dump(mode="json")
        assert data["slug"] == "ai-capex-cycle"
        assert isinstance(data["id"], str)
