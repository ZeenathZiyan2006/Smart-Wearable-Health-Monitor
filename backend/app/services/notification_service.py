import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger("pulseguardian.notifications")


@dataclass
class NotificationResult:
    success: bool
    provider: str
    status: str
    channel: str
    recipient: str
    message_id: str
    error_message: Optional[str] = None


class BaseNotificationAdapter(ABC):
    """Abstract base class for notification dispatch channels."""
    @abstractmethod
    def send(
        self,
        recipient: str,
        channel: str,
        title: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        pass


class MockDevelopmentNotificationAdapter(BaseNotificationAdapter):
    """
    Explicitly labeled development/mock adapter used when real external gateway
    credentials (e.g. Twilio, FCM, SendGrid) are not configured.
    Labels every dispatch with provider='development_mock' and status='dispatched_mock'.
    """
    def __init__(self, simulate_failure: bool = False):
        self.simulate_failure = simulate_failure

    def send(
        self,
        recipient: str,
        channel: str,
        title: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationResult:
        msg_id = f"mock-msg-{uuid.uuid4().hex[:8]}"

        if self.simulate_failure:
            logger.warning(
                f"[DEVELOPMENT_MOCK] Simulated delivery failure for recipient '{recipient}' on channel '{channel}'"
            )
            return NotificationResult(
                success=False,
                provider="development_mock",
                status="failed",
                channel=channel,
                recipient=recipient,
                message_id=msg_id,
                error_message="Simulated mock gateway network timeout error"
            )

        logger.info(
            f"[DEVELOPMENT_MOCK] Dispatched emergency notification via channel '{channel}' to '{recipient}': "
            f"Title='{title}', Body='{body}'"
        )

        return NotificationResult(
            success=True,
            provider="development_mock",
            status="dispatched_mock",
            channel=channel,
            recipient=recipient,
            message_id=msg_id,
            error_message=None
        )


class NotificationService:
    """
    Modular notification dispatcher supporting Push, SMS, Email and system channels.
    Falls back safely to the clearly labeled MockDevelopmentNotificationAdapter.
    """
    def __init__(self, adapter: Optional[BaseNotificationAdapter] = None):
        self.adapter = adapter or MockDevelopmentNotificationAdapter()

    def dispatch_alert(
        self,
        recipient_phone: Optional[str],
        recipient_email: Optional[str],
        preferred_channel: str,
        patient_name: str,
        alert_type: str,
        severity: str,
        tier: int,
        location_summary: str,
        assistance_message: Optional[str] = None
    ) -> NotificationResult:
        """
        Dispatches an emergency notification to a designated caregiver.
        """
        title = f"EMERGENCY: PulseGuardian Alert ({severity.upper()}) - {patient_name}"
        body_parts = [
            f"Emergency event: {alert_type.replace('_', ' ').title()}",
            f"Escalation Tier: {tier}",
            f"Location: {location_summary}"
        ]
        if assistance_message:
            body_parts.append(f"Message from patient: '{assistance_message}'")

        body = " | ".join(body_parts)

        # Determine target recipient address based on channel
        channel = preferred_channel.lower()
        if channel == "sms":
            recipient = recipient_phone or recipient_email or "unknown-phone"
        elif channel == "email":
            recipient = recipient_email or recipient_phone or "unknown-email"
        else:
            # push or all
            recipient = recipient_phone or recipient_email or "caregiver-device-token"

        return self.adapter.send(
            recipient=recipient,
            channel=channel,
            title=title,
            body=body,
            metadata={
                "patient_name": patient_name,
                "tier": tier,
                "alert_type": alert_type,
                "severity": severity
            }
        )


notification_service = NotificationService()
