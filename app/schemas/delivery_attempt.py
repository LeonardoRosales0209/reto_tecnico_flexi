from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class DeliveryAttemptGet(BaseModel):
    id: UUID
    subscription_id: UUID
    event_id: UUID
    status: str
    http_status_code: Optional[int] = None
    response_body: Optional[str] = None
    attempted_at: datetime