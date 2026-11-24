from datetime import datetime, timedelta, timezone
import pytest

from app.models.health import HealthTelemetry
from app.models.user import CaregiverProfile, PatientCaregiverAssociation, User, UserRole
from app.schemas.ai import MEDICAL_DISCLAIMER


def test_cold_start_digital_twin_baseline(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/digital-twin/baseline", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == test_patient_user.patient_profile.id
    assert data["cold_start"] is True
    assert data["status"] == "cold_start"
    assert data["samples_count"] == 0
    assert data["baseline_resting_hr"] == 72.0
    assert data["baseline_spo2"] == 98.0
    assert data["baseline_temperature"] == 36.8


def test_digital_twin_baseline_learning_with_historical_data(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    base_time = datetime.now(timezone.utc) - timedelta(hours=30)

    # Ingest 25 historical readings with a distinct resting HR around 68 bpm
    readings = []
    for i in range(25):
        readings.append(HealthTelemetry(
            patient_id=patient_id,
            heart_rate=68.0 + (i % 3),  # 68, 69, 70 bpm
            spo2=98.0,
            temperature=36.6,
            step_count=0,
            activity_type="resting",
            fall_detected=False,
            recorded_at=base_time + timedelta(hours=i)
        ))
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/digital-twin/baseline?recalculate=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["cold_start"] is False
    assert data["status"] == "active"
    assert data["samples_count"] >= 20
    assert 67.0 <= data["baseline_resting_hr"] <= 71.0
    assert data["hr_std_dev"] >= 3.0
    assert data["circadian_profile"] is not None
    assert data["circadian_profile"]["status"] == "active"


def test_get_full_digital_twin_model(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    base_time = datetime.now(timezone.utc) - timedelta(hours=26)

    readings = [
        HealthTelemetry(
            patient_id=patient_id,
            heart_rate=72.0,
            spo2=99.0,
            temperature=36.7,
            step_count=0,
            activity_type="resting",
            recorded_at=base_time + timedelta(hours=i)
        )
        for i in range(22)
    ]
    db_session.add_all(readings)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/digital-twin", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == patient_id
    assert "circadian_profile" in data
    assert "baseline_resting_hr" in data


def test_analyze_normal_vitals_no_anomaly(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "vitals": {
            "heart_rate": 72.0,
            "spo2": 98.0,
            "temperature": 36.6,
            "step_count": 0,
            "activity_type": "resting",
            "fall_detected": False
        }
    }
    response = client.post("/api/v1/ai/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()
    assert res["overall_status"] == "normal"
    assert res["severity"] == "normal"
    assert res["detected_anomalies"] == []
    assert res["medical_disclaimer"] == MEDICAL_DISCLAIMER
    assert len(res["recommendations"]) > 0


def test_analyze_acute_redlines_fall_and_bradycardia(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "vitals": {
            "heart_rate": 42.0,
            "spo2": 98.0,
            "temperature": 36.6,
            "step_count": 0,
            "activity_type": "resting",
            "fall_detected": True
        }
    }
    response = client.post("/api/v1/ai/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()
    assert res["overall_status"] == "anomalous"
    assert res["severity"] == "critical"

    params = [a["parameter"] for a in res["detected_anomalies"]]
    assert "fall_impact" in params
    assert "heart_rate" in params
    assert any("fall" in rec.lower() or "sos" in rec.lower() for rec in res["recommendations"])


def test_analyze_multi_signal_cardiorespiratory_stress(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "vitals": {
            "heart_rate": 115.0,
            "spo2": 91.0,
            "temperature": 36.8,
            "step_count": 0,
            "activity_type": "resting",
            "fall_detected": False
        }
    }
    response = client.post("/api/v1/ai/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()
    assert res["overall_status"] in ["anomalous", "cautionary"]
    assert res["severity"] in ["high", "critical"]
    params = [a["parameter"] for a in res["detected_anomalies"]]
    assert "multi_signal" in params


def test_analyze_distinguishes_exercise_from_resting_tachycardia(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    # Heart rate 125 bpm during active walking (step_count = 120)
    payload = {
        "vitals": {
            "heart_rate": 125.0,
            "spo2": 98.0,
            "temperature": 36.7,
            "step_count": 120,
            "activity_type": "active",
            "fall_detected": False
        }
    }
    response = client.post("/api/v1/ai/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()
    # Should not flag resting tachycardia
    reasons = [a["explanation"] for a in res["detected_anomalies"]]
    assert not any("resting tachycardia" in r.lower() for r in reasons)


def test_isolation_forest_with_sufficient_historical_data(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    base_time = datetime.now(timezone.utc) - timedelta(hours=40)

    # Ingest 35 tightly clustered normal readings
    records = [
        HealthTelemetry(
            patient_id=patient_id,
            heart_rate=70.0 + (i % 2),
            spo2=99.0,
            temperature=36.6,
            step_count=0,
            activity_type="resting",
            recorded_at=base_time + timedelta(minutes=i * 30)
        )
        for i in range(35)
    ]
    db_session.add_all(records)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    # Outlier vector in the multi-signal space
    payload = {
        "vitals": {
            "heart_rate": 95.0,
            "spo2": 93.0,
            "temperature": 37.6,
            "step_count": 0,
            "activity_type": "resting"
        }
    }
    response = client.post("/api/v1/ai/analyze", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()
    assert "isolation_forest_triggered" in res
    assert "isolation_forest_score" in res


def test_ai_health_status_endpoint(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    # Record latest telemetry
    telemetry = HealthTelemetry(
        patient_id=patient_id,
        heart_rate=74.0,
        spo2=98.0,
        temperature=36.7,
        step_count=50,
        activity_type="walking",
        is_anomalous=False,
        recorded_at=now
    )
    db_session.add(telemetry)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/health-status", headers=headers)
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["patient_id"] == patient_id
    assert status_data["current_status"] in ["normal", "cautionary"]
    assert status_data["latest_vitals"]["heart_rate"] == 74.0
    assert status_data["data_quality_status"] == "good"
    assert status_data["disclaimer"] == MEDICAL_DISCLAIMER


def test_ai_anomalies_history_with_severity_filter(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    # Add an anomalous record with high severity score
    anom = HealthTelemetry(
        patient_id=patient_id,
        heart_rate=142.0,
        spo2=88.0,
        temperature=38.9,
        activity_type="resting",
        fall_detected=False,
        is_anomalous=True,
        anomaly_score=0.90,
        anomaly_reason="Critical hypoxemia and resting tachycardia",
        recorded_at=now
    )
    db_session.add(anom)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/anomalies?severity=critical", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_anomalies"] >= 1
    assert data["anomalies"][0]["severity"] == "critical"
    assert data["anomalies"][0]["anomaly_score"] >= 0.85


def test_health_timeline_endpoint(client, patient_token, test_patient_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    now = datetime.now(timezone.utc)

    for i in range(5):
        t = HealthTelemetry(
            patient_id=patient_id,
            heart_rate=70.0 + i,
            spo2=98.0,
            temperature=36.6,
            step_count=10 * i,
            activity_type="resting",
            recorded_at=now - timedelta(hours=4 - i)
        )
        db_session.add(t)
    db_session.commit()

    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/ai/health-timeline?hours=24", headers=headers)
    assert response.status_code == 200
    timeline_data = response.json()
    assert timeline_data["patient_id"] == patient_id
    assert timeline_data["total_points"] == 5
    point = timeline_data["timeline"][0]
    assert "baseline_resting_hr" in point
    assert "hr_lower_bound" in point
    assert "hr_upper_bound" in point


def test_ai_rbac_patient_and_caregiver_permissions(client, patient_token, caregiver_token, test_patient_user, test_caregiver_user, db_session):
    patient_id = test_patient_user.patient_profile.id
    caregiver_id = test_caregiver_user.caregiver_profile.id

    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    caregiver_headers = {"Authorization": f"Bearer {caregiver_token}"}

    # 1. Patient trying to access a different patient ID (e.g. 999) -> 403 Forbidden
    resp = client.get("/api/v1/ai/digital-twin?patient_id=999", headers=patient_headers)
    assert resp.status_code == 403

    # 2. Caregiver accessing without association -> 403 Forbidden
    resp = client.get(f"/api/v1/ai/digital-twin?patient_id={patient_id}", headers=caregiver_headers)
    assert resp.status_code == 403

    # 3. Establish caregiver association
    assoc = PatientCaregiverAssociation(
        patient_id=patient_id,
        caregiver_id=caregiver_id,
        is_primary=True,
        access_level="full",
        escalation_tier=1
    )
    db_session.add(assoc)
    db_session.commit()

    # 4. Caregiver now has authorized access
    resp = client.get(f"/api/v1/ai/digital-twin?patient_id={patient_id}", headers=caregiver_headers)
    assert resp.status_code == 200
    assert resp.json()["patient_id"] == patient_id
