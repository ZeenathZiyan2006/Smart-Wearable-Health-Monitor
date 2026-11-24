def test_list_patients_as_caregiver(client, caregiver_token, test_patient_user):
    headers = {"Authorization": f"Bearer {caregiver_token}"}
    response = client.get("/api/v1/users/patients", headers=headers)
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) >= 1
    assert any(p["user_id"] == test_patient_user.id for p in patients)


def test_list_patients_as_patient_forbidden(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/users/patients", headers=headers)
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]


def test_get_patient_self_success(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    patient_id = test_patient_user.patient_profile.id
    response = client.get(f"/api/v1/users/patients/{patient_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == patient_id
    assert data["blood_group"] == "O+"
    assert data["device_uuid"] == "PG-ESP32-001"


def test_get_patient_other_forbidden(client, test_patient_user, db_session):
    # Create another patient
    from app.core.security import create_access_token, get_password_hash
    from app.models.user import PatientProfile, User

    other_user = User(
        email="otherpatient@pulseguardian.ai",
        hashed_password=get_password_hash("password123"),
        full_name="Other Patient",
        role="patient",
        preferred_language="en",
        is_active=True
    )
    db_session.add(other_user)
    db_session.flush()

    other_profile = PatientProfile(user_id=other_user.id, blood_group="A+")
    db_session.add(other_profile)
    db_session.commit()

    other_token = create_access_token(subject=other_user.id, role="patient")
    headers = {"Authorization": f"Bearer {other_token}"}

    # Other patient tries to view test_patient_user's profile
    target_id = test_patient_user.patient_profile.id
    response = client.get(f"/api/v1/users/patients/{target_id}", headers=headers)
    assert response.status_code == 403
    assert "You can only view your own" in response.json()["detail"]


def test_update_patient_profile(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    patient_id = test_patient_user.patient_profile.id
    update_payload = {
        "blood_group": "AB+",
        "medical_history": "Mild asthma and hypertension",
        "emergency_contact_phone": "+919999888877",
        "device_status": "online"
    }
    response = client.put(f"/api/v1/users/patients/{patient_id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["blood_group"] == "AB+"
    assert data["medical_history"] == "Mild asthma and hypertension"
    assert data["emergency_contact_phone"] == "+919999888877"
    assert data["device_status"] == "online"


def test_create_and_query_association(
    client,
    caregiver_token,
    test_patient_user,
    test_caregiver_user
):
    headers = {"Authorization": f"Bearer {caregiver_token}"}
    patient_id = test_patient_user.patient_profile.id
    caregiver_id = test_caregiver_user.caregiver_profile.id

    # 1. Create association (Tier 1 Primary Caregiver)
    assoc_payload = {
        "patient_id": patient_id,
        "caregiver_id": caregiver_id,
        "is_primary": True,
        "access_level": "full",
        "escalation_tier": 1
    }
    response = client.post("/api/v1/users/associations", json=assoc_payload, headers=headers)
    assert response.status_code == 201
    assoc_data = response.json()
    assert assoc_data["patient_id"] == patient_id
    assert assoc_data["caregiver_id"] == caregiver_id
    assert assoc_data["is_primary"] is True
    assert assoc_data["escalation_tier"] == 1
    association_id = assoc_data["id"]

    # 2. Duplicate link fails
    dup_resp = client.post("/api/v1/users/associations", json=assoc_payload, headers=headers)
    assert dup_resp.status_code == 400
    assert "already linked" in dup_resp.json()["detail"]

    # 3. Query caregivers for patient
    cg_list_resp = client.get(f"/api/v1/users/patients/{patient_id}/caregivers", headers=headers)
    assert cg_list_resp.status_code == 200
    cg_list = cg_list_resp.json()
    assert len(cg_list) == 1
    assert cg_list[0]["caregiver_id"] == caregiver_id

    # 4. Query patients for caregiver
    pt_list_resp = client.get(f"/api/v1/users/caregivers/{caregiver_id}/patients", headers=headers)
    assert pt_list_resp.status_code == 200
    pt_list = pt_list_resp.json()
    assert len(pt_list) == 1
    assert pt_list[0]["patient_id"] == patient_id

    # 5. Delete association
    del_resp = client.delete(f"/api/v1/users/associations/{association_id}", headers=headers)
    assert del_resp.status_code == 204

    # 6. Verify removed
    cg_list_after = client.get(f"/api/v1/users/patients/{patient_id}/caregivers", headers=headers).json()
    assert len(cg_list_after) == 0
