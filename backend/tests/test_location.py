from datetime import datetime, timedelta, timezone


def test_record_location_active_gps(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "altitude": 920.0,
        "accuracy": 3.8,
        "speed": 1.1,
        "is_gps_available": True,
        "device_battery": 87.0
    }
    response = client.post("/api/v1/location/track", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == test_patient_user.patient_profile.id
    assert data["latitude"] == 12.9716
    assert data["longitude"] == 77.5946
    assert data["accuracy"] == 3.8
    assert data["is_gps_available"] is True
    assert data["device_battery"] == 87.0


def test_record_location_gps_unavailable_does_not_invent_coordinates(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    # Device indoors or tunnel without GPS satellite lock
    payload = {
        "is_gps_available": False,
        "device_battery": 80.0
    }
    response = client.post("/api/v1/location/track", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["is_gps_available"] is False
    assert data["latitude"] is None
    assert data["longitude"] is None


def test_record_location_validation_error_when_available_but_missing_coords(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "is_gps_available": True,
        "latitude": None  # Invalid: claimed available but coordinate missing
    }
    response = client.post("/api/v1/location/track", json=payload, headers=headers)
    assert response.status_code == 422
    assert "Latitude and longitude must be provided" in response.json()["detail"]


def test_get_latest_location_active_fix(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    patient_id = test_patient_user.patient_profile.id

    client.post("/api/v1/location/track", json={
        "latitude": 12.9300,
        "longitude": 77.5300,
        "accuracy": 4.0,
        "is_gps_available": True
    }, headers=headers)

    response = client.get(f"/api/v1/location/latest/{patient_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["has_location"] is True
    assert data["is_stale"] is False
    assert data["status"] == "active"
    assert data["latest_location"]["latitude"] == 12.9300


def test_get_latest_location_stale_fix_handling(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    patient_id = test_patient_user.patient_profile.id

    stale_time = (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat()
    client.post("/api/v1/location/track", json={
        "latitude": 12.9400,
        "longitude": 77.5400,
        "is_gps_available": True,
        "recorded_at": stale_time
    }, headers=headers)

    response = client.get(f"/api/v1/location/latest/{patient_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["has_location"] is True
    assert data["is_stale"] is True
    assert data["status"] == "stale"
    assert "minute(s) old" in data["message"]


def test_get_latest_location_unavailable_fix(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    patient_id = test_patient_user.patient_profile.id

    # Post an unavailable fix as latest
    client.post("/api/v1/location/track", json={
        "is_gps_available": False,
        "device_battery": 65.0
    }, headers=headers)

    response = client.get(f"/api/v1/location/latest/{patient_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["has_location"] is False
    assert data["status"] == "unavailable"
    assert "unavailable or indoor" in data["message"]


def test_get_latest_location_no_records_exist(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    patient_id = test_patient_user.patient_profile.id

    response = client.get(f"/api/v1/location/latest/{patient_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["has_location"] is False
    assert data["status"] == "unavailable"
    assert "No GPS fixes" in data["message"]


def test_get_location_history_filters(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    patient_id = test_patient_user.patient_profile.id

    # Insert two valid and one unavailable
    client.post("/api/v1/location/track", json={"latitude": 12.9001, "longitude": 77.5001, "is_gps_available": True}, headers=headers)
    client.post("/api/v1/location/track", json={"latitude": 12.9002, "longitude": 77.5002, "is_gps_available": True}, headers=headers)
    client.post("/api/v1/location/track", json={"is_gps_available": False}, headers=headers)

    response = client.get(f"/api/v1/location/history/{patient_id}?valid_fixes_only=true", headers=headers)
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert all(p["latitude"] is not None for p in history)


def test_location_caregiver_access_permitted(
    client,
    caregiver_token,
    test_patient_user,
    test_caregiver_user,
    db_session
):
    from app.models.user import PatientCaregiverAssociation
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

    client.post("/api/v1/location/track", json={
        "device_uuid": "PG-ESP32-001",
        "latitude": 12.9500,
        "longitude": 77.5500,
        "is_gps_available": True
    })

    response = client.get(f"/api/v1/location/latest/{patient_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["has_location"] is True


def test_location_unauthorized_caregiver_access_forbidden(client, caregiver_token, test_patient_user):
    headers = {"Authorization": f"Bearer {caregiver_token}"}
    patient_id = test_patient_user.patient_profile.id
    response = client.get(f"/api/v1/location/latest/{patient_id}", headers=headers)
    assert response.status_code == 403
    assert "not assigned" in response.json()["detail"]
