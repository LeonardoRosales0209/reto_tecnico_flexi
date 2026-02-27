import pytest

@pytest.mark.asyncio
async def test_create_subscription_sets_preview_fields_when_unfurl_succeeds(client, monkeypatch):
    # IMPORTANTE: ajusta el módulo donde se usa unfurl_preview
    # Si lo llamas en el service -> monkeypatch al service.
    # Si lo llamas directamente en el router -> monkeypatch al router.
    #
    # Ejemplo: si tu endpoint importa así:
    # from app.services.unfurl_service import unfurl_preview
    # entonces el patch debe hacerse sobre el módulo que lo usa (router/service), NO sobre unfurl_service.
    #
    # Ajusta esta línea según tu estructura:
    import app.api.routes.subscriptions as subs_module

    def fake_unfurl_preview(url: str, timeout: float = 5.0):
        return ("My Title", "My Description")

    monkeypatch.setattr(subs_module, "unfurl_preview", fake_unfurl_preview)

    payload = {
        "name": "CRM",
        "target_url": "https://example.com/webhook",
        "event_type": "lead.created",
        "secret": "abc123",
    }

    r = await client.post("/subscriptions", json=payload)
    assert r.status_code == 201

    data = r.json()
    assert data["preview_title"] == "My Title"
    assert data["preview_description"] == "My Description"


@pytest.mark.asyncio
async def test_create_subscription_returns_null_preview_fields_when_unfurl_fails(client, monkeypatch):
    import app.api.routes.subscriptions as subs_module

    def fake_unfurl_preview_raises(url: str, timeout: float = 5.0):
        raise RuntimeError("unfurl failed")

    monkeypatch.setattr(subs_module, "unfurl_preview", fake_unfurl_preview_raises)

    payload = {
        "name": "CRM",
        "target_url": "https://example.com/webhook",
        "event_type": "lead.created",
        "secret": "abc123",
    }

    r = await client.post("/subscriptions", json=payload)
    assert r.status_code == 201

    data = r.json()
    assert data["preview_title"] is None
    assert data["preview_description"] is None