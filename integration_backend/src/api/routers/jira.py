from typing import List, Optional
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from ..auth.oauth import jira_oauth
from ..models.jira import (
    JiraIssueCreate,
    JiraIssueUpdate,
    JiraIssueResponse
)
from ..services.jira import jira_service

router = APIRouter(
    prefix="/api/jira",
    tags=["jira"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/auth/authorize")
async def authorize_jira():
    """
    Get JIRA OAuth authorization URL
    
    Returns:
        dict: Authorization URL and state
    """
    state = "random-state"  # TODO: Generate secure random state
    auth_url = jira_oauth.get_authorization_url(state)
    return {
        "auth_url": auth_url,
        "state": state
    }

@router.post("/auth/callback")
async def jira_oauth_callback(code: str, state: str):
    """
    Handle JIRA OAuth callback
    
    Args:
        code: Authorization code
        state: State for CSRF protection
        
    Returns:
        OAuthToken: Access token response
    """
    # TODO: Verify state matches
    return await jira_oauth.exchange_code_for_token(code)

@router.post("/issues", response_model=JiraIssueResponse)
async def create_issue(
    issue: JiraIssueCreate,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Create a new JIRA issue
    
    Args:
        issue: Issue creation data
        access_token: OAuth access token
        
    Returns:
        JiraIssueResponse: Created issue
    """
    return await jira_service.create_issue(access_token, issue)

@router.get("/issues/{issue_key}", response_model=JiraIssueResponse)
async def get_issue(
    issue_key: str,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Get a JIRA issue by key
    
    Args:
        issue_key: JIRA issue key
        access_token: OAuth access token
        
    Returns:
        JiraIssueResponse: Issue details
    """
    return await jira_service.get_issue(access_token, issue_key)

@router.put("/issues/{issue_key}", response_model=JiraIssueResponse)
async def update_issue(
    issue_key: str,
    update_data: JiraIssueUpdate,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Update a JIRA issue
    
    Args:
        issue_key: JIRA issue key
        update_data: Issue update data
        access_token: OAuth access token
        
    Returns:
        JiraIssueResponse: Updated issue
    """
    return await jira_service.update_issue(access_token, issue_key, update_data)

@router.delete("/issues/{issue_key}")
async def delete_issue(
    issue_key: str,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Delete a JIRA issue
    
    Args:
        issue_key: JIRA issue key
        access_token: OAuth access token
        
    Returns:
        dict: Success message
    """
    await jira_service.delete_issue(access_token, issue_key)
    return {"message": f"Issue {issue_key} deleted successfully"}

@router.post("/issues/search", response_model=List[JiraIssueResponse])
async def search_issues(
    jql: str,
    max_results: Optional[int] = 50,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Search JIRA issues using JQL
    
    Args:
        jql: JQL search query
        max_results: Maximum number of results to return
        access_token: OAuth access token
        
    Returns:
        List[JiraIssueResponse]: List of matching issues
    """
    return await jira_service.search_issues(access_token, jql, max_results)
