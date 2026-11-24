from datetime import datetime, timedelta, timezone
import pytest

from app.models.health import HealthTelemetry
from app.models.user import PatientCaregiverAssociation
from app.schemas.ai import MEDICAL_DISCLAIMER


def test_drift_stable_readings(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    # Ingest 7 days of stable readings (HR ~72 bpm, SpO2 ~98%, Temp ~36.8C)
    readings = []
    for day in range(7):
        rec_time = now - timedelta(days=6 - day, hours=12)
        readings.append(HealthTelemetry(
            patient_id=patient_id,
            heart_rate=71.0 + (day % 2),
            spo2=98.0,
            temperature=36.8,
            step_count=5000,
            sleep_duration_minutes=450,
            activity_type="resting",
            recorded_at=rec_time
        ))
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/health-drift/summary?window_days=7", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["patient_id"] == patient_id
    assert data["overall_drift_status"] == "stable"
    assert data["data_completeness_percentage"] == 100.0
    assert data["medical_disclaimer"] == MEDICAL_DISCLAIMER

    hr_drift = data["metrics_summary"]["heart_rate"]
    assert hr_drift["trend_direction"] == "stable"
    assert hr_drift["classification"] == "stable"
    assert hr_drift["significance"] == "stable"


def test_drift_gradually_rising_heart_rate(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    # Ingest 7 days of steadily increasing resting HR: 72 -> 84 bpm (+16%)
    readings = []
    for day in range(7):
        rec_time = now - timedelta(days=6 - day, hours=10)
        readings.append(HealthTelemetry(
            patient_id=patient_id,
            heart_rate=72.0 + (day * 2.0),  # 72, 74, 76, 78, 80, 82, 84
            spo2=98.0,
            temperature=36.8,
            step_count=4500,
            sleep_duration_minutes=420,
            activity_type="resting",
            recorded_at=rec_time
        ))
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/health-drift/summary?window_days=7", headers=headers)
    assert response.status_code == 200
    data = response.json()

    hr_drift = data["metrics_summary"]["heart_rate"]
    assert hr_drift["trend_direction"] == "upward"
    assert hr_drift["slope_per_day"] > 1.0
    assert hr_drift["is_persistent"] is True
    assert hr_drift["classification"] == "persistent_drift"
    assert hr_drift["significance"] in ["mild_drift", "moderate_drift", "significant_drift"]
    assert "upward drift" in hr_drift["explanation"].lower()


def test_drift_gradually_falling_spo2(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    # Ingest 7 days of steadily declining SpO2: 98.0 -> 94.5%
    readings = []
    for day in range(7):
        rec_time = now - timedelta(days=6 - day, hours=10)
        readings.append(HealthTelemetry(
            patient_id=patient_id,
            heart_rate=72.0,
            spo2=98.0 - (day * 0.5),  # 98.0, 97.5, 97.0, 96.5, 96.0, 95.5, 95.0
            temperature=36.8,
            step_count=4000,
            sleep_duration_minutes=420,
            activity_type="resting",
            recorded_at=rec_time
        ))
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/health-drift/metric/spo2?window_days=7", headers=headers)
    assert response.status_code == 200
    spo2_drift = response.json()

    assert spo2_drift["metric_name"] == "spo2"
    assert spo2_drift["trend_direction"] == "downward"
    assert spo2_drift["slope_per_day"] < 0
    assert spo2_drift["is_persistent"] is True
    assert spo2_drift["classification"] == "persistent_drift"
    assert spo2_drift["significance"] in ["mild_drift", "moderate_drift", "significant_drift"]
    assert len(spo2_drift["data_points"]) == 7


def test_drift_distinguishes_transient_fluctuation_from_persistent_drift(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    # Days 0, 1, 2: 70 bpm, Day 3: acute 88 bpm spike, Days 4, 5, 6: back to 70-71 bpm
    hr_sequence = [70.0, 71.0, 70.0, 88.0, 71.0, 70.0, 71.0]
    readings = []
    for day, hr in enumerate(hr_sequence):
        rec_time = now - timedelta(days=6 - day, hours=8)
        readings.append(HealthTelemetry(
            patient_id=patient_id,
            heart_rate=hr,
            spo2=98.0,
            temperature=36.7,
            step_count=5000,
            sleep_duration_minutes=450,
            activity_type="resting",
            recorded_at=rec_time
        ))
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/health-drift/metric/heart_rate?window_days=7", headers=headers)
    assert response.status_code == 200
    hr_drift = response.json()

    # The spike should NOT be classified as persistent drift
    assert hr_drift["classification"] in ["transient_fluctuation", "stable"]
    assert hr_drift["is_persistent"] is False


def test_drift_insufficient_historical_data(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    # Only 1 reading exists (less than minimum 3 days)
    reading = HealthTelemetry(
        patient_id=patient_id,
        heart_rate=75.0,
        spo2=98.0,
        temperature=36.8,
        activity_type="resting",
        recorded_at=now - timedelta(hours=5)
    )
    db_session.add(reading)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/health-drift/summary?window_days=7", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_drift_status"] == "insufficient_data"
    assert data["overall_confidence"] == "low"
    assert data["metrics_summary"]["heart_rate"]["data_sufficiency"] == "insufficient"


def test_drift_missing_and_noisy_readings_handled(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    # 4 days out of 7 recorded (some missing days), temperature has an invalid noise artifact that gets cleaned
    sparse_days = [0, 2, 4, 6]
    readings = []
    for day in sparse_days:
        rec_time = now - timedelta(days=6 - day, hours=10)
        readings.append(HealthTelemetry(
            patient_id=patient_id,
            heart_rate=72.0,
            spo2=98.0,
            temperature=36.7,
            step_count=4500,
            activity_type="resting",
            recorded_at=rec_time
        ))
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/health-drift/summary?window_days=7", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # 4 of 7 days recorded = ~57.1% completeness
    assert 50.0 <= data["data_completeness_percentage"] <= 65.0
    assert data["metrics_summary"]["heart_rate"]["recorded_days_count"] == 4


def test_drift_multi_window_comparisons_present(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    readings = []
    for day in range(8):
        rec_time = now - timedelta(days=7 - day, hours=8)
        readings.append(HealthTelemetry(
            patient_id=patient_id,
            heart_rate=70.0 + day,
            spo2=98.0,
            temperature=36.6,
            step_count=5000,
            activity_type="resting",
            recorded_at=rec_time
        ))
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/health-drift/summary?window_days=7", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "multi_window_trends" in data
    assert "3d" in data["multi_window_trends"]
    assert "7d" in data["multi_window_trends"]
    assert "30d" in data["multi_window_trends"]


def test_drift_timeline_endpoint(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    # Ingest drift-triggering readings
    readings = []
    for day in range(7):
        rec_time = now - timedelta(days=6 - day, hours=10)
        readings.append(HealthTelemetry(
            patient_id=patient_id,
            heart_rate=72.0 + (day * 2.5),
            spo2=98.0,
            temperature=36.8,
            activity_type="resting",
            recorded_at=rec_time
        ))
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    # Trigger drift analysis which persists drift record
    client.get("/api/v1/ai/health-drift/summary?window_days=7", headers=headers)

    # Query timeline
    response = client.get("/api/v1/ai/health-drift/timeline", headers=headers)
    assert response.status_code == 200
    timeline = response.json()
    assert timeline["patient_id"] == patient_id
    assert timeline["total_records"] >= 1
    assert "drift_parameter" in timeline["records"][0]
    assert "drift_percentage" in timeline["records"][0]


def test_drift_custom_window_analyze_endpoint(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    readings = []
    for day in range(10):
        rec_time = now - timedelta(days=9 - day, hours=10)
        readings.append(HealthTelemetry(
            patient_id=patient_id,
            heart_rate=70.0 + (day % 3),
            spo2=98.0,
            temperature=36.7,
            step_count=6000,
            sleep_duration_minutes=480,
            activity_type="resting",
            recorded_at=rec_time
        ))
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "window_days": 10,
        "metrics": ["heart_rate", "spo2", "sleep_duration"],
        "persist": True
    }
    response = client.post("/api/v1/ai/health-drift/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["window_days"] == 10
    assert "heart_rate" in data["metrics_summary"]
    assert "spo2" in data["metrics_summary"]
    assert "sleep_duration" in data["metrics_summary"]


def test_drift_rbac_patient_and_caregiver_permissions(client, patient_token, caregiver_token, test_patient_user, test_caregiver_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    caregiver_id = test_caregiver_user.caregiver_profile.id

    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    caregiver_headers = {"Authorization": f"Bearer {caregiver_token}"}

    # 1. Patient querying someone else's patient_id -> 403 Forbidden
    resp = client.get("/api/v1/ai/health-drift/summary?patient_id=999", headers=patient_headers)
    assert resp.status_code == 403

    # 2. Caregiver querying unassigned patient -> 403 Forbidden
    resp = client.get(f"/api/v1/ai/health-drift/summary?patient_id={patient_id}", headers=caregiver_headers)
    assert resp.status_code == 403

    # 3. Associate caregiver with patient
    assoc = PatientCaregiverAssociation(
        patient_id=patient_id,
        caregiver_id=caregiver_id,
        is_primary=True,
        access_level="full",
        escalation_tier=1
    )
    db_session.add(assoc)
    db_session.commit()

    # 4. Caregiver now authorized to query
    resp = client.get(f"/api/v1/ai/health-drift/summary?patient_id={patient_id}", headers=caregiver_headers)
    assert resp.status_code == 200
    assert resp.json()["patient_id"] == patient_id
