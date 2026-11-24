from datetime import datetime, timedelta, timezone


def test_ingest_telemetry_complete_wearable_vitals(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "heart_rate": 74.0,
        "spo2": 98.5,
        "temperature": 36.6,
        "temperature_unit": "C",
        "step_count": 3400,
        "activity_type": "walking",
        "sleep_duration_minutes": 420,
        "fall_detected": False,
        "accelerometer_x": 0.02,
        "accelerometer_y": 0.98,
        "accelerometer_z": 0.15,
        "battery_percentage": 82.0
    }
    response = client.post("/api/v1/health/telemetry", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == test_patient_user.patient_profile.id
    assert data["heart_rate"] == 74.0
    assert data["spo2"] == 98.5
    assert data["temperature"] == 36.6
    assert data["temperature_unit"] == "C"
    assert data["step_count"] == 3400
    assert data["activity_type"] == "walking"
    assert data["sleep_duration_minutes"] == 420
    assert data["accelerometer_x"] == 0.02
    assert data["accelerometer_y"] == 0.98
    assert data["accelerometer_z"] == 0.15
    assert data["battery_percentage"] == 82.0
    assert data["is_anomalous"] is False


def test_ingest_telemetry_offline_sync_duplicate_prevention(client, test_patient_user):
    # Same reading submitted twice with identical timestamp (e.g. re-sync from wearable flash storage)
    fixed_time = datetime(2026, 11, 23, 10, 30, 0, tzinfo=timezone.utc).isoformat()
    payload = {
        "device_uuid": "PG-ESP32-001",
        "heart_rate": 72.0,
        "spo2": 98.0,
        "recorded_at": fixed_time
    }
    # First submission
    resp1 = client.post("/api/v1/health/telemetry", json=payload)
    assert resp1.status_code == 201
    reading_id = resp1.json()["id"]

    # Second submission with same timestamp must not create duplicate
    resp2 = client.post("/api/v1/health/telemetry", json=payload)
    assert resp2.status_code == 201
    assert resp2.json()["id"] == reading_id


def test_batch_ingestion_with_duplicate_skipping(client, test_patient_user):
    now = datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc)
    t1 = (now - timedelta(minutes=15)).isoformat()
    t2 = (now - timedelta(minutes=10)).isoformat()

    # Pre-insert t1
    client.post("/api/v1/health/telemetry", json={
        "device_uuid": "PG-ESP32-001",
        "heart_rate": 69.0,
        "recorded_at": t1
    })

    # Send batch containing t1 (duplicate) and t2 (new)
    batch_payload = {
        "device_uuid": "PG-ESP32-001",
        "readings": [
            {"heart_rate": 69.0, "recorded_at": t1},
            {"heart_rate": 73.0, "recorded_at": t2}
        ]
    }
    response = client.post("/api/v1/health/telemetry/batch", json=batch_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["total_received"] == 2
    assert data["inserted"] == 1
    assert data["duplicates_skipped"] == 1
    assert len(data["readings"]) == 1
    assert data["readings"][0]["heart_rate"] == 73.0


def test_get_health_latest_endpoint(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    client.post("/api/v1/health/telemetry", json={"heart_rate": 70.0, "spo2": 97.0}, headers=headers)
    client.post("/api/v1/health/telemetry", json={"heart_rate": 85.0, "spo2": 99.0}, headers=headers)

    # Calling /health/latest directly without param (infers authenticated patient)
    response = client.get("/api/v1/health/latest", headers=headers)
    assert response.status_code == 200
    assert response.json()["heart_rate"] == 85.0


def test_get_health_history_endpoint(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    client.post("/api/v1/health/telemetry", json={"heart_rate": 65.0, "spo2": 98.0}, headers=headers)
    client.post("/api/v1/health/telemetry", json={"heart_rate": 140.0, "spo2": 95.0, "activity_type": "resting"}, headers=headers)

    # 1. Query full history
    resp_all = client.get("/api/v1/health/history", headers=headers)
    assert resp_all.status_code == 200
    assert len(resp_all.json()) >= 2

    # 2. Query anomalies only
    resp_anom = client.get("/api/v1/health/history?anomalies_only=true", headers=headers)
    assert resp_anom.status_code == 200
    anomalies = resp_anom.json()
    assert len(anomalies) >= 1
    assert all(a["is_anomalous"] is True for a in anomalies)


def test_get_health_trends_endpoint(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    patient_id = test_patient_user.patient_profile.id

    client.post("/api/v1/health/telemetry", json={"heart_rate": 70.0, "spo2": 97.0, "step_count": 500, "sleep_duration_minutes": 60}, headers=headers)
    client.post("/api/v1/health/telemetry", json={"heart_rate": 75.0, "spo2": 98.0, "step_count": 800}, headers=headers)
    client.post("/api/v1/health/telemetry", json={"heart_rate": 80.0, "spo2": 99.0, "step_count": 1200}, headers=headers)

    response = client.get(f"/api/v1/health/trends?hours=24", headers=headers)
    assert response.status_code == 200
    trends = response.json()
    assert trends["total_readings"] >= 3
    assert trends["min_heart_rate"] == 70.0
    assert trends["max_heart_rate"] == 80.0
    assert trends["total_steps"] == 2500
    assert trends["total_sleep_minutes"] == 60
    assert "hourly_averages" in trends


def test_get_device_status_endpoint(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    client.post("/api/v1/health/telemetry", json={
        "heart_rate": 72.0,
        "battery_percentage": 94.0,
        "device_uuid": "PG-ESP32-001"
    }, headers=headers)

    response = client.get("/api/v1/health/device-status", headers=headers)
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["patient_id"] == test_patient_user.patient_profile.id
    assert status_data["device_status"] == "online"
    assert status_data["is_online"] is True
    assert status_data["is_stale"] is False
    assert status_data["battery_percentage"] == 94.0
    assert "max30102_heart_rate_spo2" in status_data["sensor_status"]


def test_caregiver_access_permitted_for_associated_patient(
    client,
    caregiver_token,
    test_patient_user,
    test_caregiver_user,
    db_session
):
    from app.models.user import PatientCaregiverAssociation
    # Link patient and caregiver
    assoc = PatientCaregiverAssociation(
        patient_id=test_patient_user.patient_profile.id,
        caregiver_id=test_caregiver_user.caregiver_profile.id,
        is_primary=True,
        escalation_tier=1
    )
    db_session.add(assoc)
    db_session.commit()

    headers = {"Authorization": f"Bearer {caregiver_token}"}
    patient_id = test_patient_user.patient_profile.id

    # Caregiver querying associated patient's latest vitals
    response = client.get(f"/api/v1/health/latest?patient_id={patient_id}", headers=headers)
    assert response.status_code == 200


def test_unassigned_caregiver_access_forbidden(client, caregiver_token, test_patient_user):
    headers = {"Authorization": f"Bearer {caregiver_token}"}
    patient_id = test_patient_user.patient_profile.id
    response = client.get(f"/api/v1/health/latest?patient_id={patient_id}", headers=headers)
    assert response.status_code == 403
    assert "not assigned" in response.json()["detail"]
