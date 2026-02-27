from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel, Field

class EventCreate(BaseModel):
    event_type: str = Field(min_length=1)
    payload: Dict[str, Any]
    occurred_at: datetime