import types
from app import main as mainmod
from app.main import _token_cache


def test_confluence_requires_auth_token(client):
    r = client.get("/api/v1/confluence/pages/123")
    assert r.status_code == 401
    r2 = client.put("/api/v1/confluence/pages/123", json={"body_storage_value": "<p>x</p>", "version": 2})
    assert r2.status_code == 401


def test_confluence_get_success(client, monkeypatch):
    _token_cache["access_token"] = "tkn"
    # Return bases: jira (unused), confluence base
    monkeypatch.setattr(mainmod, "_ensure_bases", lambda token: ("jira", "https://example.atlassian.com/confluence/rest/api"), raising=True)

    def fake_get(self, url, headers=None, params=None):
        assert url.endswith("/content/123")
        return types.SimpleNamespace(
            status_code=200,
            json=lambda: {
                "id": "123",
                "type": "page",
                "title": "Hello",
                "version": {"number": 3},
                "space": {"key": "SPACE"},
            },
            text="",
        )

    monkeypatch.setattr(mainmod.httpx.Client, "get", fake_get, raising=True)

    r = client.get("/api/v1/confluence/pages/123")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "123"
    assert data["title"] == "Hello"
    assert data["version"] == 3
    assert data["spaceKey"] == "SPACE"


def test_confluence_get_error_propagates(client, monkeypatch):
    _token_cache["access_token"] = "tkn"
    monkeypatch.setattr(mainmod, "_ensure_bases", lambda token: ("jira", "base"), raising=True)

    def fake_get(self, url, headers=None, params=None):
        return types.SimpleNamespace(status_code=404, json=lambda: {"err": "not found"}, text="nf")

    monkeypatch.setattr(mainmod.httpx.Client, "get", fake_get, raising=True)

    r = client.get("/api/v1/confluence/pages/999")
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "Confluence get page failed"


def test_confluence_update_success_with_title_fetch(client, monkeypatch):
    _token_cache["access_token"] = "tkn"
    monkeypatch.setattr(mainmod, "_ensure_bases", lambda token: ("jira", "https://example.atlassian.com/confluence/rest/api"), raising=True)

    # First GET to fetch current title
    def fake_get(self, url, headers=None, params=None):
        return types.SimpleNamespace(status_code=200, json=lambda: {"title": "Existing Title"}, text="")

    # PUT to update
    def fake_put(self, url, headers=None, json=None):
        assert json["title"] == "Existing Title"
        assert json["body"]["storage"]["value"] == "<p>Updated</p>"
        return types.SimpleNamespace(status_code=200, json=lambda: {"ok": True, "id": "123"}, text="")

    monkeypatch.setattr(mainmod.httpx.Client, "get", fake_get, raising=True)
    monkeypatch.setattr(mainmod.httpx.Client, "put", fake_put, raising=True)

    payload = {"body_storage_value": "<p>Updated</p>", "version": 2}
    r = client.put("/api/v1/confluence/pages/123", json=payload)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_confluence_update_error_propagates(client, monkeypatch):
    _token_cache["access_token"] = "tkn"
    monkeypatch.setattr(mainmod, "_ensure_bases", lambda token: ("jira", "base"), raising=True)

    def fake_put(self, url, headers=None, json=None):
        return types.SimpleNamespace(status_code=500, json=lambda: {"err": "server"}, text="oops")

    monkeypatch.setattr(mainmod.httpx.Client, "put", fake_put, raising=True)

    payload = {"title": "T", "body_storage_value": "<p>x</p>", "version": 2}
    r = client.put("/api/v1/confluence/pages/1", json=payload)
    assert r.status_code == 500
    assert r.json()["detail"]["error"] == "Confluence update failed"
