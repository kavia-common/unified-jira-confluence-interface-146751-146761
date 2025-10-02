from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from httpx import AsyncClient

from ..models.jira import (
    JiraIssueCreate,
    JiraIssueUpdate,
    JiraIssueResponse
)


class JiraService:
    """Service class for handling JIRA operations"""
    
    def __init__(self, base_url: str = "https://api.atlassian.com/ex/jira/"):
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
    async def create_issue(
        self, 
        access_token: str,
        issue_data: JiraIssueCreate
    ) -> JiraIssueResponse:
        """
        Create a new JIRA issue
        
        Args:
            access_token: OAuth access token
            issue_data: Issue creation data
            
        Returns:
            Created issue response
            
        Raises:
            HTTPException: If issue creation fails
        """
        client = await self._get_client(access_token)
        
        try:
            # Transform our model to JIRA API format
            jira_payload = {
                "fields": {
                    "project": {"key": issue_data.project_key},
                    "summary": issue_data.title,
                    "description": issue_data.description,
                    "issuetype": {"name": issue_data.issue_type.value},
                    "priority": {"name": issue_data.priority.value},
                    "labels": issue_data.labels
                }
            }
            
            if issue_data.assignee:
                jira_payload["fields"]["assignee"] = {"name": issue_data.assignee}
            
            response = await client.post("/rest/api/2/issue", json=jira_payload)
            response.raise_for_status()
            
            # Get full issue details
            issue_key = response.json()["key"]
            return await self.get_issue(access_token, issue_key)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create JIRA issue: {str(e)}"
            )

    # PUBLIC_INTERFACE
    async def get_issue(
        self, 
        access_token: str,
        issue_key: str
    ) -> JiraIssueResponse:
        """
        Get a JIRA issue by key
        
        Args:
            access_token: OAuth access token
            issue_key: JIRA issue key
            
        Returns:
            Issue response
            
        Raises:
            HTTPException: If issue retrieval fails
        """
        client = await self._get_client(access_token)
        
        try:
            response = await client.get(f"/rest/api/2/issue/{issue_key}")
            response.raise_for_status()
            
            issue_data = response.json()
            fields = issue_data["fields"]
            
            return JiraIssueResponse(
                id=issue_data["id"],
                key=issue_data["key"],
                title=fields["summary"],
                description=fields.get("description"),
                issue_type=fields["issuetype"]["name"],
                priority=fields["priority"]["name"],
                status=fields["status"]["name"],
                url=f"{self.base_url}/browse/{issue_data['key']}",
                project_key=fields["project"]["key"],
                assignee=fields.get("assignee"),
                reporter=fields["reporter"],
                labels=fields.get("labels", []),
                created_at=fields["created"],
                updated_at=fields["updated"]
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to get JIRA issue: {str(e)}"
            )

    # PUBLIC_INTERFACE
    async def update_issue(
        self,
        access_token: str,
        issue_key: str,
        update_data: JiraIssueUpdate
    ) -> JiraIssueResponse:
        """
        Update a JIRA issue
        
        Args:
            access_token: OAuth access token
            issue_key: JIRA issue key
            update_data: Issue update data
            
        Returns:
            Updated issue response
            
        Raises:
            HTTPException: If issue update fails
        """
        client = await self._get_client(access_token)
        
        try:
            # Build update payload
            fields: Dict[str, Any] = {}
            
            if update_data.title is not None:
                fields["summary"] = update_data.title
            if update_data.description is not None:
                fields["description"] = update_data.description
            if update_data.priority is not None:
                fields["priority"] = {"name": update_data.priority.value}
            if update_data.status is not None:
                fields["status"] = {"name": update_data.status.value}
            if update_data.assignee is not None:
                fields["assignee"] = {"name": update_data.assignee}
            if update_data.labels is not None:
                fields["labels"] = update_data.labels
                
            response = await client.put(
                f"/rest/api/2/issue/{issue_key}",
                json={"fields": fields}
            )
            response.raise_for_status()
            
            # Get updated issue
            return await self.get_issue(access_token, issue_key)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update JIRA issue: {str(e)}"
            )

    # PUBLIC_INTERFACE
    async def delete_issue(
        self,
        access_token: str,
        issue_key: str
    ) -> None:
        """
        Delete a JIRA issue
        
        Args:
            access_token: OAuth access token
            issue_key: JIRA issue key
            
        Raises:
            HTTPException: If issue deletion fails
        """
        client = await self._get_client(access_token)
        
        try:
            response = await client.delete(f"/rest/api/2/issue/{issue_key}")
            response.raise_for_status()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete JIRA issue: {str(e)}"
            )

    # PUBLIC_INTERFACE
    async def search_issues(
        self,
        access_token: str,
        jql: str,
        max_results: int = 50
    ) -> List[JiraIssueResponse]:
        """
        Search JIRA issues using JQL
        
        Args:
            access_token: OAuth access token
            jql: JQL search query
            max_results: Maximum number of results to return
            
        Returns:
            List of matching issues
            
        Raises:
            HTTPException: If search fails
        """
        client = await self._get_client(access_token)
        
        try:
            response = await client.post(
                "/rest/api/2/search",
                json={
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": ["*all"]
                }
            )
            response.raise_for_status()
            
            issues_data = response.json()["issues"]
            return [
                await self.get_issue(access_token, issue["key"])
                for issue in issues_data
            ]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to search JIRA issues: {str(e)}"
            )

# Create global service instance
jira_service = JiraService()
