import pytest
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_publish_event_enqueues_matching_subscriptions(client, monkeypatch):
    # Crear 2 subs del mismo event_type
    await client.post("/subscriptions", json={
        "name": "S1",
        "target_url": "https://example.com/1",
        "event_type": "lead.created",
        "secret": "a",
    })
    await client.post("/subscriptions", json={
        "name": "S2",
        "target_url": "https://example.com/2",
        "event_type": "lead.created",
        "secret": "b",
    })
    # Y otra de otro tipo
    await client.post("/subscriptions", json={
        "name": "S3",
        "target_url": "https://example.com/3",
        "event_type": "order.paid",
        "secret": "c",
    })

    calls = {"count": 0}

    # Ajusta el import a donde uses deliver_webhook en tu router /events
    # Ej: from app.api.routes.events import deliver_webhook
    from app.api.routes import events as events_router_module

    def fake_delay(subscription_id, event_id):
        calls["count"] += 1

    monkeypatch.setattr(events_router_module.deliver_webhook, "delay", fake_delay)

    payload = {
        "event_type": "lead.created",
        "payload": {"id": 123},
        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    r = await client.post("/events", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["subscriptions_matched"] == 2
    assert calls["count"] == 2