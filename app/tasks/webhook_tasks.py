import json
import httpx
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import sign_hmac_sha256
from app.models.subscription import Subscription
from app.models.event import EventPayload
from app.models.delivery_attempt import DeliveryAttempt

from uuid import UUID

# Backoff requerido: 30s, luego 90s, luego fail (máximo 3 intentos)
BACKOFF_SECONDS = [30, 90]  # after attempt 1 -> 30s, after attempt 2 -> 90s

def _get_db() -> Session:
    return SessionLocal()

def _record_attempt(
    db: Session,
    subscription_id: UUID,
    event_id: UUID,
    status: str,
    http_status_code: int | None,
    response_body: str | None,
):
    attempt = DeliveryAttempt(
        subscription_id=subscription_id,
        event_id=event_id,
        status=status,
        http_status_code=http_status_code,
        response_body=response_body,
    )
    db.add(attempt)
    db.commit()

@shared_task(bind=True, name="deliver_webhook")
def deliver_webhook(self, subscription_id: UUID, event_id: UUID) -> None:
    """
    Worker task:
    - POST to target_url with event payload
    - header X-Hookshot-Signature = HMAC-SHA256(payload_bytes, secret)
    - record every attempt
    - retry with backoff if 5xx or timeout/no response: 30s then 90s then fail
    """
    db = _get_db()
    try:
        sub = db.execute(
            select(Subscription).where(
                Subscription.id == subscription_id,
                Subscription.deleted_at.is_(None),
            )
        ).scalar_one_or_none()

        event = db.execute(
            select(EventPayload).where(EventPayload.id == event_id)
        ).scalar_one_or_none()

        if not sub or not sub.is_active or not event:
            # No retry: invalid state
            return

        # Body: payload libre (JSON). Mantén orden estable para firma.
        body_dict = event.payload if isinstance(event.payload, dict) else dict(event.payload)
        body_bytes = json.dumps(body_dict, separators=(",", ":"), sort_keys=True).encode("utf-8")

        signature = sign_hmac_sha256(sub.secret, body_bytes)

        headers = {
            "Content-Type": "application/json",
            "X-Hookshot-Signature": signature,
        }

        # Timeout razonable para webhook
        timeout = httpx.Timeout(10.0)

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(sub.target_url, content=body_bytes, headers=headers)

            # Registrar intento
            resp_text = resp.text[:5000] if resp.text else None  # evita guardar responses gigantes
            if 200 <= resp.status_code < 300:
                _record_attempt(db, sub.id, event.id, "success", resp.status_code, resp_text)
                return

            # Si 5xx -> retry según reglas; 4xx -> fail sin retry (criterio común)
            if 500 <= resp.status_code <= 599:
                _record_attempt(db, sub.id, event.id, "failed", resp.status_code, resp_text)
                raise httpx.HTTPStatusError("5xx from target", request=resp.request, response=resp)

            # 4xx y otros: no reintentar
            _record_attempt(db, sub.id, event.id, "failed", resp.status_code, resp_text)
            return

        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
            # timeout/no response/5xx: reintentar con backoff 30s luego 90s, máximo 3 intentos
            # self.request.retries = cantidad de reintentos ya hechos
            retries_done = getattr(self.request, "retries", 0)

            # Intento actual = retries_done + 1
            # Máx total de intentos: 3 (1 inicial + 2 retries)
            if retries_done >= 2:
                # Ya se hicieron 2 retries => estamos en el 3er intento fallido: marcar fail definitivo
                # (Ya registramos el intento como failed arriba cuando hubo response 5xx;
                #  para timeout/transport, registra aquí)
                if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
                    _record_attempt(db, sub.id, event.id, "failed", None, str(exc)[:5000])
                return

            # Registra intento fallido si fue timeout/transport (sin status code)
            if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
                _record_attempt(db, sub.id, event.id, "failed", None, str(exc)[:5000])

            countdown = BACKOFF_SECONDS[retries_done]  # 0->30, 1->90
            raise self.retry(exc=exc, countdown=countdown)

    finally:
        db.close()