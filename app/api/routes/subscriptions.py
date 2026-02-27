from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import List, Optional

from app.api.deps import get_db
from app.schemas.subscription import SubscriptionCreate, SubscriptionGet, SubscriptionUpdate
from app.models.subscription import Subscription
from datetime import datetime, timezone

from uuid import UUID

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

def utcnow():
    return datetime.now(timezone.utc)

@router.post("", response_model=SubscriptionGet, status_code=status.HTTP_201_CREATED)
def create_subscription(data: SubscriptionCreate, db: Session = Depends(get_db)):
    sub = Subscription(
        name=data.name,
        target_url=str(data.target_url),
        event_type=data.event_type,
        secret=data.secret,
        is_active=True,
        created_at=utcnow(),
        deleted_at=None,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

@router.get("", response_model=List[SubscriptionGet])
def list_active_subscriptions(
    event_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Subscription).where(
        Subscription.is_active == True,  # noqa: E712
        Subscription.deleted_at.is_(None),
    )
    if event_type:
        stmt = stmt.where(Subscription.event_type == event_type)

    subs = db.execute(stmt).scalars().all()
    return subs

@router.get("/{subscription_id}", response_model=SubscriptionGet)
def get_subscription(subscription_id: UUID, db: Session = Depends(get_db)):
    stmt = select(Subscription).where(
        Subscription.id == subscription_id,
        Subscription.deleted_at.is_(None),
    )
    sub = db.execute(stmt).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub

@router.patch("/{subscription_id}", response_model=SubscriptionGet)
def patch_subscription(subscription_id: UUID, data: SubscriptionUpdate, db: Session = Depends(get_db)):
    values = {}
    if data.is_active is not None:
        values["is_active"] = data.is_active
    if data.target_url is not None:
        values["target_url"] = str(data.target_url)

    if not values:
        raise HTTPException(status_code=422, detail="No valid fields to update")

    sub = db.execute(
        select(Subscription).where(Subscription.id == subscription_id, Subscription.deleted_at.is_(None))
    ).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.execute(
        update(Subscription)
        .where(Subscription.id == subscription_id)
        .values(**values)
    )
    db.commit()

    db.refresh(sub)
    return sub

@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_subscription(subscription_id: UUID, db: Session = Depends(get_db)):
    sub = db.execute(
        select(Subscription).where(Subscription.id == subscription_id, Subscription.deleted_at.is_(None))
    ).scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    sub.deleted_at = utcnow()
    sub.is_active = False
    db.commit()
    return None