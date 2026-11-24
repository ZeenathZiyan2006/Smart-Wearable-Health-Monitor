import logging
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.escalation_service import escalation_service
from app.workers.celery_app import celery_app

logger = logging.getLogger("pulseguardian.workers")


@celery_app.task(name="escalate_emergency_alert", bind=True, max_retries=3)
def escalate_emergency_alert(self, alert_id: int, target_tier: int = 1):
    """
    Durable Celery task for executing a caregiver escalation step and scheduling
    the subsequent timeout check if unacknowledged.
    """
    db = SessionLocal()
    try:
        result = escalation_service.execute_escalation_tier(db, alert_id, target_tier)
        logger.info(f"[CELERY] Escalation step completed for alert {alert_id}, tier {target_tier}: {result}")

        # If escalation should advance to next tier upon timeout and alert was not halted
        if result.get("status") == "escalated" and result.get("has_next_tier"):
            next_tier = result.get("next_tier")
            timeout = result.get("timeout_seconds", settings.EMERGENCY_ACK_TIMEOUT_SECONDS)
            logger.info(f"[CELERY] Scheduling tier {next_tier} escalation for alert {alert_id} in {timeout}s")
            escalate_emergency_alert.apply_async(
                args=[alert_id, next_tier],
                countdown=timeout
            )

        return result
    except Exception as exc:
        logger.error(f"[CELERY] Error processing escalation for alert {alert_id}: {exc}", exc_info=True)
        db.rollback()
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()


def dispatch_emergency_escalation(alert_id: int, initial_tier: int = 1) -> None:
    """
    Initiates emergency escalation via Celery background worker.
    Gracefully falls back to synchronous execution if the message broker is unreachable.
    """
    try:
        escalate_emergency_alert.apply_async(args=[alert_id, initial_tier])
        logger.info(f"Dispatched background Celery task for alert {alert_id}, tier {initial_tier}")
    except Exception as exc:
        logger.warning(
            f"Celery message broker unreachable ({exc}). Falling back to immediate execution for alert {alert_id}."
        )
        db = SessionLocal()
        try:
            escalation_service.execute_escalation_tier(db, alert_id, initial_tier)
        finally:
            db.close()
