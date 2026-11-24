from datetime import datetime, timezone
import pytest

from app.models.location import LocationLog
from app.models.user import CaregiverProfile, PatientCaregiverAssociation, User
from app.services.escalation_service import escalation_service
from app.services.notification_service import (
    MockDevelopmentNotificationAdapter,
    NotificationService,
)


def test_manual_sos_trigger_as_patient(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "alert_type": "manual_sos",
        "severity": "critical",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "location_accuracy": 5.0
    }
    response = client.post("/api/v1/emergency/sos", json=payload, headers=headers)
    assert response.status_code == 201
    alert = response.json()
    assert alert["patient_id"] == test_patient_user.patient_profile.id
    assert alert["alert_type"] == "manual_sos"
    assert alert["severity"] == "critical"
    assert alert["latitude"] == 12.9716
    assert alert["longitude"] == 77.5946
    assert alert["status"] in ["triggered", "escalating"]


def test_sos_auto_populates_latest_gps_when_omitted(client, test_patient_user, db_session):
    # Pre-record a GPS fix for this patient in LocationLog
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)
    loc = LocationLog(
        patient_id=patient_id,
        latitude=12.9350,
        longitude=77.5350,
        accuracy=4.2,
        is_gps_available=True,
        recorded_at=now
    )
    db_session.add(loc)
    db_session.commit()

    # Hardware sends SOS without GPS coords in payload
    payload = {
        "device_uuid": "PG-ESP32-001",
        "alert_type": "fall_detection",
        "severity": "critical"
    }
    response = client.post("/api/v1/emergency/sos", json=payload)
    assert response.status_code == 201
    alert = response.json()
    assert alert["patient_id"] == patient_id
    assert alert["latitude"] == 12.9350
    assert alert["longitude"] == 77.5350
    assert alert["location_accuracy"] == 4.2


def test_assistance_request_not_okay(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "message": "Feeling severe chest tightness and dizziness",
        "severity": "high",
        "latitude": 12.9700,
        "longitude": 77.5900
    }
    response = client.post("/api/v1/emergency/assistance", json=payload, headers=headers)
    assert response.status_code == 201
    alert = response.json()
    assert alert["alert_type"] == "not_okay_assistance"
    assert alert["severity"] == "high"
    assert alert["assistance_message"] == "Feeling severe chest tightness and dizziness"


def test_multi_tier_caregiver_escalation_and_history(
    client,
    patient_token,
    test_patient_user,
    test_caregiver_user,
    db_session
):
    from app.core.security import get_password_hash
    patient_id = test_patient_user.patient_profile.id

    # Create Tier 1 Primary Caregiver
    assoc_t1 = PatientCaregiverAssociation(
        patient_id=patient_id,
        caregiver_id=test_caregiver_user.caregiver_profile.id,
        is_primary=True,
        escalation_tier=1
    )
    db_session.add(assoc_t1)

    # Create Tier 2 Secondary Caregiver
    user_t2 = User(
        email="secondary_cg@pulseguardian.ai",
        hashed_password=get_password_hash("pass123"),
        full_name="Nurse Priya",
        role="caregiver",
        phone_number="+919999111122",
        preferred_language="en",
        is_active=True
    )
    db_session.add(user_t2)
    db_session.flush()

    cg_t2 = CaregiverProfile(user_id=user_t2.id, relationship_type="Nurse")
    db_session.add(cg_t2)
    db_session.flush()

    assoc_t2 = PatientCaregiverAssociation(
        patient_id=patient_id,
        caregiver_id=cg_t2.id,
        is_primary=False,
        escalation_tier=2
    )
    db_session.add(assoc_t2)
    db_session.commit()

    # 1. Trigger SOS
    headers = {"Authorization": f"Bearer {patient_token}"}
    sos_resp = client.post("/api/v1/emergency/sos", json={"alert_type": "manual_sos"}, headers=headers)
    assert sos_resp.status_code == 201
    alert_id = sos_resp.json()["id"]

    # 2. Check escalation history - Celery eager mode processes the escalation chain
    history_resp = client.get(f"/api/v1/emergency/{alert_id}/escalation-history", headers=headers)
    assert history_resp.status_code == 200
    logs = history_resp.json()
    assert len(logs) >= 2
    assert logs[0]["tier"] == 1
    assert logs[1]["tier"] == 2
    assert logs[0]["provider"] == "development_mock"
    assert logs[0]["status"] == "dispatched_mock"


def test_caregiver_acknowledgment_halts_escalation(
    client,
    patient_token,
    caregiver_token,
    test_patient_user,
    test_caregiver_user,
    db_session
):
    patient_id = test_patient_user.patient_profile.id
    assoc = PatientCaregiverAssociation(
        patient_id=patient_id,
        caregiver_id=test_caregiver_user.caregiver_profile.id,
        is_primary=True,
        escalation_tier=1
    )
    db_session.add(assoc)
    db_session.commit()

    # 1. Trigger alert
    headers_pt = {"Authorization": f"Bearer {patient_token}"}
    sos_resp = client.post("/api/v1/emergency/sos", json={"alert_type": "manual_sos"}, headers=headers_pt)
    alert_id = sos_resp.json()["id"]

    # 2. Caregiver acknowledges
    headers_cg = {"Authorization": f"Bearer {caregiver_token}"}
    ack_payload = {"notes": "On my way to patient residence now."}
    ack_resp = client.post(f"/api/v1/emergency/{alert_id}/acknowledge", json=ack_payload, headers=headers_cg)
    assert ack_resp.status_code == 200
    ack_data = ack_resp.json()
    assert ack_data["status"] == "acknowledged"
    assert ack_data["acknowledged_by_id"] == test_caregiver_user.id
    assert ack_data["resolution_notes"] == "On my way to patient residence now."

    # 3. Subsequent escalation attempt must halt
    halt_result = escalation_service.execute_escalation_tier(db_session, alert_id=alert_id, target_tier=2)
    assert halt_result["status"] == "halted"


def test_caregiver_rejection_marks_false_alarm(
    client,
    patient_token,
    caregiver_token,
    test_patient_user,
    test_caregiver_user,
    db_session
):
    patient_id = test_patient_user.patient_profile.id
    assoc = PatientCaregiverAssociation(
        patient_id=patient_id,
        caregiver_id=test_caregiver_user.caregiver_profile.id,
        is_primary=True,
        escalation_tier=1
    )
    db_session.add(assoc)
    db_session.commit()

    headers_pt = {"Authorization": f"Bearer {patient_token}"}
    sos_resp = client.post("/api/v1/emergency/sos", json={"alert_type": "manual_sos"}, headers=headers_pt)
    alert_id = sos_resp.json()["id"]

    headers_cg = {"Authorization": f"Bearer {caregiver_token}"}
    reject_payload = {"reason": "Patient confirmed accidental button click"}
    reject_resp = client.post(f"/api/v1/emergency/{alert_id}/reject", json=reject_payload, headers=headers_cg)
    assert reject_resp.status_code == 200
    reject_data = reject_resp.json()
    assert reject_data["status"] == "rejected"
    assert reject_data["rejected_by_id"] == test_caregiver_user.id
    assert reject_data["rejection_reason"] == "Patient confirmed accidental button click"


def test_escalation_idempotency_duplicate_prevention(
    test_patient_user,
    test_caregiver_user,
    db_session
):
    from app.models.emergency import EmergencyAlert
    patient_id = test_patient_user.patient_profile.id
    assoc = PatientCaregiverAssociation(
        patient_id=patient_id,
        caregiver_id=test_caregiver_user.caregiver_profile.id,
        is_primary=True,
        escalation_tier=1
    )
    db_session.add(assoc)

    alert = EmergencyAlert(patient_id=patient_id, alert_type="manual_sos", status="triggered")
    db_session.add(alert)
    db_session.commit()

    # First dispatch
    res1 = escalation_service.execute_escalation_tier(db_session, alert_id=alert.id, target_tier=1)
    assert res1["status"] == "escalated"

    # Second dispatch for same tier must detect already dispatched
    res2 = escalation_service.execute_escalation_tier(db_session, alert_id=alert.id, target_tier=1)
    assert res2["status"] == "already_dispatched"


def test_notification_delivery_failure_and_retry(test_patient_user, test_caregiver_user, db_session):
    from app.models.emergency import EmergencyAlert

    patient_id = test_patient_user.patient_profile.id
    assoc = PatientCaregiverAssociation(
        patient_id=patient_id,
        caregiver_id=test_caregiver_user.caregiver_profile.id,
        is_primary=True,
        escalation_tier=1
    )
    db_session.add(assoc)

    alert = EmergencyAlert(patient_id=patient_id, alert_type="manual_sos", status="triggered")
    db_session.add(alert)
    db_session.commit()

    # Temporarily plug in failing adapter to verify retry tracking
    failing_adapter = MockDevelopmentNotificationAdapter(simulate_failure=True)
    orig_service = escalation_service.notification_service
    escalation_service.notification_service = NotificationService(adapter=failing_adapter)

    try:
        res = escalation_service.execute_escalation_tier(db_session, alert_id=alert.id, target_tier=1)
        assert res["status"] == "escalated"

        # Check audit log recorded failed status and retry attempts
        audit = alert.audit_logs[0]
        assert audit.status == "failed"
        assert audit.retry_count == 3
        assert "Simulated mock gateway network timeout" in audit.error_message
    finally:
        escalation_service.notification_service = orig_service


def test_unassigned_caregiver_cannot_acknowledge(
    client,
    caregiver_token,
    test_patient_user,
    db_session
):
    from app.models.emergency import EmergencyAlert
    patient_id = test_patient_user.patient_profile.id
    alert = EmergencyAlert(patient_id=patient_id, alert_type="manual_sos", status="triggered")
    db_session.add(alert)
    db_session.commit()

    headers = {"Authorization": f"Bearer {caregiver_token}"}
    response = client.post(f"/api/v1/emergency/{alert.id}/acknowledge", json={"notes": "test"}, headers=headers)
    assert response.status_code == 403
    assert "not an assigned caregiver" in response.json()["detail"]


def test_patient_cannot_view_unrelated_patient_emergency_alerts(
    client,
    patient_token,
    test_patient_user,
    db_session
):
    from app.core.security import get_password_hash
    from app.models.emergency import EmergencyAlert
    from app.models.user import PatientProfile, User

    # Create another patient's alert
    other_user = User(
        email="stranger@pulseguardian.ai",
        hashed_password=get_password_hash("pass123"),
        full_name="Stranger Patient",
        role="patient",
        preferred_language="en",
        is_active=True
    )
    db_session.add(other_user)
    db_session.flush()

    other_profile = PatientProfile(user_id=other_user.id)
    db_session.add(other_profile)
    db_session.flush()

    stranger_alert = EmergencyAlert(patient_id=other_profile.id, alert_type="manual_sos")
    db_session.add(stranger_alert)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get(f"/api/v1/emergency/{stranger_alert.id}", headers=headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]
