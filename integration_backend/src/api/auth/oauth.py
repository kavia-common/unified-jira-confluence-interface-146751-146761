from typing import Optional
from pydantic import BaseModel, HttpUrl
from fastapi import HTTPException, status

class OAuthConfig(BaseModel):
    """OAuth configuration model"""
    client_id: str
    client_secret: str
    authorize_url: HttpUrl
    token_url: HttpUrl
    redirect_uri: str
    scope: str


class OAuthState(BaseModel):
    """OAuth state model to prevent CSRF"""
    state: str
    redirect_uri: str


class OAuthToken(BaseModel):
    """OAuth token response model"""
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    scope: Optional[str] = None


# Configurations for JIRA and Confluence OAuth
# These should be moved to environment variables
JIRA_OAUTH_CONFIG = OAuthConfig(
    client_id="your-jira-client-id",  # TODO: Move to environment variables
    client_secret="your-jira-client-secret",
    authorize_url="https://auth.atlassian.com/authorize",
    token_url="https://auth.atlassian.com/oauth/token",
    redirect_uri="http://localhost:8000/auth/jira/callback",
    scope="read:jira-work write:jira-work"
)

CONFLUENCE_OAUTH_CONFIG = OAuthConfig(
    client_id="your-confluence-client-id",  # TODO: Move to environment variables
    client_secret="your-confluence-client-secret",
    authorize_url="https://auth.atlassian.com/authorize",
    token_url="https://auth.atlassian.com/oauth/token",
    redirect_uri="http://localhost:8000/auth/confluence/callback",
    scope="read:confluence-space.summary write:confluence-space"
)


class OAuthHandler:
    """Base OAuth handler class for JIRA and Confluence authentication"""
    
    def __init__(self, config: OAuthConfig):
        self.config = config

    # PUBLIC_INTERFACE
    def get_authorization_url(self, state: str) -> str:
        """
        Generate the authorization URL for OAuth flow
        
        Args:
            state: Random state string for CSRF protection
            
        Returns:
            Authorization URL string
        """
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": self.config.scope,
            "state": state,
            "prompt": "consent"
        }
        
        # Convert params to URL query string
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.authorize_url}?{query_string}"

    # PUBLIC_INTERFACE
    async def exchange_code_for_token(self, code: str) -> OAuthToken:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            OAuthToken containing access token and related information
            
        Raises:
            HTTPException: If token exchange fails
        """
        try:
            # TODO: Implement actual token exchange with JIRA/Confluence
            # This is a placeholder implementation
            return OAuthToken(
                access_token="placeholder-token",
                token_type="Bearer",
                refresh_token="placeholder-refresh-token",
                expires_in=3600,
                scope=self.config.scope
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code for token: {str(e)}"
            )


# Create handlers for JIRA and Confluence
jira_oauth = OAuthHandler(JIRA_OAUTH_CONFIG)
confluence_oauth = OAuthHandler(CONFLUENCE_OAUTH_CONFIG)
