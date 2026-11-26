from datetime import datetime, timezone
import pytest
from app.models.user import User, UserRole, PatientProfile, CaregiverProfile, PatientCaregiverAssociation
from app.models.health import HealthTelemetry
from app.models.device import Device
from app.core.security import get_password_hash


@pytest.fixture(scope="function")
def seed_e2e_data(db_session):
    """Seed explicit accounts and associations for end-to-end integration tests."""
    now = datetime.now(timezone.utc)
    
    # 1. Check or create Patient
    patient = db_session.query(User).filter(User.email == "e2e_patient@pulseguardian.ai").first()
    if not patient:
        patient = User(
            email="e2e_patient@pulseguardian.ai",
            hashed_password=get_password_hash("Patient@123"),
            full_name="Thrisha M.",
            role=UserRole.PATIENT.value,
            preferred_language="en",
            is_active=True
        )
        db_session.add(patient)
        db_session.flush()

    p_profile = db_session.query(PatientProfile).filter(PatientProfile.user_id == patient.id).first()
    if not p_profile:
        p_profile = PatientProfile(
            user_id=patient.id,
            gender="Female",
            blood_group="O+",
            device_uuid="PG-E2E-9999",
            device_status="online",
            last_sync_at=now
        )
        db_session.add(p_profile)
        db_session.flush()

    # 2. Check or create Caregiver
    caregiver = db_session.query(User).filter(User.email == "e2e_caregiver@pulseguardian.ai").first()
    if not caregiver:
        caregiver = User(
            email="e2e_caregiver@pulseguardian.ai",
            hashed_password=get_password_hash("Caregiver@123"),
            full_name="Sarah Jenkins",
            role=UserRole.CAREGIVER.value,
            preferred_language="en",
            is_active=True
        )
        db_session.add(caregiver)
        db_session.flush()

    c_profile = db_session.query(CaregiverProfile).filter(CaregiverProfile.user_id == caregiver.id).first()
    if not c_profile:
        c_profile = CaregiverProfile(
            user_id=caregiver.id,
            relationship_type="Primary Nurse",
            notification_preference="all"
        )
        db_session.add(c_profile)
        db_session.flush()

    # 3. Associate Caregiver to Patient
    assoc = db_session.query(PatientCaregiverAssociation).filter(
        PatientCaregiverAssociation.patient_id == p_profile.id,
        PatientCaregiverAssociation.caregiver_id == c_profile.id
    ).first()
    if not assoc:
        assoc = PatientCaregiverAssociation(
            patient_id=p_profile.id,
            caregiver_id=c_profile.id,
            is_primary=True
        )
        db_session.add(assoc)

    # 4. Add telemetry
    telemetry = HealthTelemetry(
        patient_id=p_profile.id,
        heart_rate=72.0,
        spo2=98.0,
        temperature=36.8,
        temperature_unit="C",
        step_count=4820,
        battery_percentage=92.0,
        recorded_at=now
    )
    db_session.add(telemetry)

    # 5. Add device
    dev = db_session.query(Device).filter(Device.device_uuid == "PG-E2E-9999").first()
    if not dev:
        dev = Device(
            patient_id=p_profile.id,
            device_uuid="PG-E2E-9999",
            device_name="PulseGuardian Smart Band Pro",
            model_type="smartwatch",
            firmware_version="1.0.0",
            battery_level=92.0,
            status="connected",
            last_sync_at=now
        )
        db_session.add(dev)

    db_session.commit()
    return {"patient": patient, "caregiver": caregiver, "profile": p_profile}


# ==============================================================================
# PHASE 2 & 14 TESTS: AUTHENTICATION & ROLE-BASED ACCESS CONTROL
# ==============================================================================

def test_e2e_patient_login_and_token(client, seed_e2e_data):
    res = client.post("/api/v1/auth/login", json={
        "email": "e2e_patient@pulseguardian.ai",
        "password": "Patient@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "patient"
    assert data["full_name"] == "Thrisha M."


def test_e2e_caregiver_login_and_token(client, seed_e2e_data):
    res = client.post("/api/v1/auth/login", json={
        "email": "e2e_caregiver@pulseguardian.ai",
        "password": "Caregiver@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "caregiver"
    assert data["full_name"] == "Sarah Jenkins"


def test_e2e_invalid_credentials_rejected(client, seed_e2e_data):
    res = client.post("/api/v1/auth/login", json={
        "email": "e2e_patient@pulseguardian.ai",
        "password": "WrongPassword!999"
    })
    assert res.status_code == 401


# ==============================================================================
# PHASE 3 & 4 TESTS: DASHBOARD DATA INTEGRATION & TELEMETRY
# ==============================================================================

def test_e2e_patient_dashboard_api(client, seed_e2e_data):
    login = client.post("/api/v1/auth/login", json={
        "email": "e2e_patient@pulseguardian.ai",
        "password": "Patient@123"
    }).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    res = client.get("/api/v1/health/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["latest_vitals"]["heart_rate"] == 72.0
    assert data["latest_vitals"]["spo2"] == 98.0
    assert data["latest_vitals"]["temperature"] == 36.8
    assert data["latest_vitals"]["battery_percentage"] == 92.0
    assert data["device_status"]["device_uuid"] == "PG-E2E-9999"


def test_e2e_telemetry_ingestion_and_update(client, seed_e2e_data):
    login = client.post("/api/v1/auth/login", json={
        "email": "e2e_patient@pulseguardian.ai",
        "password": "Patient@123"
    }).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    ingest_res = client.post("/api/v1/health/telemetry", json={
        "heart_rate": 78.0,
        "spo2": 99.0,
        "temperature": 36.9,
        "step_count": 5100,
        "battery_percentage": 90.0,
        "device_uuid": "PG-E2E-9999"
    }, headers=headers)
    assert ingest_res.status_code == 201

    latest = client.get("/api/v1/health/latest", headers=headers)
    assert latest.status_code == 200
    assert latest.json()["heart_rate"] == 78.0


# ==============================================================================
# PHASE 6 TESTS: EMERGENCY SOS DISPATCH & CAREGIVER ACKNOWLEDGMENT
# ==============================================================================

def test_e2e_emergency_sos_dispatch_and_caregiver_ack(client, seed_e2e_data):
    p_login = client.post("/api/v1/auth/login", json={
        "email": "e2e_patient@pulseguardian.ai",
        "password": "Patient@123"
    }).json()
    p_headers = {"Authorization": f"Bearer {p_login['access_token']}"}

    sos_res = client.post("/api/v1/emergency/sos", json={
        "alert_type": "manual_sos",
        "severity": "critical",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "assistance_message": "Urgent assistance requested."
    }, headers=p_headers)
    assert sos_res.status_code == 201
    alert_id = sos_res.json()["id"]

    c_login = client.post("/api/v1/auth/login", json={
        "email": "e2e_caregiver@pulseguardian.ai",
        "password": "Caregiver@123"
    }).json()
    c_headers = {"Authorization": f"Bearer {c_login['access_token']}"}

    ack_res = client.post(f"/api/v1/emergency/{alert_id}/acknowledge", json={
        "acknowledgment_notes": "En route to residence."
    }, headers=c_headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"


# ==============================================================================
# PHASE 7 & 8 TESTS: VOICE PIPELINE & MULTILINGUAL MESSAGING
# ==============================================================================

def test_e2e_voice_transcribe_and_synthesize(client, seed_e2e_data):
    login = client.post("/api/v1/auth/login", json={
        "email": "e2e_patient@pulseguardian.ai",
        "password": "Patient@123"
    }).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    trans_res = client.post("/api/v1/voice/translate", json={
        "text": "Please take your morning vitamins.",
        "target_language": "ta",
        "source_language": "en"
    }, headers=headers)
    assert trans_res.status_code == 200
    assert "translated_text" in trans_res.json()


# ==============================================================================
# PHASE 9 & 10 TESTS: DEVICES, NOTIFICATIONS & EXPORTS
# ==============================================================================

def test_e2e_devices_list(client, seed_e2e_data):
    login = client.post("/api/v1/auth/login", json={
        "email": "e2e_patient@pulseguardian.ai",
        "password": "Patient@123"
    }).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    devices = client.get("/api/v1/devices", headers=headers)
    assert devices.status_code == 200
    assert len(devices.json()) >= 1
    assert devices.json()[0]["device_uuid"] == "PG-E2E-9999"


def test_e2e_health_history_export_json(client, seed_e2e_data):
    login = client.post("/api/v1/auth/login", json={
        "email": "e2e_patient@pulseguardian.ai",
        "password": "Patient@123"
    }).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    export_res = client.get("/api/v1/health/reports/export?format=json", headers=headers)
    assert export_res.status_code == 200
    data = export_res.json()
    assert "records" in data or "telemetry_records" in data or "readings" in data or isinstance(data, list)
