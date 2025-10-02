import json
import types
import pytest
from app.main import _state_store, _token_cache


def _insert_valid_state():
    state = "valid-state-token"
    # set far future expiry (value is timestamp); using dummy float acceptable because callback uses _validate_state
    _state_store[state] = 9999999999.0
    return state


def test_callback_missing_params_returns_400_html_by_default(client):
    state = _insert_valid_state()
    # missing code
    r = client.get(f"/api/v1/auth/atlassian/callback?state={state}")
    assert r.status_code == 400
    assert "Missing code or state" in r.text


def test_callback_invalid_state_returns_400(client):
    # no state in store
    r = client.get("/api/v1/auth/atlassian/callback?code=abc123&state=bad", headers={"accept": "text/html"})
    assert r.status_code == 400
    assert "Invalid state" in r.text


def test_callback_success_json_sets_token_cache_and_returns_safe_fields(client, monkeypatch):
    state = _insert_valid_state()

    # Mock httpx.Client.post to return a successful token exchange
    from app import main as mainmod

    def fake_post(self, url, json=None, headers=None):
        assert "oauth/token" in url
        return types.SimpleNamespace(
            status_code=200,
            json=lambda: {
                "token_type": "Bearer",
                "access_token": "access_test",
                "refresh_token": "refresh_test",
                "expires_in": 3600,
                "scope": "read:jira-user",
            },
        )

    monkeypatch.setattr(mainmod.httpx.Client, "post", fake_post, raising=True)

    r = client.get("/api/v1/auth/atlassian/callback?code=abc123&state=valid-state-token&format=json")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    tokens = data["tokens"]
    assert tokens["token_type"] == "Bearer"
    assert tokens["expires_in"] == 3600
    assert tokens["scope"] == "read:jira-user"
    assert tokens["access_token_present"] is True
    assert tokens["refresh_token_present"] is True

    # token cache updated
    assert _token_cache.get("access_token") == "access_test"
    assert _token_cache.get("refresh_token") == "refresh_test"
    assert isinstance(_token_cache.get("expires_at"), float)


def test_callback_upstream_error_returns_502_html(client, monkeypatch):
    state = _insert_valid_state()
    from app import main as mainmod

    def fake_post(self, url, json=None, headers=None):
        class E(Exception):
            pass
        # Simulate httpx.HTTPError, but we can raise a subclass to be caught as generic Exception
        raise mainmod.httpx.HTTPError("network error")

    monkeypatch.setattr(mainmod.httpx.Client, "post", fake_post, raising=True)

    r = client.get(f"/api/v1/auth/atlassian/callback?code=abc&state={state}")
    assert r.status_code == 502
    assert "Upstream error" in r.text


def test_callback_token_exchange_failure_propagates_status_and_detail_json(client, monkeypatch):
    state = _insert_valid_state()
    from app import main as mainmod

    def fake_post(self, url, json=None, headers=None):
        return types.SimpleNamespace(
            status_code=400,
            json=lambda: {"error": "invalid_grant"},
            text="bad request",
        )

    monkeypatch.setattr(mainmod.httpx.Client, "post", fake_post, raising=True)

    r = client.get(f"/api/v1/auth/atlassian/callback?code=bad&state={state}&format=json")
    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "Token exchange failed"
    assert data["detail"]["error"] == "invalid_grant"
