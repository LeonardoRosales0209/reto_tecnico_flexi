from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class DeliveryAttemptGet(BaseModel):
    id: int
    subscription_id: int
    event_id: int
    status: str
    http_status_code: Optional[int] = None
    response_body: Optional[str] = None
    attempted_at: datetime