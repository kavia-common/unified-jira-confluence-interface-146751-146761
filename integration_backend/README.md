# Integration Backend (FastAPI)

This is the FastAPI backend for the Unified JIRA-Confluence Interface.

## Features
- Health and readiness endpoints (`/health`, `/ready`)
- OpenAPI docs at `/docs` and `/openapi.json`
- CORS configured for local frontend development and preview environments (configurable via `CORS_ORIGINS`)
- Atlassian OAuth 2.0 endpoints for JIRA/Confluence
- Docker HEALTHCHECK probing `/ready`

## Requirements
- Python 3.11+
- Dependencies in `requirements.txt`
- Environment variables in `.env` (see `.env.example`)

## Setup

1. Create a `.env` file based on `.env.example`:
   - Do not commit secrets
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the server (default port is 3001):
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 3001
   ```

## Docker
Build and run:
```
docker build -t integration_backend .
docker run -p 3001:3001 --env-file .env integration_backend
```

Readiness/Health:
- Container includes a HEALTHCHECK that polls `http://127.0.0.1:${APP_PORT:-3001}/ready`
- If your platform provides `PORT`, it will be used automatically via `run.sh` (mapped to `APP_PORT`)

CORS notes:
- By default, `CORS_ORIGINS=*` to ease preview/dependency checks.
- For stricter environments, set `CORS_ORIGINS` to a comma-separated list of allowed origins.

## Endpoints
- `GET /` - Root info
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe
- `GET /api/v1/auth/status` - Auth status placeholder
- `GET /api/v1/integrations/jira/ping` - JIRA connectivity placeholder
- `GET /api/v1/integrations/confluence/ping` - Confluence connectivity placeholder
- `GET /api/v1/auth/atlassian/login` - Redirects to Atlassian's OAuth 2.0 authorization page
- `GET /api/v1/auth/atlassian/callback` - Handles Atlassian redirect, validates state, exchanges code for tokens

## Atlassian OAuth 2.0

This backend supports Atlassian OAuth 2.0 Authorization Code flow for JIRA and Confluence APIs.

1. Configure environment variables in `.env`:
   ```
   ATLASSIAN_CLIENT_ID=your_client_id
   ATLASSIAN_CLIENT_SECRET=your_client_secret
   ATLASSIAN_REDIRECT_URI=http://localhost:3001/api/v1/auth/atlassian/callback
   ```
   - The redirect URI must match exactly what you configure in the Atlassian Developer Console.

2. Start the flow by visiting:
   - `http://localhost:3001/api/v1/auth/atlassian/login`

3. After granting consent, Atlassian redirects to the callback:
   - `GET /api/v1/auth/atlassian/callback?code=...&state=...`

4. The backend validates `state` and exchanges `code` for tokens with Atlassian. The callback returns:
   - HTML success/error page by default
   - Or JSON if you pass `?format=json`

Security notes:
- A short-lived, one-time-use state token is used to protect against CSRF. In production, back this with a user session or a persistent store (e.g., Redis).
- This sample implementation does not persist tokens. Integrate with your user model and secure storage to save `access_token` and `refresh_token`.

Scopes:
- The login endpoint requests commonly used scopes for JIRA and Confluence. Adjust scopes to your needs.
```text
offline_access read:jira-user read:jira-work write:jira-work
read:confluence-space.summary read:confluence-content.all write:confluence-content
read:confluence-props read:me
```
