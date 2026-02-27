from datetime import datetime, timedelta, timezone
from celery import shared_task
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.subscription import Subscription
from app.models.delivery_attempt import DeliveryAttempt
from app.models.event import EventPayload
from app.tasks.webhook_tasks import deliver_webhook


def _get_db() -> Session:
    return SessionLocal()


@shared_task(name="health_check_subscriptions")
def health_check_subscriptions():
    """
    Every 5 minutes:
    - Find active subscriptions with NO successful delivery in last 2 hours
    - Publish synthetic event 'health.check' for each
    - Log how many checked and how many failed
    """

    db = _get_db()
    try:
        now = datetime.now(timezone.utc)
        two_hours_ago = now - timedelta(hours=2)

        # Subquery: last successful attempt per subscription
        subquery = (
            select(
                DeliveryAttempt.subscription_id,
                func.max(DeliveryAttempt.attempted_at).label("last_success")
            )
            .where(DeliveryAttempt.status == "success")
            .group_by(DeliveryAttempt.subscription_id)
            .subquery()
        )

        # Main query:
        # Subscriptions activas donde:
        #   - no existe success
        #   OR
        #   - el último success fue hace más de 2 horas
        stmt = (
            select(Subscription)
            .outerjoin(
                subquery,
                Subscription.id == subquery.c.subscription_id
            )
            .where(
                Subscription.is_active == True,
                Subscription.deleted_at.is_(None),
                (
                    (subquery.c.last_success.is_(None)) |
                    (subquery.c.last_success < two_hours_ago)
                )
            )
        )

        subs = db.execute(stmt).scalars().all()

        total_checked = len(subs)
        total_failed = 0

        for sub in subs:
            # Crear evento sintético
            event = EventPayload(
                event_type="health.check",
                payload={"subscription_id": sub.id},
                occurred_at=now,
            )
            db.add(event)
            db.commit()
            db.refresh(event)

            # Encolar como cualquier evento
            deliver_webhook.delay(sub.id, event.id)

            total_failed += 1

        print(
            f"[HEALTH CHECK] Checked: {total_checked} | "
            f"Health events generated: {total_failed}"
        )

    finally:
        db.close()