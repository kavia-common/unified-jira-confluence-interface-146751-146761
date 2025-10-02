# Integration Backend (FastAPI)

This is the FastAPI backend for the Unified JIRA-Confluence Interface.

## Features
- Health and readiness endpoints (`/health`, `/ready`)
- OpenAPI docs at `/docs` and `/openapi.json`
- CORS configured for local frontend development and preview environments (configurable via `CORS_ORIGINS`)
- Placeholder routes for Auth and Integrations
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
