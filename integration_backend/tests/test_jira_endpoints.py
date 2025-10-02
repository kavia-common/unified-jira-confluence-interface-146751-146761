import types
import pytest
from app import main as mainmod
from app.main import _token_cache


def test_jira_search_requires_auth_token(client):
    payload = {"jql": "project=TEST", "max_results": 10}
    r = client.post("/api/v1/jira/issues/search", json=payload)
    assert r.status_code == 401
    assert r.json()["detail"].startswith("Not authenticated")


def test_jira_create_requires_auth_token(client):
    payload = {"fields": {"project_key": "TEST", "summary": "Title"}}
    r = client.post("/api/v1/jira/issues", json=payload)
    assert r.status_code == 401


def test_jira_search_success_with_mocked_httpx(client, monkeypatch):
    # Prepare token and base URLs
    _token_cache["access_token"] = "tkn"
    # Mock _ensure_bases to return JIRA base and dummy confluence base
    monkeypatch.setattr(mainmod, "_ensure_bases", lambda token: ("https://example.atlassian.com/jira/rest/api/3", "conf"), raising=True)

    # Mock httpx.Client.post to return search results
    def fake_post(self, url, headers=None, json=None):
        assert url.endswith("/search")
        assert json["jql"] == "project=TEST"
        return types.SimpleNamespace(
            status_code=200,
            json=lambda: {"issues": [{"id": "10001"}], "total": 1},
            text="",
        )

    monkeypatch.setattr(mainmod.httpx.Client, "post", fake_post, raising=True)

    payload = {"jql": "project=TEST", "max_results": 5, "fields": ["summary", "status"]}
    r = client.post("/api/v1/jira/issues/search", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["issues"][0]["id"] == "10001"


def test_jira_search_error_propagates(client, monkeypatch):
    _token_cache["access_token"] = "tkn"
    monkeypatch.setattr(mainmod, "_ensure_bases", lambda token: ("https://example.atlassian.com/jira/rest/api/3", "conf"), raising=True)

    def fake_post(self, url, headers=None, json=None):
        return types.SimpleNamespace(status_code=400, json=lambda: {"err": "bad jql"}, text="bad")

    monkeypatch.setattr(mainmod.httpx.Client, "post", fake_post, raising=True)
    payload = {"jql": "bad", "max_results": 5}
    r = client.post("/api/v1/jira/issues/search", json=payload)
    assert r.status_code == 400
    data = r.json()
    assert data["detail"]["error"] == "JIRA search failed"


def test_jira_create_success(client, monkeypatch):
    _token_cache["access_token"] = "tkn"
    monkeypatch.setattr(mainmod, "_ensure_bases", lambda token: ("https://example.atlassian.com/jira/rest/api/3", "conf"), raising=True)

    def fake_post(self, url, headers=None, json=None):
        assert url.endswith("/issue")
        return types.SimpleNamespace(status_code=201, json=lambda: {"id": "10005"}, text="")

    monkeypatch.setattr(mainmod.httpx.Client, "post", fake_post, raising=True)

    payload = {
        "fields": {
            "project_key": "TEST",
            "summary": "Implement tests",
            "description": "Desc",
            "issuetype_name": "Task",
        }
    }
    r = client.post("/api/v1/jira/issues", json=payload)
    assert r.status_code == 200 or r.status_code == 201
    assert r.json()["id"] == "10005"


def test_jira_create_error_propagates(client, monkeypatch):
    _token_cache["access_token"] = "tkn"
    monkeypatch.setattr(mainmod, "_ensure_bases", lambda token: ("https://example.atlassian.com/jira/rest/api/3", "conf"), raising=True)

    def fake_post(self, url, headers=None, json=None):
        return types.SimpleNamespace(status_code=500, json=lambda: {"err": "server"}, text="oops")

    monkeypatch.setattr(mainmod.httpx.Client, "post", fake_post, raising=True)

    payload = {"fields": {"project_key": "TEST", "summary": "x"}}
    r = client.post("/api/v1/jira/issues", json=payload)
    assert r.status_code == 500
    data = r.json()
    assert data["detail"]["error"] == "JIRA create failed"
