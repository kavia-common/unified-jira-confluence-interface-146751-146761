import os
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Unified JIRA-Confluence Backend")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
APP_ENV = os.getenv("APP_ENV", "development")

# Configure CORS
cors_origins_env = os.getenv("CORS_ORIGINS", "")
cors_origins_raw: List[str] = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
# If wildcard requested or not provided, allow "*", which is acceptable for non-credentialed requests.
# If credentials are required in future, switch to explicit origins.
allow_all = False
if not cors_origins_raw:
    # Default for preview/dev: allow all to avoid origin mismatch during installer checks
    allow_all = True
    cors_origins: List[str] = []
elif len(cors_origins_raw) == 1 and cors_origins_raw[0] == "*":
    allow_all = True
    cors_origins = []
else:
    cors_origins = cors_origins_raw

openapi_tags = [
    {"name": "Health", "description": "Service health, readiness, and version endpoints."},
    {"name": "Docs", "description": "Documentation helpers and usage notes, including WebSocket info if applicable."},
    {"name": "Auth", "description": "Authentication endpoints (placeholder)."},
    {"name": "Integrations", "description": "JIRA and Confluence integration endpoints (placeholders)."},
]

app = FastAPI(
    title=APP_NAME,
    description="Backend service handling API requests, integrations with JIRA and Confluence, user authentication, and business logic.",
    version=APP_VERSION,
    openapi_tags=openapi_tags,
)

# Apply CORS middleware
# If allow_all is True, set allow_origins=["*"] and disable credentials for spec compliance.
if allow_all:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Models
class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall service status indicator.")
    env: str = Field(..., description="Deployment environment (e.g., development, staging, production).")
    version: str = Field(..., description="Application version.")
    dependencies_ok: bool = Field(..., description="Whether downstream dependencies appear ready.")
    details: Optional[dict] = Field(default=None, description="Additional diagnostic information.")


class ReadyResponse(BaseModel):
    ready: bool = Field(..., description="If the service is ready to accept traffic.")
    reason: Optional[str] = Field(default=None, description="Reason if not ready.")
    dependencies_ok: bool = Field(..., description="Whether downstream dependencies appear ready.")


# PUBLIC_INTERFACE
@app.get("/health", tags=["Health"], summary="Health check", description="Returns basic health status for liveness probes.", response_model=HealthResponse)
def health() -> HealthResponse:
    """Service liveness probe endpoint."""
    deps_ok = True  # Placeholder logic; extend with real checks (e.g., DB ping)
    return HealthResponse(
        status="ok",
        env=APP_ENV,
        version=APP_VERSION,
        dependencies_ok=deps_ok,
        details={"service": "integration_backend"},
    )


# PUBLIC_INTERFACE
@app.get("/ready", tags=["Health"], summary="Readiness check", description="Indicates if the service is ready to accept requests.", response_model=ReadyResponse)
def readiness() -> ReadyResponse:
    """Service readiness probe endpoint."""
    # In future, validate DB connectivity or external integrations here
    deps_ok = True
    return ReadyResponse(ready=True, reason=None, dependencies_ok=deps_ok)


# PUBLIC_INTERFACE
@app.get("/", tags=["Docs"], summary="Root", description="Welcome message and quick links to API docs.")
def root() -> dict:
    """Root endpoint that provides basic info and links.

    Returns:
        dict: A JSON object with service message, documentation links, health and readiness endpoints, and version.
    """
    return {
        "message": "Unified JIRA-Confluence Backend",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "ready": "/ready",
        "version": APP_VERSION,
    }


# Placeholder routes to make the API structure visible to the frontend
# PUBLIC_INTERFACE
@app.get("/api/v1/auth/status", tags=["Auth"], summary="Auth status", description="Placeholder auth status endpoint.")
def auth_status() -> dict:
    """Returns a placeholder authentication status."""
    return {"authenticated": False, "user": None}


# PUBLIC_INTERFACE
@app.get("/api/v1/integrations/jira/ping", tags=["Integrations"], summary="JIRA ping", description="Placeholder JIRA connectivity check.")
def jira_ping() -> dict:
    """Placeholder endpoint for JIRA connectivity check."""
    base = os.getenv("JIRA_BASE_URL", "")
    return {"service": "jira", "configured": bool(base), "base_url": base or None}


# PUBLIC_INTERFACE
@app.get("/api/v1/integrations/confluence/ping", tags=["Integrations"], summary="Confluence ping", description="Placeholder Confluence connectivity check.")
def confluence_ping() -> dict:
    """Placeholder endpoint for Confluence connectivity check."""
    base = os.getenv("CONFLUENCE_BASE_URL", "")
    return {"service": "confluence", "configured": bool(base), "base_url": base or None}


# PUBLIC_INTERFACE
@app.get("/docs/websocket", tags=["Docs"], summary="WebSocket usage help", description="Currently no WebSocket endpoints are exposed. This page provides future usage notes.")
def websocket_docs() -> dict:
    """WebSocket usage helper endpoint to comply with documentation requirements."""
    return {
        "websocket_supported": False,
        "note": "No WebSocket endpoints are currently implemented. Future versions will document connection info here.",
    }
