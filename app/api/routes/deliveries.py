from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from app.api.deps import get_db
from app.schemas.delivery_attempt import DeliveryAttemptGet
from app.models.delivery_attempt import DeliveryAttempt

from uuid import UUID

router = APIRouter(prefix="/deliveries", tags=["deliveries"])

@router.get("/{event_id}", response_model=List[DeliveryAttemptGet])
def get_deliveries_for_event(event_id: UUID, db: Session = Depends(get_db)):
    attempts = db.execute(
        select(DeliveryAttempt).where(DeliveryAttempt.event_id == event_id)
        .order_by(DeliveryAttempt.attempted_at.asc())
    ).scalars().all()
    return attempts