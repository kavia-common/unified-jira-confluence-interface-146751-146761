from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from httpx import AsyncClient

from ..models.confluence import (
    ConfluencePageCreate,
    ConfluencePageUpdate,
    ConfluencePageResponse
)


class ConfluenceService:
    """Service class for handling Confluence operations"""
    
    def __init__(self, base_url: str = "https://api.atlassian.com/ex/confluence/"):
        self.base_url = base_url
        self._client: Optional[AsyncClient] = None

    async def _get_client(self, access_token: str) -> AsyncClient:
        """Get or create an HTTP client with proper authentication"""
        if not self._client:
            self._client = AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
        return self._client

    # PUBLIC_INTERFACE
    async def create_page(
        self, 
        access_token: str,
        page_data: ConfluencePageCreate
    ) -> ConfluencePageResponse:
        """
        Create a new Confluence page
        
        Args:
            access_token: OAuth access token
            page_data: Page creation data
            
        Returns:
            Created page response
            
        Raises:
            HTTPException: If page creation fails
        """
        client = await self._get_client(access_token)
        
        try:
            # Transform our model to Confluence API format
            confluence_payload = {
                "type": "page",
                "title": page_data.title,
                "space": {"key": page_data.space_key},
                "body": {
                    "storage": {
                        "value": page_data.body,
                        "representation": "storage"
                    }
                },
                "metadata": {
                    "labels": [{"name": label} for label in page_data.labels]
                }
            }
            
            if page_data.parent_id:
                confluence_payload["ancestors"] = [{"id": page_data.parent_id}]
            
            response = await client.post("/rest/api/content", json=confluence_payload)
            response.raise_for_status()
            
            # Get full page details
            page_id = response.json()["id"]
            return await self.get_page(access_token, page_id)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create Confluence page: {str(e)}"
            )

    # PUBLIC_INTERFACE
    async def get_page(
        self, 
        access_token: str,
        page_id: str
    ) -> ConfluencePageResponse:
        """
        Get a Confluence page by ID
        
        Args:
            access_token: OAuth access token
            page_id: Confluence page ID
            
        Returns:
            Page response
            
        Raises:
            HTTPException: If page retrieval fails
        """
        client = await self._get_client(access_token)
        
        try:
            response = await client.get(
                f"/rest/api/content/{page_id}",
                params={
                    "expand": "body.storage,version,ancestors,descendants.page,metadata.labels"
                }
            )
            response.raise_for_status()
            
            page_data = response.json()
            
            return ConfluencePageResponse(
                id=page_data["id"],
                title=page_data["title"],
                space_key=page_data["space"]["key"],
                body=page_data["body"]["storage"]["value"],
                status="published",  # Determine actual status
                url=f"{self.base_url}/wiki/spaces/{page_data['space']['key']}/pages/{page_data['id']}",
                version=page_data["version"],
                ancestors=page_data.get("ancestors", []),
                descendants=page_data.get("descendants", {}),
                labels=[label["name"] for label in page_data.get("metadata", {}).get("labels", [])],
                created_at=page_data["created"],
                updated_at=page_data["modified"]
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to get Confluence page: {str(e)}"
            )

    # PUBLIC_INTERFACE
    async def update_page(
        self,
        access_token: str,
        page_id: str,
        update_data: ConfluencePageUpdate
    ) -> ConfluencePageResponse:
        """
        Update a Confluence page
        
        Args:
            access_token: OAuth access token
            page_id: Confluence page ID
            update_data: Page update data
            
        Returns:
            Updated page response
            
        Raises:
            HTTPException: If page update fails
        """
        client = await self._get_client(access_token)
        
        try:
            # Get current page to get version number
            current_page = await self.get_page(access_token, page_id)
            
            # Build update payload
            confluence_payload: Dict[str, Any] = {
                "version": {
                    "number": current_page.version["number"] + 1
                }
            }
            
            if update_data.title is not None:
                confluence_payload["title"] = update_data.title
            if update_data.body is not None:
                confluence_payload["body"] = {
                    "storage": {
                        "value": update_data.body,
                        "representation": "storage"
                    }
                }
            if update_data.status is not None:
                confluence_payload["status"] = update_data.status.value
            if update_data.version_comment is not None:
                confluence_payload["version"]["message"] = update_data.version_comment
                
            response = await client.put(
                f"/rest/api/content/{page_id}",
                json=confluence_payload
            )
            response.raise_for_status()
            
            # Update labels if provided
            if update_data.labels is not None:
                await client.put(
                    f"/rest/api/content/{page_id}/label",
                    json=[{"name": label} for label in update_data.labels]
                )
            
            # Get updated page
            return await self.get_page(access_token, page_id)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update Confluence page: {str(e)}"
            )

    # PUBLIC_INTERFACE
    async def delete_page(
        self,
        access_token: str,
        page_id: str
    ) -> None:
        """
        Delete a Confluence page
        
        Args:
            access_token: OAuth access token
            page_id: Confluence page ID
            
        Raises:
            HTTPException: If page deletion fails
        """
        client = await self._get_client(access_token)
        
        try:
            response = await client.delete(f"/rest/api/content/{page_id}")
            response.raise_for_status()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete Confluence page: {str(e)}"
            )

    # PUBLIC_INTERFACE
    async def search_pages(
        self,
        access_token: str,
        cql: str,
        max_results: int = 50
    ) -> List[ConfluencePageResponse]:
        """
        Search Confluence pages using CQL
        
        Args:
            access_token: OAuth access token
            cql: CQL search query
            max_results: Maximum number of results to return
            
        Returns:
            List of matching pages
            
        Raises:
            HTTPException: If search fails
        """
        client = await self._get_client(access_token)
        
        try:
            response = await client.get(
                "/rest/api/content/search",
                params={
                    "cql": cql,
                    "limit": max_results,
                    "expand": "body.storage,version,ancestors,descendants.page,metadata.labels"
                }
            )
            response.raise_for_status()
            
            pages_data = response.json()["results"]
            return [
                await self.get_page(access_token, page["id"])
                for page in pages_data
            ]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to search Confluence pages: {str(e)}"
            )

# Create global service instance
confluence_service = ConfluenceService()
