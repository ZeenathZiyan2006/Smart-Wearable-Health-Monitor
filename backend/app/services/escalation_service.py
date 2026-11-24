import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.emergency import EmergencyAlert, EscalationAuditLog
from app.models.location import LocationLog
from app.models.user import (
    CaregiverProfile,
    PatientCaregiverAssociation,
    PatientProfile,
    User,
)
from app.services.notification_service import notification_service

logger = logging.getLogger("pulseguardian.escalation")


class EscalationService:
    """
    Manages the multi-tier caregiver escalation ladder for emergency alerts.
    Dispatches notifications sequentially by tier, enforces timeouts, ensures
    idempotency, and halts immediately upon caregiver acknowledgment.
    """

    def __init__(self, notif_service=None):
        self._notif_service = notif_service

    @property
    def notification_service(self):
        return self._notif_service or notification_service

    @notification_service.setter
    def notification_service(self, service):
        self._notif_service = service

    def execute_escalation_tier(
        self,
        db: Session,
        alert_id: int,
        target_tier: int = 1
    ) -> Dict[str, Any]:
        """
        Processes a single escalation tier for an emergency alert.
        Returns execution status and indicates whether a subsequent tier timeout should be scheduled.
        """
        # 1. Fetch Alert
        alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
        if not alert:
            return {"status": "error", "message": f"Alert {alert_id} not found"}

        # 2. Check if escalation should halt (Caregiver already acknowledged or rejected)
        if alert.status in ["acknowledged", "rejected", "resolved"]:
            logger.info(f"Escalation halted for alert {alert_id}: status is already '{alert.status}'")
            return {
                "status": "halted",
                "alert_status": alert.status,
                "message": f"Escalation stopped because alert is {alert.status}."
            }

        # 3. Retrieve patient details
        patient = db.query(PatientProfile).filter(PatientProfile.id == alert.patient_id).first()
        patient_name = patient.user.full_name if patient and patient.user else f"Patient #{alert.patient_id}"

        # Format location summary
        loc_str = "Location unavailable"
        if alert.latitude is not None and alert.longitude is not None:
            loc_str = f"Lat: {alert.latitude:.4f}, Lon: {alert.longitude:.4f}"
            if alert.location_accuracy:
                loc_str += f" (±{alert.location_accuracy:.1f}m)"

        # 4. Fetch caregivers assigned to this patient
        associations = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.patient_id == alert.patient_id
        ).order_by(PatientCaregiverAssociation.escalation_tier.asc()).all()

        if not associations:
            logger.warning(f"No caregivers linked to patient {alert.patient_id} for alert {alert_id}")
            # Log unassigned escalation audit
            audit = EscalationAuditLog(
                alert_id=alert.id,
                tier=target_tier,
                notified_caregiver_id=None,
                notification_channel="system",
                provider="development_mock",
                status="failed",
                message_payload=f"No caregivers assigned to patient {alert.patient_id}",
                error_message="No caregiver associations configured."
            )
            db.add(audit)
            db.commit()
            return {"status": "no_caregivers_assigned"}

        # 5. Find caregivers at the target tier
        tier_associations = [a for a in associations if a.escalation_tier == target_tier]

        # If no caregiver at exact target tier, search for next available higher tier
        if not tier_associations:
            higher_tiers = [a for a in associations if a.escalation_tier > target_tier]
            if higher_tiers:
                next_available_tier = higher_tiers[0].escalation_tier
                return EscalationService.execute_escalation_tier(db, alert_id, next_available_tier)
            else:
                alert.status = "timeout_exhausted"
                db.commit()
                return {"status": "exhausted", "message": "All caregiver tiers exhausted without acknowledgment."}

        # 6. Idempotency check: verify if this tier was already successfully dispatched
        already_dispatched = db.query(EscalationAuditLog).filter(
            EscalationAuditLog.alert_id == alert.id,
            EscalationAuditLog.tier == target_tier,
            EscalationAuditLog.status.in_(["dispatched_mock", "delivered"])
        ).first()

        if already_dispatched:
            logger.info(f"Tier {target_tier} for alert {alert_id} was already dispatched. Skipping duplicate.")
            return {"status": "already_dispatched", "tier": target_tier}

        # 7. Dispatch notifications to all caregivers at target tier
        dispatched_count = 0
        for assoc in tier_associations:
            cg = assoc.caregiver
            cg_user = cg.user if cg else None
            if not cg_user:
                continue

            phone = cg_user.phone_number
            email = cg_user.email
            channel = cg.notification_preference or "all"

            # Execute dispatch with retry safety
            result = None
            retry_count = 0
            max_retries = 2

            for attempt in range(max_retries + 1):
                result = self.notification_service.dispatch_alert(
                    recipient_phone=phone,
                    recipient_email=email,
                    preferred_channel=channel,
                    patient_name=patient_name,
                    alert_type=alert.alert_type,
                    severity=alert.severity,
                    tier=target_tier,
                    location_summary=loc_str,
                    assistance_message=alert.assistance_message
                )
                if result.success:
                    break
                retry_count += 1

            audit = EscalationAuditLog(
                alert_id=alert.id,
                tier=target_tier,
                notified_caregiver_id=cg.id,
                notification_channel=result.channel,
                provider=result.provider,
                recipient_address=result.recipient,
                status=result.status,
                message_payload=f"Alert: {alert.alert_type} | Severity: {alert.severity} | Location: {loc_str}",
                error_message=result.error_message,
                retry_count=retry_count
            )
            db.add(audit)
            dispatched_count += 1

        alert.current_escalation_tier = target_tier
        if alert.status == "triggered":
            alert.status = "escalating"

        db.commit()
        db.refresh(alert)

        # 8. Check if subsequent higher tier exists
        higher_tiers = [a for a in associations if a.escalation_tier > target_tier]
        has_next_tier = len(higher_tiers) > 0
        next_tier_number = higher_tiers[0].escalation_tier if has_next_tier else None

        return {
            "status": "escalated",
            "tier": target_tier,
            "dispatched_count": dispatched_count,
            "has_next_tier": has_next_tier,
            "next_tier": next_tier_number,
            "timeout_seconds": settings.EMERGENCY_ACK_TIMEOUT_SECONDS
        }


escalation_service = EscalationService()
