import pytest

@pytest.mark.asyncio
async def test_create_subscription_success(client):
    payload = {
        "name": "CRM",
        "target_url": "https://example.com/webhook",
        "event_type": "lead.created",
        "secret": "abc123",
    }
    r = await client.post("/subscriptions", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "CRM"
    assert data["event_type"] == "lead.created"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_subscription_invalid_url_422(client):
    payload = {
        "name": "CRM",
        "target_url": "not-a-url",
        "event_type": "lead.created",
        "secret": "abc123",
    }
    r = await client.post("/subscriptions", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_subscriptions_filter_and_soft_delete(client):
    # Create 2 subs
    s1 = await client.post("/subscriptions", json={
        "name": "A",
        "target_url": "https://example.com/a",
        "event_type": "lead.created",
        "secret": "s1",
    })
    s2 = await client.post("/subscriptions", json={
        "name": "B",
        "target_url": "https://example.com/b",
        "event_type": "order.paid",
        "secret": "s2",
    })
    assert s1.status_code == 201 and s2.status_code == 201

    # Filter lead.created => solo 1
    r = await client.get("/subscriptions", params={"event_type": "lead.created"})
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Soft delete el primero
    sub_id = s1.json()["id"]
    d = await client.delete(f"/subscriptions/{sub_id}")
    assert d.status_code == 204

    # List sin filtro => solo debería quedar la activa no borrada
    r2 = await client.get("/subscriptions")
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["event_type"] == "order.paid"

@pytest.mark.asyncio
async def test_patch_subscription_updates_target_url_and_is_active(client):
    created = await client.post("/subscriptions", json={
        "name": "PatchMe",
        "target_url": "https://example.com/old",
        "event_type": "lead.created",
        "secret": "s",
    })
    sub_id = created.json()["id"]

    r = await client.patch(f"/subscriptions/{sub_id}", json={
        "target_url": "https://example.com/new",
        "is_active": False
    })
    assert r.status_code == 200
    data = r.json()
    assert data["target_url"] == "https://example.com/new"
    assert data["is_active"] is False