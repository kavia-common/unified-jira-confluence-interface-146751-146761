from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routers import jira_router, confluence_router
from .routers.user import router as user_router

# Create FastAPI application with metadata
app = FastAPI(
    title="JIRA-Confluence Integration API",
    description="API for integrating JIRA and Confluence services, providing a unified interface for both platforms",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=[
        {
            "name": "users",
            "description": "User management operations"
        },
        {
            "name": "jira",
            "description": "JIRA integration operations"
        },
        {
            "name": "confluence",
            "description": "Confluence integration operations"
        }
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure with environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(user_router)
app.include_router(jira_router)
app.include_router(confluence_router)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Health check endpoint
@app.get("/", tags=["health"])
def health_check():
    """
    Simple health check endpoint to verify the API is running
    
    Returns:
        dict: Health status message
    """
    return {"status": "healthy", "message": "API is running"}
