"""Unit tests for Company and Person models."""

from __future__ import annotations

from datetime import UTC, datetime
import uuid

from pydantic import ValidationError
import pytest

from sentinel_core.enums import AssetClass, MarketRegion, Sector
from sentinel_core.models import Company, Person

# -- Company ------------------------------------------------------------------


@pytest.mark.unit
class TestCompany:
    def test_minimal_construction(self) -> None:
        c = Company(name="Apple Inc.")
        assert c.name == "Apple Inc."
        assert c.ticker is None
        assert c.isin is None
        assert c.is_verified is False
        assert c.mention_count == 0
        assert c.market_id is None

    def test_full_construction(self, market_id: uuid.UUID) -> None:
        c = Company(
            name="Apple Inc.",
            legal_name="Apple Inc.",
            ticker="NASDAQ:AAPL",
            isin="US0378331005",
            country="US",
            sector=Sector.TECHNOLOGY,
            asset_class=AssetClass.EQUITY,
            region=MarketRegion.US,
            market_id=market_id,
            description="Consumer electronics and software company.",
            is_verified=True,
            mention_count=500,
            last_mentioned_at=datetime(2026, 8, 7, tzinfo=UTC),
        )
        assert c.ticker == "NASDAQ:AAPL"
        assert c.isin == "US0378331005"
        assert c.market_id == market_id

    def test_is_frozen(self) -> None:
        c = Company(name="Apple")
        with pytest.raises((TypeError, ValidationError)):
            c.name = "Changed"  # type: ignore[misc]

    def test_invalid_ticker_no_colon(self) -> None:
        with pytest.raises(ValidationError):
            Company(name="Apple", ticker="NASDAQAAPL")  # type: ignore[arg-type]

    def test_invalid_isin_too_short(self) -> None:
        with pytest.raises(ValidationError):
            Company(name="Apple", isin="US037833100")  # type: ignore[arg-type]

    def test_invalid_isin_lowercase(self) -> None:
        with pytest.raises(ValidationError):
            Company(name="Apple", isin="us0378331005")  # type: ignore[arg-type]

    def test_invalid_country_code(self) -> None:
        with pytest.raises(ValidationError):
            Company(name="Apple", country="usa")  # type: ignore[arg-type]

    def test_negative_mention_count_raises(self) -> None:
        with pytest.raises(ValidationError):
            Company(name="Apple", mention_count=-1)

    def test_naive_last_mentioned_at_raises(self) -> None:
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            Company(name="Apple", last_mentioned_at=dt(2026, 8, 7))

    def test_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Company(name="x" * 301)

    def test_legal_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Company(name="Apple", legal_name="x" * 501)

    def test_description_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Company(name="Apple", description="x" * 5001)

    def test_uuid_id_generated(self) -> None:
        c = Company(name="Apple")
        assert isinstance(c.id, uuid.UUID)

    def test_timestamps_utc(self) -> None:
        c = Company(name="Apple")
        assert c.created_at.tzinfo is not None
        assert c.updated_at.tzinfo is not None

    def test_json_serialization(self) -> None:
        c = Company(name="Apple Inc.", ticker="NASDAQ:AAPL")
        data = c.model_dump(mode="json")
        assert data["name"] == "Apple Inc."
        assert data["ticker"] == "NASDAQ:AAPL"
        assert isinstance(data["id"], str)

    def test_indian_company(self) -> None:
        c = Company(
            name="Reliance Industries",
            ticker="NSE:RELIANCE",
            country="IN",
            region=MarketRegion.INDIA,
        )
        assert c.country == "IN"

    def test_private_equity_asset_class(self) -> None:
        c = Company(name="KKR & Co.", asset_class=AssetClass.PRIVATE_EQUITY)
        assert c.asset_class == AssetClass.PRIVATE_EQUITY


# -- Person -------------------------------------------------------------------


@pytest.mark.unit
class TestPerson:
    def test_minimal_construction(self) -> None:
        p = Person(full_name="Jerome Powell")
        assert p.full_name == "Jerome Powell"
        assert p.title is None
        assert p.organization_name is None
        assert p.country is None
        assert p.is_verified is False
        assert p.mention_count == 0
        assert p.last_mentioned_at is None

    def test_full_construction(self) -> None:
        p = Person(
            full_name="Jerome Powell",
            title="Chair",
            organization_name="Federal Reserve System",
            country="US",
            description="Chair of the Federal Reserve since 2018.",
            is_verified=True,
            mention_count=320,
            last_mentioned_at=datetime(2026, 8, 7, tzinfo=UTC),
        )
        assert p.full_name == "Jerome Powell"
        assert p.title == "Chair"
        assert p.mention_count == 320

    def test_is_frozen(self) -> None:
        p = Person(full_name="Jerome Powell")
        with pytest.raises((TypeError, ValidationError)):
            p.full_name = "Changed"  # type: ignore[misc]

    def test_negative_mention_count_raises(self) -> None:
        with pytest.raises(ValidationError):
            Person(full_name="Jerome Powell", mention_count=-1)

    def test_naive_last_mentioned_at_raises(self) -> None:
        from datetime import datetime as dt

        with pytest.raises(ValidationError, match="UTC-aware"):
            Person(full_name="Jerome Powell", last_mentioned_at=dt(2026, 8, 7))

    def test_full_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Person(full_name="x" * 201)

    def test_title_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Person(full_name="Jerome Powell", title="x" * 201)

    def test_organization_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Person(full_name="Jerome Powell", organization_name="x" * 301)

    def test_description_max_length(self) -> None:
        with pytest.raises(ValidationError):
            Person(full_name="Jerome Powell", description="x" * 2001)

    def test_invalid_country_code(self) -> None:
        with pytest.raises(ValidationError):
            Person(full_name="Jerome Powell", country="usa")  # type: ignore[arg-type]

    def test_uuid_generated(self) -> None:
        p = Person(full_name="Jerome Powell")
        assert isinstance(p.id, uuid.UUID)

    def test_json_serialization(self) -> None:
        p = Person(full_name="Jerome Powell", title="Chair", country="US")
        data = p.model_dump(mode="json")
        assert data["full_name"] == "Jerome Powell"
        assert isinstance(data["id"], str)

    def test_no_external_identifier_fields(self) -> None:
        """No linkedin_url or wikidata_id -- these are deferred to a future ADR."""
        p = Person(full_name="Elon Musk")
        assert not hasattr(p, "linkedin_url")
        assert not hasattr(p, "wikidata_id")
