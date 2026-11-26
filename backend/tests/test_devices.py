def test_pair_and_get_device(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    pair_payload = {
        "device_uuid": "ESP32_PULSE_9999",
        "device_name": "Ramesh's Smart Band",
        "model_type": "ESP32-MAX30102-MPU6050",
        "firmware_version": "1.0.1",
        "is_simulator": False
    }
    response = client.post("/api/v1/devices/pair", json=pair_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["device_uuid"] == "ESP32_PULSE_9999"
    assert data["status"] == "connected"
    device_id = data["id"]

    # Get device by ID
    get_res = client.get(f"/api/v1/devices/{device_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["device_name"] == "Ramesh's Smart Band"

    # List devices
    list_res = client.get("/api/v1/devices", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_update_device_config_and_sync(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    pair_payload = {
        "device_uuid": "ESP32_PULSE_8888",
        "device_name": "Test Band 2",
        "model_type": "ESP32",
        "firmware_version": "1.0.0"
    }
    res = client.post("/api/v1/devices/pair", json=pair_payload, headers=headers)
    assert res.status_code == 201
    device_id = res.json()["id"]

    # Update config
    cfg_payload = {
        "sampling_interval_seconds": 10,
        "hr_alert_threshold_high": 130.0,
        "hr_alert_threshold_low": 45.0,
        "fall_detection_enabled": True
    }
    cfg_res = client.put(f"/api/v1/devices/{device_id}/config", json=cfg_payload, headers=headers)
    assert cfg_res.status_code == 200
    assert "sampling_interval_seconds" in cfg_res.json()["config_json"]

    # Manual sync
    sync_res = client.post(f"/api/v1/devices/{device_id}/sync", headers=headers)
    assert sync_res.status_code == 200
    assert sync_res.json()["status"] == "connected"

    # Check history
    hist_res = client.get(f"/api/v1/devices/{device_id}/history", headers=headers)
    assert hist_res.status_code == 200
    events = [h["event_type"] for h in hist_res.json()]
    assert "paired" in events
    assert "sync" in events


def test_disconnect_and_simulate_reading(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    pair_payload = {
        "device_uuid": "ESP32_SIMULATOR_001",
        "device_name": "Simulated ESP32",
        "model_type": "ESP32-SIM",
        "firmware_version": "1.0.0",
        "is_simulator": True
    }
    res = client.post("/api/v1/devices/pair", json=pair_payload, headers=headers)
    device_id = res.json()["id"]

    # Disconnect
    disc_res = client.post(f"/api/v1/devices/{device_id}/disconnect", headers=headers)
    assert disc_res.status_code == 200
    assert disc_res.json()["status"] == "disconnected"

    # Simulate reading
    sim_payload = {
        "heart_rate": 84.0,
        "spo2": 97.5,
        "temperature": 36.7,
        "step_count": 310,
        "fall_detected": False,
        "battery_level": 88.0
    }
    sim_res = client.post(f"/api/v1/devices/{device_id}/simulate", json=sim_payload, headers=headers)
    assert sim_res.status_code == 201
    sim_data = sim_res.json()
    assert sim_data["is_simulated"] is True
    assert sim_data["status"] == "simulated_reading_recorded"
