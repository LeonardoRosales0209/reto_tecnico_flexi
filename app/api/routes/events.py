from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.schemas.event import EventCreate
from app.models.event import EventPayload
from app.models.subscription import Subscription

from app.tasks.webhook_tasks import deliver_webhook

router = APIRouter(prefix="/events", tags=["events"])

@router.post("", status_code=status.HTTP_201_CREATED)
def publish_event(data: EventCreate, db: Session = Depends(get_db)):
    event = EventPayload(
        event_type=data.event_type,
        payload=data.payload,
        occurred_at=data.occurred_at,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    subs = db.execute(
        select(Subscription).where(
            Subscription.deleted_at.is_(None),
            Subscription.is_active == True,
            Subscription.event_type == data.event_type,
        )
    ).scalars().all()

    for sub in subs:
        deliver_webhook.delay(sub.id, event.id)

    return {
        "event_id": event.id,
        "subscriptions_matched": len(subs),
        "message": "Event stored and deliveries enqueued."
    }