from typing import List, Optional
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from ..auth.oauth import confluence_oauth
from ..models.confluence import (
    ConfluencePageCreate,
    ConfluencePageUpdate,
    ConfluencePageResponse
)
from ..services.confluence import confluence_service

router = APIRouter(
    prefix="/api/confluence",
    tags=["confluence"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/auth/authorize")
async def authorize_confluence():
    """
    Get Confluence OAuth authorization URL
    
    Returns:
        dict: Authorization URL and state
    """
    state = "random-state"  # TODO: Generate secure random state
    auth_url = confluence_oauth.get_authorization_url(state)
    return {
        "auth_url": auth_url,
        "state": state
    }

@router.post("/auth/callback")
async def confluence_oauth_callback(code: str, state: str):
    """
    Handle Confluence OAuth callback
    
    Args:
        code: Authorization code
        state: State for CSRF protection
        
    Returns:
        OAuthToken: Access token response
    """
    # TODO: Verify state matches
    return await confluence_oauth.exchange_code_for_token(code)

@router.post("/pages", response_model=ConfluencePageResponse)
async def create_page(
    page: ConfluencePageCreate,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Create a new Confluence page
    
    Args:
        page: Page creation data
        access_token: OAuth access token
        
    Returns:
        ConfluencePageResponse: Created page
    """
    return await confluence_service.create_page(access_token, page)

@router.get("/pages/{page_id}", response_model=ConfluencePageResponse)
async def get_page(
    page_id: str,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Get a Confluence page by ID
    
    Args:
        page_id: Confluence page ID
        access_token: OAuth access token
        
    Returns:
        ConfluencePageResponse: Page details
    """
    return await confluence_service.get_page(access_token, page_id)

@router.put("/pages/{page_id}", response_model=ConfluencePageResponse)
async def update_page(
    page_id: str,
    update_data: ConfluencePageUpdate,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Update a Confluence page
    
    Args:
        page_id: Confluence page ID
        update_data: Page update data
        access_token: OAuth access token
        
    Returns:
        ConfluencePageResponse: Updated page
    """
    return await confluence_service.update_page(access_token, page_id, update_data)

@router.delete("/pages/{page_id}")
async def delete_page(
    page_id: str,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Delete a Confluence page
    
    Args:
        page_id: Confluence page ID
        access_token: OAuth access token
        
    Returns:
        dict: Success message
    """
    await confluence_service.delete_page(access_token, page_id)
    return {"message": f"Page {page_id} deleted successfully"}

@router.post("/pages/search", response_model=List[ConfluencePageResponse])
async def search_pages(
    cql: str,
    max_results: Optional[int] = 50,
    access_token: str = Depends(oauth2_scheme)
):
    """
    Search Confluence pages using CQL
    
    Args:
        cql: CQL search query
        max_results: Maximum number of results to return
        access_token: OAuth access token
        
    Returns:
        List[ConfluencePageResponse]: List of matching pages
    """
    return await confluence_service.search_pages(access_token, cql, max_results)
