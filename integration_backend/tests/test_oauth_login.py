import urllib.parse
import re
import os
import pytest
from app.main import _state_store


def test_login_misconfiguration_returns_500_json(client, monkeypatch):
    # Remove required envs
    monkeypatch.delenv("ATLASSIAN_CLIENT_ID", raising=False)
    monkeypatch.delenv("ATLASSIAN_REDIRECT_URI", raising=False)

    r = client.get("/api/v1/auth/atlassian/login")
    assert r.status_code == 500
    data = r.json()
    assert data["error"] == "Server misconfiguration"
    assert "ATLASSIAN_CLIENT_ID" in data["detail"]


def test_login_redirect_contains_expected_params_and_records_state(client):
    r = client.get("/api/v1/auth/atlassian/login", allow_redirects=False)
    assert r.status_code in (302, 307)
    loc = r.headers.get("location")
    assert loc is not None
    parsed = urllib.parse.urlparse(loc)
    assert parsed.scheme == "https"
    assert parsed.netloc == "auth.atlassian.com"
    assert parsed.path == "/authorize"

    # Check query params
    q = urllib.parse.parse_qs(parsed.query)
    assert q["audience"] == ["api.atlassian.com"]
    assert q["client_id"] == ["test-client-id"]
    assert "scope" in q
    # redirect_uri must be urlencode-equivalent to the env redirect
    assert q["redirect_uri"] == ["http://testserver/api/v1/auth/atlassian/callback"]
    assert q["response_type"] == ["code"]
    assert q["prompt"] == ["consent"]
    assert "state" in q and len(q["state"][0]) > 10  # some non-empty random state

    # State should be recorded in the in-memory store
    state = q["state"][0]
    assert state in _state_store


def test_login_with_client_provided_state_is_preserved_and_stored(client):
    provided_state = "custom-state-123"
    r = client.get(f"/api/v1/auth/atlassian/login?state={provided_state}", allow_redirects=False)
    assert r.status_code in (302, 307)
    loc = r.headers["location"]
    q = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)
    assert q["state"] == [provided_state]
    # should be stored too
    assert provided_state in _state_store
