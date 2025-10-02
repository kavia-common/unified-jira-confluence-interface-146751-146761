from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from enum import Enum
from ..models import TimestampMixin

class IssueType(str, Enum):
    """JIRA issue type enumeration"""
    STORY = "story"
    TASK = "task"
    BUG = "bug"
    EPIC = "epic"

class IssuePriority(str, Enum):
    """JIRA issue priority enumeration"""
    HIGHEST = "highest"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    LOWEST = "lowest"

class IssueStatus(str, Enum):
    """JIRA issue status enumeration"""
    TODO = "to_do"
    IN_PROGRESS = "in_progress"
    DONE = "done"

# PUBLIC_INTERFACE
class JiraIssueBase(BaseModel):
    """Base JIRA issue model with common fields"""
    title: str = Field(..., min_length=1, max_length=255, description="Issue title")
    description: Optional[str] = Field(None, description="Issue description")
    issue_type: IssueType = Field(..., description="Type of the issue")
    priority: IssuePriority = Field(default=IssuePriority.MEDIUM, description="Issue priority")
    status: IssueStatus = Field(default=IssueStatus.TODO, description="Current status of the issue")

# PUBLIC_INTERFACE
class JiraIssueCreate(JiraIssueBase):
    """Model for creating new JIRA issues"""
    project_key: str = Field(..., description="JIRA project key")
    assignee: Optional[str] = Field(None, description="Username of assignee")
    labels: List[str] = Field(default=[], description="Issue labels")

# PUBLIC_INTERFACE
class JiraIssueUpdate(BaseModel):
    """Model for updating JIRA issues"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[IssuePriority] = None
    status: Optional[IssueStatus] = None
    assignee: Optional[str] = None
    labels: Optional[List[str]] = None

# PUBLIC_INTERFACE
class JiraIssueResponse(JiraIssueBase, TimestampMixin):
    """Model for JIRA issue responses"""
    id: str = Field(..., description="JIRA issue identifier")
    key: str = Field(..., description="JIRA issue key")
    url: HttpUrl = Field(..., description="URL to the issue in JIRA")
    project_key: str = Field(..., description="JIRA project key")
    assignee: Optional[Dict] = Field(None, description="Assignee information")
    reporter: Dict = Field(..., description="Reporter information")
    labels: List[str] = Field(default=[], description="Issue labels")

    class Config:
        from_attributes = True
