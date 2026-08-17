"""Base exception classes for the Sentinel domain.

All exceptions raised from within sentinel_core must extend SentinelError.
Application-layer packages may extend these base classes to add context
specific to their stage (e.g. RSSCollectionError extending CollectionError).
"""

from __future__ import annotations


class SentinelError(Exception):
    """Root exception for all Sentinel domain errors.

    Catching SentinelError catches every domain-originated exception.
    Do not raise SentinelError directly — use a typed subclass.
    """


class ValidationError(SentinelError):
    """A domain-level validation rule was violated.

    Distinct from Pydantic's ValidationError, which is raised during model
    construction. This exception is raised when higher-level business rules
    are violated (e.g. an Article cannot be marked PUBLISHED before it has
    been PROCESSED).

    Do not confuse with pydantic.ValidationError.
    """


class ConfigurationError(SentinelError):
    """Required configuration is missing, invalid, or inconsistent.

    Raised at startup when the application config cannot be validated
    against the expected schema.
    """


class CollectionError(SentinelError):
    """A content collection operation failed.

    Raised by sentinel/collector/ implementations. Not raised by
    sentinel_core itself — defined here so that application-layer
    collectors can raise a typed, catchable domain exception.
    """


class ProcessingError(SentinelError):
    """An article processing operation failed.

    Raised by sentinel/processing/ implementations.
    """


class IntelligenceError(SentinelError):
    """An intelligence synthesis operation failed.

    Raised by sentinel/intelligence/ implementations.
    """


class PublishingError(SentinelError):
    """A report publishing operation failed.

    Raised by sentinel/publish/ implementations.
    """


class NotFoundError(SentinelError):
    """A requested domain object was not found.

    Example: looking up a Source by name that does not exist in the database.
    """

    def __init__(self, model: str, identifier: str) -> None:
        """Initialise with the model name and identifier that was not found.

        Args:
            model: The domain model class name (e.g. 'Source', 'Article').
            identifier: The identifier value that was not found.

        """
        super().__init__(f"{model} not found: {identifier!r}")
        self.model = model
        self.identifier = identifier
