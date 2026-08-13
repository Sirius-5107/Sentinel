"""Unit tests for sentinel_core.types value objects."""

from __future__ import annotations

from pydantic import BaseModel, ValidationError
import pytest

from sentinel_core.types import (
    ConfidenceScore,
    CountryCode,
    CurrencyCode,
    IanaTimezone,
    ImportanceScore,
    IsinCode,
    LanguageCode,
    MicCode,
    SlugField,
    Ticker,
)

# -- Helpers ------------------------------------------------------------------


def _make(field_type: object, value: object) -> object:
    """Construct a temporary model with the given field type and validate value."""
    m = type("_Tmp", (BaseModel,), {"__annotations__": {"value": field_type}})
    return m(value=value).value  # type: ignore[call-arg]


def _raises(field_type: object, value: object) -> None:
    """Assert that constructing a model with the given value raises ValidationError."""
    with pytest.raises(ValidationError):
        _make(field_type, value)


# -- ConfidenceScore ----------------------------------------------------------


@pytest.mark.unit
class TestConfidenceScore:
    def test_valid_boundary_zero(self) -> None:
        assert _make(ConfidenceScore, 0.0) == 0.0

    def test_valid_boundary_one(self) -> None:
        assert _make(ConfidenceScore, 1.0) == 1.0

    def test_valid_midpoint(self) -> None:
        assert _make(ConfidenceScore, 0.5) == 0.5

    def test_rounded_to_four_decimal_places(self) -> None:
        result = _make(ConfidenceScore, 0.87501)
        assert result == round(0.87501, 4)

    def test_below_zero_raises(self) -> None:
        _raises(ConfidenceScore, -0.001)

    def test_above_one_raises(self) -> None:
        _raises(ConfidenceScore, 1.001)


# -- ImportanceScore ----------------------------------------------------------


@pytest.mark.unit
class TestImportanceScore:
    def test_valid_boundary_zero(self) -> None:
        assert _make(ImportanceScore, 0.0) == 0.0

    def test_valid_boundary_ten(self) -> None:
        assert _make(ImportanceScore, 10.0) == 10.0

    def test_valid_midpoint(self) -> None:
        assert _make(ImportanceScore, 5.0) == 5.0

    def test_rounded_to_two_decimal_places(self) -> None:
        result = _make(ImportanceScore, 7.555)
        assert result == round(7.555, 2)

    def test_below_zero_raises(self) -> None:
        _raises(ImportanceScore, -0.01)

    def test_above_ten_raises(self) -> None:
        _raises(ImportanceScore, 10.01)


# -- CountryCode --------------------------------------------------------------


@pytest.mark.unit
class TestCountryCode:
    @pytest.mark.parametrize("code", ["US", "IN", "GB", "JP", "DE"])
    def test_valid(self, code: str) -> None:
        assert _make(CountryCode, code) == code

    def test_lowercase_raises(self) -> None:
        _raises(CountryCode, "us")

    def test_three_chars_raises(self) -> None:
        _raises(CountryCode, "USA")

    def test_one_char_raises(self) -> None:
        _raises(CountryCode, "U")

    def test_digit_raises(self) -> None:
        _raises(CountryCode, "U1")

    def test_empty_raises(self) -> None:
        _raises(CountryCode, "")


# -- LanguageCode -------------------------------------------------------------


@pytest.mark.unit
class TestLanguageCode:
    @pytest.mark.parametrize("code", ["en", "hi", "zh", "ja", "de"])
    def test_valid(self, code: str) -> None:
        assert _make(LanguageCode, code) == code

    def test_uppercase_raises(self) -> None:
        _raises(LanguageCode, "EN")

    def test_three_chars_raises(self) -> None:
        _raises(LanguageCode, "eng")

    def test_empty_raises(self) -> None:
        _raises(LanguageCode, "")


# -- Ticker -------------------------------------------------------------------


@pytest.mark.unit
class TestTicker:
    @pytest.mark.parametrize(
        "ticker",
        ["NYSE:BRK.B", "NSE:RELIANCE", "NASDAQ:AAPL", "LSE:HSBA", "BSE:500325"],
    )
    def test_valid(self, ticker: str) -> None:
        assert _make(Ticker, ticker) == ticker

    def test_no_colon_raises(self) -> None:
        _raises(Ticker, "NASDAQAAPL")

    def test_lowercase_exchange_raises(self) -> None:
        _raises(Ticker, "nasdaq:AAPL")

    def test_too_long_raises(self) -> None:
        _raises(Ticker, "ABCDEFGHIJK:ABCDEFGHIJ")

    def test_empty_raises(self) -> None:
        _raises(Ticker, "")


# -- CurrencyCode -------------------------------------------------------------


@pytest.mark.unit
class TestCurrencyCode:
    @pytest.mark.parametrize("code", ["USD", "INR", "EUR", "GBP", "JPY"])
    def test_valid(self, code: str) -> None:
        assert _make(CurrencyCode, code) == code

    def test_two_chars_raises(self) -> None:
        _raises(CurrencyCode, "US")

    def test_four_chars_raises(self) -> None:
        _raises(CurrencyCode, "USDD")

    def test_lowercase_raises(self) -> None:
        _raises(CurrencyCode, "usd")


# -- MicCode ------------------------------------------------------------------


@pytest.mark.unit
class TestMicCode:
    @pytest.mark.parametrize("mic", ["XNYS", "XNAS", "XNSE", "XBSE", "XLON"])
    def test_valid(self, mic: str) -> None:
        assert _make(MicCode, mic) == mic

    def test_three_chars_raises(self) -> None:
        _raises(MicCode, "XNY")

    def test_five_chars_raises(self) -> None:
        _raises(MicCode, "XNYSE")

    def test_lowercase_raises(self) -> None:
        _raises(MicCode, "xnys")


# -- IsinCode -----------------------------------------------------------------


@pytest.mark.unit
class TestIsinCode:
    @pytest.mark.parametrize(
        "isin",
        ["US0378331005", "US5949181045", "IN0009010547", "GB0002634946"],
    )
    def test_valid(self, isin: str) -> None:
        assert _make(IsinCode, isin) == isin

    def test_too_short_raises(self) -> None:
        _raises(IsinCode, "US037833100")

    def test_too_long_raises(self) -> None:
        _raises(IsinCode, "US03783310050")

    def test_lowercase_raises(self) -> None:
        _raises(IsinCode, "us0378331005")


# -- IanaTimezone -------------------------------------------------------------


@pytest.mark.unit
class TestIanaTimezone:
    @pytest.mark.parametrize(
        "tz",
        ["America/New_York", "Asia/Kolkata", "Europe/London", "UTC", "Asia/Tokyo"],
    )
    def test_valid(self, tz: str) -> None:
        assert _make(IanaTimezone, tz) == tz

    def test_invalid_raises(self) -> None:
        _raises(IanaTimezone, "Not/A/Timezone")

    def test_empty_raises(self) -> None:
        _raises(IanaTimezone, "")

    def test_offset_string_raises(self) -> None:
        _raises(IanaTimezone, "UTC+5:30")


# -- SlugField ----------------------------------------------------------------


@pytest.mark.unit
class TestSlugField:
    @pytest.mark.parametrize(
        "slug",
        ["ai-capex-cycle", "india-infrastructure", "private-credit", "macro", "us-equities"],
    )
    def test_valid(self, slug: str) -> None:
        assert _make(SlugField, slug) == slug

    def test_uppercase_raises(self) -> None:
        _raises(SlugField, "AI-Capex")

    def test_leading_hyphen_raises(self) -> None:
        _raises(SlugField, "-ai-capex")

    def test_trailing_hyphen_raises(self) -> None:
        _raises(SlugField, "ai-capex-")

    def test_double_hyphen_raises(self) -> None:
        _raises(SlugField, "ai--capex")

    def test_too_long_raises(self) -> None:
        _raises(SlugField, "a" * 101)

    def test_space_raises(self) -> None:
        _raises(SlugField, "ai capex")
