from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from enum import Enum
from ..models import TimestampMixin

class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username for login")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    role: UserRole = Field(default=UserRole.USER, description="User's role in the system")

# PUBLIC_INTERFACE
class UserCreate(UserBase):
    """Model for creating new users"""
    password: str = Field(..., min_length=8, description="User's password")

# PUBLIC_INTERFACE
class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8)

# PUBLIC_INTERFACE
class UserResponse(UserBase, TimestampMixin):
    """Model for user responses, excluding sensitive information"""
    id: int = Field(..., description="Unique user identifier")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    jira_connected: bool = Field(default=False, description="Whether user has connected JIRA account")
    confluence_connected: bool = Field(default=False, description="Whether user has connected Confluence account")

    class Config:
        from_attributes = True
