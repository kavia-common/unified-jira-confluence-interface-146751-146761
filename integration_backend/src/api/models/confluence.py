from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from enum import Enum
from ..models import TimestampMixin

class PageStatus(str, Enum):
    """Confluence page status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

# PUBLIC_INTERFACE
class ConfluencePageBase(BaseModel):
    """Base Confluence page model with common fields"""
    title: str = Field(..., min_length=1, max_length=255, description="Page title")
    space_key: str = Field(..., description="Confluence space key")
    body: str = Field(..., description="Page content in storage format")
    status: PageStatus = Field(default=PageStatus.DRAFT, description="Current status of the page")

# PUBLIC_INTERFACE
class ConfluencePageCreate(ConfluencePageBase):
    """Model for creating new Confluence pages"""
    parent_id: Optional[str] = Field(None, description="ID of the parent page")
    labels: List[str] = Field(default=[], description="Page labels")

# PUBLIC_INTERFACE
class ConfluencePageUpdate(BaseModel):
    """Model for updating Confluence pages"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    body: Optional[str] = None
    status: Optional[PageStatus] = None
    labels: Optional[List[str]] = None
    version_comment: Optional[str] = Field(None, description="Comment for this version")

# PUBLIC_INTERFACE
class ConfluencePageResponse(ConfluencePageBase, TimestampMixin):
    """Model for Confluence page responses"""
    id: str = Field(..., description="Confluence page identifier")
    url: HttpUrl = Field(..., description="URL to the page in Confluence")
    version: Dict = Field(..., description="Version information")
    ancestors: List[Dict] = Field(default=[], description="List of ancestor pages")
    descendants: Optional[Dict] = Field(None, description="Information about child pages")
    labels: List[str] = Field(default=[], description="Page labels")

    class Config:
        from_attributes = True
