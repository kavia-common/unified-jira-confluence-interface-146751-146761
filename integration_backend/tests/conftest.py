import os
import types
import pytest
from fastapi.testclient import TestClient

# Import app and internal caches/utilities to reset between tests
from app.main import app, _state_store, _token_cache, _site_cache


@pytest.fixture(autouse=True)
def _env_and_reset(monkeypatch):
    """
    Autouse fixture:
    - Sets required Atlassian OAuth env vars for tests unless a test overrides them.
    - Resets in-memory stores between tests to ensure isolation.
    """
    # Default env for successful paths (tests can override per-case)
    monkeypatch.setenv("ATLASSIAN_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("ATLASSIAN_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("ATLASSIAN_REDIRECT_URI", "http://testserver/api/v1/auth/atlassian/callback")
    # Clear optional envs
    for key in ("JIRA_BASE_URL", "CONFLUENCE_BASE_URL", "CORS_ORIGINS"):
        if key in os.environ:
            monkeypatch.delenv(key, raising=False)

    # Reset caches
    _state_store.clear()
    _token_cache.clear()
    _site_cache.clear()

    yield

    # Ensure no state leaks to next test
    _state_store.clear()
    _token_cache.clear()
    _site_cache.clear()


@pytest.fixture
def client():
    """
    Provides a FastAPI TestClient.
    """
    with TestClient(app) as c:
        yield c


class DummyResponse:
    """A minimal dummy response for mocking httpx responses used in tests."""
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        if self._json_data is not None:
            return self._json_data
        raise ValueError("No JSON available")
