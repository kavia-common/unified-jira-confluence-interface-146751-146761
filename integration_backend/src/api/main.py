from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import jira_router

app = FastAPI(
    title="JIRA-Confluence Integration API",
    description="API for integrating JIRA and Confluence services",
    version="1.0.0"
)

app.include_router(jira_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"message": "Healthy"}
