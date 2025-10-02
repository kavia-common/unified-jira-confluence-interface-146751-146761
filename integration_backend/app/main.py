import os
import secrets
import time
from typing import List, Optional, Dict

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file if present
# Note: Server host/port are controlled by run.sh via APP_HOST/APP_PORT (default 3001)
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Unified JIRA-Confluence Backend")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
APP_ENV = os.getenv("APP_ENV", "development")

# Atlassian OAuth environment variables
ATLASSIAN_CLIENT_ID = os.getenv("ATLASSIAN_CLIENT_ID")
ATLASSIAN_CLIENT_SECRET = os.getenv("ATLASSIAN_CLIENT_SECRET")
ATLASSIAN_REDIRECT_URI = os.getenv("ATLASSIAN_REDIRECT_URI")

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
    {"name": "Auth", "description": "Authentication endpoints including Atlassian OAuth 2.0."},
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


# ============ Atlassian OAuth 2.0 Implementation ============

# Simple in-memory state store with expiry to prevent CSRF.
# For production, use a persistent/redis-backed store scoped per-user session.
_state_store: Dict[str, float] = {}
STATE_TTL_SECONDS = 600  # 10 minutes


def _cleanup_state_store() -> None:
    """Remove expired state entries."""
    now = time.time()
    expired = [k for k, exp in _state_store.items() if exp < now]
    for k in expired:
        _state_store.pop(k, None)


def _new_state() -> str:
    """Generate and record a new state token with expiry."""
    token = secrets.token_urlsafe(24)
    _state_store[token] = time.time() + STATE_TTL_SECONDS
    return token


def _validate_state(token: Optional[str]) -> bool:
    """Validate a provided state token and consume it if valid."""
    if not token:
        return False
    _cleanup_state_store()
    exp = _state_store.get(token)
    if exp is None:
        return False
    if exp < time.time():
        _state_store.pop(token, None)
        return False
    # One-time use: consume token
    _state_store.pop(token, None)
    return True


# PUBLIC_INTERFACE
@app.get(
    "/api/v1/auth/atlassian/login",
    tags=["Auth"],
    summary="Start Atlassian OAuth 2.0 flow",
    description="Redirects the user to Atlassian's authorization endpoint with client ID, redirect URI, scopes, and state.",
)
def atlassian_login() -> RedirectResponse | JSONResponse:
    """Initiate Atlassian OAuth 2.0 Authorization Code flow.

    Returns:
        RedirectResponse: Redirects user agent to Atlassian's authorize URL.
        JSONResponse: Error if environment is not configured.
    """
    if not ATLASSIAN_CLIENT_ID or not ATLASSIAN_REDIRECT_URI:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Server misconfiguration",
                "detail": "ATLASSIAN_CLIENT_ID and ATLASSIAN_REDIRECT_URI must be set in environment.",
            },
        )

    # Scopes: Request OpenID Connect basic profile and offline access for refresh tokens,
    # plus Jira/Confluence scopes as needed. Adjust as required by product needs.
    scopes = [
        "offline_access",
        "read:jira-user",
        "read:jira-work",
        "write:jira-work",
        "read:confluence-space.summary",
        "read:confluence-content.all",
        "write:confluence-content",
        "read:confluence-props",
        "read:me",
    ]
    scope_param = " ".join(scopes)

    state = _new_state()

    # Atlassian Cloud OAuth 2.0 authorize endpoint
    authorize_url = "https://auth.atlassian.com/authorize"
    params = {
        "audience": "api.atlassian.com",
        "client_id": ATLASSIAN_CLIENT_ID,
        "scope": scope_param,
        "redirect_uri": ATLASSIAN_REDIRECT_URI,
        "response_type": "code",
        "prompt": "consent",
        "state": state,
    }
    # Build redirect URL manually to preserve spaces as encoded %20
    query = httpx.QueryParams(params)
    url = f"{authorize_url}?{query}"
    return RedirectResponse(url=url, status_code=302)


# PUBLIC_INTERFACE
@app.get(
    "/api/v1/auth/atlassian/callback",
    tags=["Auth"],
    summary="Handle Atlassian OAuth 2.0 callback",
    description="Handles the redirect with code and state, validates state, exchanges the code for tokens, and returns a simple result.",
)
def atlassian_callback(
    code: Optional[str] = Query(default=None, description="Authorization code returned by Atlassian"),
    state: Optional[str] = Query(default=None, description="Opaque state for CSRF protection"),
    format: Optional[str] = Query(default="html", description="Response format: 'html' or 'json'"),
):
    """Handle Atlassian OAuth callback.

    Parameters:
        code (str): Authorization code from Atlassian.
        state (str): State token used to protect against CSRF.
        format (str): Optional response format. 'html' (default) returns a simple success/error page, 'json' returns token JSON.

    Returns:
        HTMLResponse | JSONResponse: Outcome of token exchange or error details.
    """
    # Validate config
    if not ATLASSIAN_CLIENT_ID or not ATLASSIAN_CLIENT_SECRET or not ATLASSIAN_REDIRECT_URI:
        msg = "ATLASSIAN_CLIENT_ID, ATLASSIAN_CLIENT_SECRET, and ATLASSIAN_REDIRECT_URI must be set."
        if format == "json":
            return JSONResponse(status_code=500, content={"error": "Server misconfiguration", "detail": msg})
        return HTMLResponse(status_code=500, content=f"<h3>Server misconfiguration</h3><p>{msg}</p>")

    # Validate presence of code/state
    if not code or not state:
        if format == "json":
            return JSONResponse(status_code=400, content={"error": "Invalid request", "detail": "Missing code or state"})
        return HTMLResponse(status_code=400, content="<h3>Invalid request</h3><p>Missing code or state.</p>")

    # Validate state against store
    if not _validate_state(state):
        if format == "json":
            return JSONResponse(status_code=400, content={"error": "Invalid state", "detail": "State is invalid or expired"})
        return HTMLResponse(status_code=400, content="<h3>Invalid state</h3><p>State is invalid or expired.</p>")

    token_url = "https://auth.atlassian.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": ATLASSIAN_CLIENT_ID,
        "client_secret": ATLASSIAN_CLIENT_SECRET,
        "code": code,
        "redirect_uri": ATLASSIAN_REDIRECT_URI,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(token_url, json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code != 200:
                detail = None
                try:
                    detail = resp.json()
                except Exception:
                    detail = {"text": resp.text}
                if format == "json":
                    return JSONResponse(
                        status_code=resp.status_code,
                        content={"error": "Token exchange failed", "detail": detail},
                    )
                return HTMLResponse(
                    status_code=resp.status_code,
                    content=f"<h3>Token exchange failed</h3><pre>{detail}</pre>",
                )

            token_data = resp.json()
    except httpx.HTTPError as e:
        if format == "json":
            return JSONResponse(status_code=502, content={"error": "Upstream error", "detail": str(e)})
        return HTMLResponse(status_code=502, content=f"<h3>Upstream error</h3><pre>{str(e)}</pre>")

    # In a full implementation you would persist tokens (including refresh_token) securely, associated with the user.
    # For now, just return a minimal confirmation.
    if format == "json":
        # Do not expose refresh_token unless necessary; include minimal fields
        safe = {
            "token_type": token_data.get("token_type"),
            "expires_in": token_data.get("expires_in"),
            "scope": token_data.get("scope"),
            "access_token_present": bool(token_data.get("access_token")),
            "refresh_token_present": bool(token_data.get("refresh_token")),
        }
        return JSONResponse(status_code=200, content={"success": True, "tokens": safe})

    return HTMLResponse(
        status_code=200,
        content="""
            <h3>Atlassian OAuth Success</h3>
            <p>The authorization code was exchanged for tokens successfully.</p>
            <p>You can close this window and return to the app.</p>
        """,
    )
