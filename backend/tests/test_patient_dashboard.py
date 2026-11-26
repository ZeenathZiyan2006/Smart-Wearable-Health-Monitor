import pytest
from fastapi import status

def test_patient_dashboard_endpoints(client):
    """Test full patient dashboard CRUD for medicines, reminders, appointments, hydration, conditions, allergies."""
    # 1. Register a patient to get a token
    p_data = {
        "full_name": "Aarav Sharma",
        "date_of_birth": "1990-01-15",
        "gender": "male",
        "contact_number": "+91 9123456789",
        "family_email": "sharma.family@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    reg_res = client.post("/api/v1/patient/register", json=p_data)
    assert reg_res.status_code == status.HTTP_201_CREATED
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Medicine Management (Module 4)
    med_payload = {
        "medicine_name": "Metformin 500mg",
        "dosage": "1 Tablet",
        "frequency": "Twice daily",
        "scheduled_times": "08:00,20:00",
        "total_quantity": 60,
        "remaining_quantity": 60
    }
    med_create = client.post("/api/v1/patient/dashboard/medicines", json=med_payload, headers=headers)
    assert med_create.status_code == status.HTTP_201_CREATED
    med_id = med_create.json()["id"]
    assert med_create.json()["medicine_name"] == "Metformin 500mg"

    # Fetch medicines
    med_list = client.get("/api/v1/patient/dashboard/medicines", headers=headers)
    assert med_list.status_code == status.HTTP_200_OK
    assert len(med_list.json()) >= 1

    # Record action: taken (decreases remaining quantity)
    action_res = client.post(f"/api/v1/patient/dashboard/medicines/{med_id}/action", json={"status": "taken", "notes": "With morning breakfast"}, headers=headers)
    assert action_res.status_code == status.HTTP_200_OK
    assert action_res.json()["status"] == "taken"

    # Verify remaining quantity is decremented on the medicine
    med_list_updated = client.get("/api/v1/patient/dashboard/medicines", headers=headers)
    assert med_list_updated.status_code == status.HTTP_200_OK
    updated_med = next(m for m in med_list_updated.json() if m["id"] == med_id)
    assert updated_med["remaining_quantity"] == 59
    assert updated_med["consumed_quantity"] == 1

    # 3. Smart Reminders (Module 5)
    rem_payload = {
        "title": "Evening Blood Pressure & Walk",
        "reminder_type": "medicine",
        "reminder_time": "19:00",
        "is_enabled": True
    }
    rem_create = client.post("/api/v1/patient/dashboard/reminders", json=rem_payload, headers=headers)
    assert rem_create.status_code == status.HTTP_201_CREATED
    rem_id = rem_create.json()["id"]

    # Toggle reminder
    rem_toggle = client.put(f"/api/v1/patient/dashboard/reminders/{rem_id}", json={"is_enabled": False}, headers=headers)
    assert rem_toggle.status_code == status.HTTP_200_OK
    assert rem_toggle.json()["is_enabled"] is False

    # 4. Doctor Consultations (Module 7)
    appt_payload = {
        "doctor_name": "Dr. Sunita Rao",
        "specialization": "Cardiologist",
        "hospital_name": "Manipal Heart Centre",
        "appointment_date": "2026-12-05T10:30:00",
        "reason": "Routine Holter ECG follow-up"
    }
    appt_create = client.post("/api/v1/patient/dashboard/appointments", json=appt_payload, headers=headers)
    assert appt_create.status_code == status.HTTP_201_CREATED
    assert appt_create.json()["doctor_name"] == "Dr. Sunita Rao"

    appt_list = client.get("/api/v1/patient/dashboard/appointments", headers=headers)
    assert appt_list.status_code == status.HTTP_200_OK
    assert len(appt_list.json()) >= 1

    # 5. Hydration Tracking (Module 1)
    hyd_post = client.post("/api/v1/patient/dashboard/hydration", json={"amount_ml": 250}, headers=headers)
    assert hyd_post.status_code == status.HTTP_200_OK
    hyd_summary = hyd_post.json()
    assert hyd_summary["total_intake_ml"] >= 250

    # 6. Medical Conditions & Allergies (Module 2)
    cond_post = client.post("/api/v1/patient/dashboard/conditions", json={"condition_name": "Hypertension (Stage 1)", "severity": "mild"}, headers=headers)
    assert cond_post.status_code == status.HTTP_201_CREATED
    assert cond_post.json()["condition_name"] == "Hypertension (Stage 1)"

    allg_post = client.post("/api/v1/patient/dashboard/allergies", json={"allergen": "Penicillin", "severity": "severe"}, headers=headers)
    assert allg_post.status_code == status.HTTP_201_CREATED
    assert allg_post.json()["allergen"] == "Penicillin"


def test_patient_data_isolation_between_two_accounts(client):
    """
    Phase 1 Test:
    Verify strict isolation between two patient accounts.
    Prevent Patient 2 from accessing Patient 1's records via query parameters, URL, or payloads.
    """
    # 1. Register Patient 1
    p1_data = {
        "full_name": "Patient Alpha",
        "date_of_birth": "1988-06-12",
        "gender": "female",
        "contact_number": "+91 9888811111",
        "family_email": "alpha.family@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    r1 = client.post("/api/v1/patient/register", json=p1_data)
    assert r1.status_code == status.HTTP_201_CREATED
    token1 = r1.json()["access_token"]
    h1 = {"Authorization": f"Bearer {token1}"}

    # Patient 1 adds medicine
    med_res = client.post("/api/v1/patient/dashboard/medicines", json={
        "medicine_name": "Alpha-Statin 10mg",
        "dosage": "1 Tablet",
        "frequency": "Daily",
        "total_quantity": 30,
        "remaining_quantity": 30
    }, headers=h1)
    assert med_res.status_code == status.HTTP_201_CREATED
    p1_patient_id = med_res.json()["patient_id"]

    # 2. Register Patient 2
    p2_data = {
        "full_name": "Patient Beta",
        "date_of_birth": "1992-09-24",
        "gender": "male",
        "contact_number": "+91 9777722222",
        "family_email": "beta.family@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    r2 = client.post("/api/v1/patient/register", json=p2_data)
    assert r2.status_code == status.HTTP_201_CREATED
    token2 = r2.json()["access_token"]
    h2 = {"Authorization": f"Bearer {token2}"}

    # 3. Security Check: Patient 2 tries to access Patient 1's medicines via URL parameter
    leak_attempt = client.get(f"/api/v1/patient/dashboard/medicines?patient_id={p1_patient_id}", headers=h2)
    assert leak_attempt.status_code == status.HTTP_403_FORBIDDEN
    assert "Access denied" in leak_attempt.json()["detail"]

    # 4. Security Check: Patient 2 tries to create medicine under Patient 1's ID
    inject_attempt = client.post(f"/api/v1/patient/dashboard/medicines?patient_id={p1_patient_id}", json={
        "medicine_name": "Malicious Tablet",
        "dosage": "500mg",
        "frequency": "Daily"
    }, headers=h2)
    assert inject_attempt.status_code == status.HTTP_403_FORBIDDEN

    # 5. Security Check: Patient 2 tries to read Patient 1's telemetry
    telemetry_attempt = client.get(f"/api/v1/health/latest?patient_id={p1_patient_id}", headers=h2)
    assert telemetry_attempt.status_code == status.HTTP_403_FORBIDDEN

    # 6. Security Check: Patient 2 tries to read Patient 1's GPS location
    location_attempt = client.get(f"/api/v1/location/latest/{p1_patient_id}", headers=h2)
    assert location_attempt.status_code == status.HTTP_403_FORBIDDEN

    # 7. Patient 2 accesses their own dashboard - must be cleanly isolated and empty
    p2_own_meds = client.get("/api/v1/patient/dashboard/medicines", headers=h2)
    assert p2_own_meds.status_code == status.HTTP_200_OK
    assert len(p2_own_meds.json()) == 0
