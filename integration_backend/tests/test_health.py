from app.main import APP_VERSION


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "env" in data
    assert data["version"] == APP_VERSION
    assert data["dependencies_ok"] is True
    assert data["details"]["service"] == "integration_backend"


def test_ready_endpoint(client):
    r = client.get("/ready")
    assert r.status_code == 200
    data = r.json()
    assert data["ready"] is True
    assert data["dependencies_ok"] is True
    assert data["reason"] is None


def test_root_and_openapi(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "Unified JIRA-Confluence Backend"
    assert data["docs"] == "/docs"
    assert data["openapi"] == "/openapi.json"
    assert data["health"] == "/health"
    assert data["ready"] == "/ready"
    assert data["version"] == APP_VERSION

    # OpenAPI should be present and valid JSON
    r2 = client.get("/openapi.json")
    assert r2.status_code == 200
    spec = r2.json()
    assert "openapi" in spec
    assert "paths" in spec
