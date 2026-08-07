"""Foundation smoke tests.

Verify that the core packages are importable and the project is correctly
installed. These tests contain no business logic — they exist to ensure
the engineering foundation is intact.
"""

import pytest


@pytest.mark.unit
def test_sentinel_importable() -> None:
    """sentinel package must be importable."""
    import sentinel  # noqa: F401


@pytest.mark.unit
def test_sentinel_core_importable() -> None:
    """sentinel_core package must be importable."""
    import sentinel_core  # noqa: F401


@pytest.mark.unit
def test_sentinel_subpackages_importable() -> None:
    """All sentinel sub-packages must be importable."""
    from sentinel import (  # noqa: F401
        api,
        cli,
        collector,
        common,
        intelligence,
        knowledge,
        processing,
        publish,
        research,
        scheduler,
    )


@pytest.mark.unit
def test_sentinel_core_subpackages_importable() -> None:
    """All sentinel_core sub-packages must be importable."""
    from sentinel_core import (  # noqa: F401
        config,
        constants,
        enums,
        exceptions,
        interfaces,
        models,
        types,
    )
