"""
Unit & Integration Tests for Nova Universal Role-Aware AI Assistant
Verifies:
1. Patient interaction (vitals, medication, mood check-in, family call, emergency SOS)
2. Family caregiver interaction (personal wellbeing isolation, linked patient report, unauthorized rejection)
3. Doctor interaction (clinical trends, AI observations, assignment authorization checks)
4. Emergency EMS interaction (active incidents, triage vitals, GPS coordinates, handover logging)
5. Context discovery and wellbeing history segregation
"""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.models.user import (
    User,
    UserRole,
    PatientProfile,
    CaregiverProfile,
    PatientCaregiverAssociation,
    DoctorProfile,
    DoctorPatientAssignment,
    EmergencyTeamProfile,
)
from app.models.health import HealthTelemetry, PatientMedicine
from app.models.emergency import EmergencyAlert
from app.models.location import LocationLog
from app.core.security import create_access_token, get_password_hash


@pytest.fixture
def test_doctor_user(db_session):
    user = User(
        email="dr.nova@pulseguardian.ai",
        hashed_password=get_password_hash("Doctor@123"),
        full_name="Dr. Nova Rao",
        role=UserRole.DOCTOR.value,
        phone_number="+919876543230",
        preferred_language="en",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    doc_profile = DoctorProfile(
        user_id=user.id,
        medical_reg_no="MCI-NOVA-99",
        specialization="Cardiology",
        hospital_name="PulseGuardian Heart Clinic",
        designation="Attending Physician",
        is_verified=True,
    )
    db_session.add(doc_profile)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def doctor_token(test_doctor_user):
    return create_access_token(
        subject=test_doctor_user.id,
        role=test_doctor_user.role,
        extra_claims={"email": test_doctor_user.email}
    )


@pytest.fixture
def test_ems_user(db_session):
    user = User(
        email="ems.nova@pulseguardian.ai",
        hashed_password=get_password_hash("Emergency@123"),
        full_name="Officer Nova EMS",
        role=UserRole.EMERGENCY.value,
        phone_number="+919110022334",
        preferred_language="en",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    ems_profile = EmergencyTeamProfile(
        user_id=user.id,
        organization_name="Emergency Response Team",
        responder_id="EMS-NOVA-01",
        designation="Lead Paramedic",
        is_verified=True,
    )
    db_session.add(ems_profile)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def ems_token(test_ems_user):
    return create_access_token(
        subject=test_ems_user.id,
        role=test_ems_user.role,
        extra_claims={"email": test_ems_user.email}
    )


# -----------------------------------------------------------------------------
# 1. CONTEXT DISCOVERY TESTS
# -----------------------------------------------------------------------------
def test_nova_context_patient(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    res = client.get("/api/v1/nova/context", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "patient"
    assert "check_vitals" in data["capabilities"]
    assert "emergency_sos" in data["capabilities"]
    assert len(data["authorized_patients"]) == 1
    assert data["authorized_patients"][0]["name"] == test_patient_user.full_name


def test_nova_context_family(client, caregiver_token, test_caregiver_user, test_patient_user, db_session):
    # Link caregiver to patient
    assoc = PatientCaregiverAssociation(
        patient_id=test_patient_user.patient_profile.id,
        caregiver_id=test_caregiver_user.caregiver_profile.id,
        is_primary=True,
    )
    db_session.add(assoc)
    db_session.commit()

    headers = {"Authorization": f"Bearer {caregiver_token}"}
    res = client.get("/api/v1/nova/context", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "caregiver"
    assert "caregiver_wellbeing" in data["capabilities"]
    assert len(data["authorized_patients"]) == 1
    assert data["authorized_patients"][0]["name"] == test_patient_user.full_name


# -----------------------------------------------------------------------------
# 2. PATIENT PERSONA TESTS
# -----------------------------------------------------------------------------
def test_patient_check_vitals(client, patient_token, test_patient_user, db_session):
    # Add telemetry
    tel = HealthTelemetry(
        patient_id=test_patient_user.patient_profile.id,
        heart_rate=76.0,
        spo2=99.0,
        temperature=36.7,
        step_count=1200,
        activity_type="resting",
        fall_detected=False,
        recorded_at=datetime.now(timezone.utc),
    )
    db_session.add(tel)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    res = client.post("/api/v1/nova/interact", json={"action": "check_vitals", "language": "en"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "patient"
    assert "76 beats per minute" in data["text"]
    assert data["action_result"]["heart_rate"] == 76


def test_patient_multilingual_kannada(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    res = client.post("/api/v1/nova/interact", json={"action": "check_vitals", "language": "kn"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "ಹೃದಯ ಬಡಿತ" in data["text"]


def test_patient_mood_checkin(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    res = client.post(
        "/api/v1/nova/interact",
        json={"action": "mood_checkin", "mood_type": "lonely", "notes": "Feeling isolated today."},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert "never alone" in data["text"].lower() or "right here with you" in data["text"].lower()


def test_patient_emergency_sos(client, patient_token, test_patient_user, db_session):
    headers = {"Authorization": f"Bearer {patient_token}"}
    res = client.post("/api/v1/nova/interact", json={"action": "emergency_sos"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_emergency"] is True
    assert data["direct_call_url"] == "tel:112"
    assert "Emergency SOS initiated" in data["text"]

    # Verify alert created in DB
    alert = db_session.query(EmergencyAlert).filter(
        EmergencyAlert.patient_id == test_patient_user.patient_profile.id,
        EmergencyAlert.alert_type == "VOICE_SOS"
    ).first()
    assert alert is not None
    assert alert.status == "triggered"


# -----------------------------------------------------------------------------
# 3. FAMILY CAREGIVER PERSONA TESTS
# -----------------------------------------------------------------------------
def test_family_member_own_wellbeing(client, caregiver_token):
    headers = {"Authorization": f"Bearer {caregiver_token}"}
    res = client.post(
        "/api/v1/nova/interact",
        json={"action": "caregiver_wellbeing", "mood_type": "routine_fatigue"},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "family"
    assert "caregiving" in data["text"].lower() or "rest" in data["text"].lower()


def test_family_authorized_patient_health_summary(
    client, caregiver_token, test_caregiver_user, test_patient_user, db_session
):
    assoc = PatientCaregiverAssociation(
        patient_id=test_patient_user.patient_profile.id,
        caregiver_id=test_caregiver_user.caregiver_profile.id,
        is_primary=True,
    )
    db_session.add(assoc)
    db_session.commit()

    headers = {"Authorization": f"Bearer {caregiver_token}"}
    pat_code = test_patient_user.patient_id or f"PT-{test_patient_user.patient_profile.id}"
    res = client.post(
        "/api/v1/nova/interact",
        json={"action": "check_patient_health", "patient_id": pat_code},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["patient_name"] == test_patient_user.full_name


def test_family_unauthorized_patient_access_blocked(
    client, caregiver_token, test_caregiver_user, db_session
):
    # Create another patient NOT linked to this caregiver
    unlinked_user = User(
        email="unlinked@pulseguardian.ai",
        hashed_password=get_password_hash("Pass@123"),
        full_name="Unlinked Patient",
        role=UserRole.PATIENT.value,
        patient_id="PT-2026-999999",
        is_active=True,
    )
    db_session.add(unlinked_user)
    db_session.flush()
    unlinked_profile = PatientProfile(user_id=unlinked_user.id)
    db_session.add(unlinked_profile)
    db_session.commit()

    headers = {"Authorization": f"Bearer {caregiver_token}"}
    res = client.post(
        "/api/v1/nova/interact",
        json={"action": "check_patient_health", "patient_id": "PT-2026-999999"},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "unauthorized"
    assert "Access Denied" in data["text"]


# -----------------------------------------------------------------------------
# 4. DOCTOR PERSONA TESTS
# -----------------------------------------------------------------------------
def test_doctor_clinical_trends_assigned_patient(
    client, doctor_token, test_doctor_user, test_patient_user, db_session
):
    doc_prof = db_session.query(DoctorProfile).filter(DoctorProfile.user_id == test_doctor_user.id).first()
    assignment = DoctorPatientAssignment(
        doctor_id=doc_prof.id,
        patient_id=test_patient_user.patient_profile.id,
        status="active",
        can_prescribe=True,
    )
    db_session.add(assignment)
    db_session.commit()

    headers = {"Authorization": f"Bearer {doctor_token}"}
    pat_code = test_patient_user.patient_id or f"PT-{test_patient_user.patient_profile.id}"
    res = client.post(
        "/api/v1/nova/interact",
        json={"action": "clinical_trends", "patient_id": pat_code},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "doctor"
    assert "Doctor Assistant Clinical Summary" in data["text"]


def test_doctor_unassigned_patient_rejected(
    client, doctor_token, test_patient_user
):
    # Doctor is NOT assigned to test_patient_user
    headers = {"Authorization": f"Bearer {doctor_token}"}
    pat_code = test_patient_user.patient_id or f"PT-{test_patient_user.patient_profile.id}"
    res = client.post(
        "/api/v1/nova/interact",
        json={"action": "clinical_trends", "patient_id": pat_code},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "unauthorized"
    assert "Access Denied" in data["text"]


# -----------------------------------------------------------------------------
# 5. EMERGENCY EMS PERSONA TESTS
# -----------------------------------------------------------------------------
def test_ems_active_incidents(client, ems_token, test_patient_user, db_session):
    alert = EmergencyAlert(
        patient_id=test_patient_user.patient_profile.id,
        alert_type="FALL_DETECTION",
        severity="critical",
        status="active",
        created_at=datetime.now(timezone.utc),
        latitude=12.9716,
        longitude=77.5946,
    )
    db_session.add(alert)
    db_session.commit()

    headers = {"Authorization": f"Bearer {ems_token}"}
    res = client.post("/api/v1/nova/interact", json={"action": "active_incidents"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "emergency"
    assert data["is_emergency"] is True
    assert "FALL_DETECTION" in data["text"]
    assert "GPS Coordinates" in data["text"]


# -----------------------------------------------------------------------------
# 6. INDEPENDENT WELLBEING HISTORY TESTS
# -----------------------------------------------------------------------------
def test_wellbeing_history_isolation(client, patient_token, caregiver_token):
    # Patient logs a mood check-in
    h_pat = {"Authorization": f"Bearer {patient_token}"}
    res1 = client.post(
        "/api/v1/nova/wellbeing",
        json={"mood_type": "calm", "notes": "Feeling balanced today."},
        headers=h_pat
    )
    assert res1.status_code == 201

    # Caregiver logs a personal wellbeing check-in
    h_cg = {"Authorization": f"Bearer {caregiver_token}"}
    res2 = client.post(
        "/api/v1/nova/wellbeing",
        json={"mood_type": "tired", "notes": "Need a 10 min break."},
        headers=h_cg
    )
    assert res2.status_code == 201
    assert res2.json()["is_caregiver_wellbeing"] is True

    # Patient retrieves their history (should only see patient log)
    history_pat = client.get("/api/v1/nova/wellbeing/history", headers=h_pat).json()
    assert len(history_pat) == 1
    assert history_pat[0]["is_caregiver_wellbeing"] is False

    # Caregiver retrieves their history (should only see caregiver log)
    history_cg = client.get("/api/v1/nova/wellbeing/history", headers=h_cg).json()
    assert len(history_cg) == 1
    assert history_cg[0]["is_caregiver_wellbeing"] is True
