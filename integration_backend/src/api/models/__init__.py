from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class TimestampMixin(BaseModel):
    """Base mixin to add timestamp fields to models"""
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
