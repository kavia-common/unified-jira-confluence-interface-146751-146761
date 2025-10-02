# Integration Backend (FastAPI)

This is the FastAPI backend for the Unified JIRA-Confluence Interface.

## Features
- Health and readiness endpoints (`/health`, `/ready`)
- OpenAPI docs at `/docs` and `/openapi.json`
- CORS configured for local frontend development (`http://localhost:3000`)
- Placeholder routes for Auth and Integrations

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
3. Run the server:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## Docker
Build and run:
```
docker build -t integration_backend .
docker run -p 8000:8000 --env-file .env integration_backend
```

## Endpoints
- `GET /` - Root info
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe
- `GET /api/v1/auth/status` - Auth status placeholder
- `GET /api/v1/integrations/jira/ping` - JIRA connectivity placeholder
- `GET /api/v1/integrations/confluence/ping` - Confluence connectivity placeholder
