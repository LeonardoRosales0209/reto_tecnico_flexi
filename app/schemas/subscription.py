from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, AnyUrl, Field

class SubscriptionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    target_url: AnyUrl
    event_type: str = Field(min_length=1)
    secret: str = Field(min_length=1)

class SubscriptionUpdate(BaseModel):
    is_active: Optional[bool] = None
    target_url: Optional[AnyUrl] = None

class SubscriptionGet(BaseModel):
    id: UUID
    name: str
    target_url: str
    event_type: str
    is_active: bool
    created_at: datetime

    preview_title: str | None = None
    preview_description: str | None = None
