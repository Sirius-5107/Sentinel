"""Unit tests for sentinel_core.exceptions."""

from __future__ import annotations

import pytest

from sentinel_core.exceptions import (
    CollectionError,
    ConfigurationError,
    IntelligenceError,
    NotFoundError,
    ProcessingError,
    PublishingError,
    SentinelError,
    ValidationError,
)


@pytest.mark.unit
class TestExceptionHierarchy:
    """All typed exceptions must be catchable as SentinelError."""

    def test_sentinel_error_is_exception(self) -> None:
        assert issubclass(SentinelError, Exception)

    def test_validation_error_is_sentinel_error(self) -> None:
        assert issubclass(ValidationError, SentinelError)

    def test_configuration_error_is_sentinel_error(self) -> None:
        assert issubclass(ConfigurationError, SentinelError)

    def test_collection_error_is_sentinel_error(self) -> None:
        assert issubclass(CollectionError, SentinelError)

    def test_processing_error_is_sentinel_error(self) -> None:
        assert issubclass(ProcessingError, SentinelError)

    def test_intelligence_error_is_sentinel_error(self) -> None:
        assert issubclass(IntelligenceError, SentinelError)

    def test_publishing_error_is_sentinel_error(self) -> None:
        assert issubclass(PublishingError, SentinelError)

    def test_not_found_error_is_sentinel_error(self) -> None:
        assert issubclass(NotFoundError, SentinelError)


@pytest.mark.unit
class TestExceptionRaising:
    """Exceptions must be raiseable and catchable."""

    def test_raise_sentinel_error(self) -> None:
        with pytest.raises(SentinelError):
            raise ValidationError("domain rule violated")

    def test_raise_validation_error(self) -> None:
        with pytest.raises(ValidationError, match="domain rule"):
            raise ValidationError("domain rule violated")

    def test_raise_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("missing required key")

    def test_raise_collection_error(self) -> None:
        with pytest.raises(CollectionError):
            raise CollectionError("RSS feed unreachable")

    def test_raise_processing_error(self) -> None:
        with pytest.raises(ProcessingError):
            raise ProcessingError("LLM timeout")

    def test_raise_intelligence_error(self) -> None:
        with pytest.raises(IntelligenceError):
            raise IntelligenceError("synthesis failed")

    def test_raise_publishing_error(self) -> None:
        with pytest.raises(PublishingError):
            raise PublishingError("Notion API rejected request")


@pytest.mark.unit
class TestNotFoundError:
    """NotFoundError carries structured context."""

    def test_message_format(self) -> None:
        err = NotFoundError("Source", "reuters-business")
        assert "Source" in str(err)
        assert "reuters-business" in str(err)

    def test_model_attribute(self) -> None:
        err = NotFoundError("Article", "some-uuid")
        assert err.model == "Article"

    def test_identifier_attribute(self) -> None:
        err = NotFoundError("Article", "some-uuid")
        assert err.identifier == "some-uuid"

    def test_catchable_as_sentinel_error(self) -> None:
        with pytest.raises(SentinelError):
            raise NotFoundError("Company", "NASDAQ:AAPL")
