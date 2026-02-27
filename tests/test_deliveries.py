import pytest
from datetime import datetime, timezone
from sqlalchemy import select

from app.models.subscription import Subscription
from app.models.event import EventPayload
from app.models.delivery_attempt import DeliveryAttempt

@pytest.mark.asyncio
async def test_get_deliveries_for_event_returns_attempts(client, db_session):
    # Crear subscription + event directo en DB
    sub = Subscription(
        name="S",
        target_url="https://example.com/x",
        event_type="lead.created",
        secret="sec",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        deleted_at=None,
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    ev = EventPayload(
        event_type="lead.created",
        payload={"id": 1},
        occurred_at=datetime.now(timezone.utc),
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    att = DeliveryAttempt(
        subscription_id=sub.id,
        event_id=ev.id,
        status="failed",
        http_status_code=500,
        response_body="err",
        attempted_at=datetime.now(timezone.utc),
    )
    db_session.add(att)
    db_session.commit()

    r = await client.get(f"/deliveries/{ev.id}")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["event_id"] == ev.id
    assert items[0]["subscription_id"] == sub.id
    assert items[0]["status"] == "failed"