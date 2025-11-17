"""
pytest configuration for throttled-api tests
"""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Restrict anyio to asyncio backend only"""
    return "asyncio"
