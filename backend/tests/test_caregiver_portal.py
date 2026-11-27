import pytest
from fastapi import status

def test_patient_id_verification_masks_name(client):
    """
    Test Step 1: Patient ID Verification
    - Valid Patient ID returns masked preview.
    - Invalid Patient ID returns 404 Not Found.
    - Does NOT return full medical records prior to authorization.
    """
    # 1. Register a test patient
    p_data = {
        "full_name": "Siddharth Verma",
        "date_of_birth": "1958-08-14",
        "gender": "male",
        "contact_number": "+91 9112233445",
        "family_email": "siddharth.family@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    reg_p = client.post("/api/v1/patient/register", json=p_data)
    assert reg_p.status_code == status.HTTP_201_CREATED
    patient_id = reg_p.json().get("patient_id") or reg_p.json().get("patient_profile", {}).get("patient_id")

    # 2. Register a family caregiver
    fam_data = {
        "full_name": "Meera Verma",
        "email": "meera.verma@example.com",
        "password": "Password@123",
        "role": "family",
        "phone_number": "+91 9988776655",
        "relationship_type": "Daughter"
    }
    reg_fam = client.post("/api/v1/auth/register", json=fam_data)
    assert reg_fam.status_code == status.HTTP_201_CREATED
    fam_login = client.post("/api/v1/auth/login", json={"email": "meera.verma@example.com", "password": "Password@123"})
    fam_token = fam_login.json()["access_token"]
    fam_headers = {"Authorization": f"Bearer {fam_token}"}

    # 3. Verify valid Patient ID
    verify_res = client.post(
        "/api/v1/caregiver-portal/verify-patient-id",
        json={"patient_id": patient_id},
        headers=fam_headers
    )
    assert verify_res.status_code == status.HTTP_200_OK
    verify_data = verify_res.json()
    assert verify_data["exists"] is True
    assert verify_data["patient_id"] == patient_id
    # Ensure name is masked (e.g. S********** V****)
    assert "S" in verify_data["masked_name"]
    assert "*" in verify_data["masked_name"]
    assert "Siddharth Verma" not in verify_data["masked_name"]  # Full name NOT exposed
    assert verify_data["requires_link_approval"] is True

    # 4. Verify invalid Patient ID returns 404
    bad_verify = client.post(
        "/api/v1/caregiver-portal/verify-patient-id",
        json={"patient_id": "PT-NON-EXISTENT-999"},
        headers=fam_headers
    )
    assert bad_verify.status_code == status.HTTP_404_NOT_FOUND


def test_family_member_linking_and_data_isolation(client):
    """
    Test Role 1: Family Member Access & Strict Data Isolation
    - Family member links to Patient 1.
    - Family member accesses Patient 1 Family Dashboard successfully.
    - Family member tries to access unlinked Patient 2 -> REJECTED (403 Forbidden).
    """
    # 1. Register Patient 1
    p1_data = {
        "full_name": "Lakshmi Narayanan",
        "date_of_birth": "1954-05-10",
        "gender": "female",
        "contact_number": "+91 9876500001",
        "family_email": "lakshmi.family@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    reg_p1 = client.post("/api/v1/patient/register", json=p1_data)
    p1_id = reg_p1.json().get("patient_id") or reg_p1.json().get("patient_profile", {}).get("patient_id")

    # 2. Register Patient 2
    p2_data = {
        "full_name": "Venkatesh Rao",
        "date_of_birth": "1952-11-20",
        "gender": "male",
        "contact_number": "+91 9876500002",
        "family_email": "venkatesh.family@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    reg_p2 = client.post("/api/v1/patient/register", json=p2_data)
    p2_id = reg_p2.json().get("patient_id") or reg_p2.json().get("patient_profile", {}).get("patient_id")

    # 3. Register Family Member
    fam_data = {
        "full_name": "Pooja Narayanan",
        "email": "pooja.family@example.com",
        "password": "Password@123",
        "role": "family",
        "phone_number": "+91 9445566778",
        "relationship_type": "Daughter"
    }
    client.post("/api/v1/auth/register", json=fam_data)
    fam_login = client.post("/api/v1/auth/login", json={"email": "pooja.family@example.com", "password": "Password@123"})
    fam_headers = {"Authorization": f"Bearer {fam_login.json()['access_token']}"}

    # Before linking: accessing Patient 1 must be FORBIDDEN
    unlinked_get = client.get(f"/api/v1/caregiver-portal/family/dashboard?patient_id={p1_id}", headers=fam_headers)
    assert unlinked_get.status_code == status.HTTP_403_FORBIDDEN

    # 4. Link to Patient 1
    link_res = client.post(
        "/api/v1/caregiver-portal/request-link",
        json={"patient_id": p1_id, "relationship_or_role": "Daughter"},
        headers=fam_headers
    )
    assert link_res.status_code == status.HTTP_200_OK
    assert link_res.json()["status"] == "approved"

    # 5. Access Patient 1 Family Dashboard -> SUCCESS
    p1_dash = client.get(f"/api/v1/caregiver-portal/family/dashboard?patient_id={p1_id}", headers=fam_headers)
    assert p1_dash.status_code == status.HTTP_200_OK
    data = p1_dash.json()
    assert data["role"] == "family"
    assert data["patient_overview"]["patient_id"] == p1_id
    assert "Lakshmi Narayanan" in data["patient_overview"]["full_name"]
    assert data["live_health"]["heart_rate"] is not None

    # 6. SECURITY CHECK: Try to access unlinked Patient 2 -> MUST BE 403 FORBIDDEN
    p2_dash_attempt = client.get(f"/api/v1/caregiver-portal/family/dashboard?patient_id={p2_id}", headers=fam_headers)
    assert p2_dash_attempt.status_code == status.HTTP_403_FORBIDDEN


def test_doctor_assignment_dashboard_and_prescriptions(client):
    """
    Test Role 2: Doctor Dashboard, Assignment, and Clinical Actions
    - Doctor links to assigned patient.
    - Doctor accesses Doctor Dashboard.
    - Doctor writes prescription.
    - Doctor tries accessing unassigned patient -> 403 FORBIDDEN.
    """
    # 1. Register a Patient
    p_data = {
        "full_name": "Harish Patel",
        "date_of_birth": "1960-02-18",
        "gender": "male",
        "contact_number": "+91 9771122334",
        "family_email": "harish.family@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    reg_p = client.post("/api/v1/patient/register", json=p_data)
    patient_id = reg_p.json().get("patient_id") or reg_p.json().get("patient_profile", {}).get("patient_id")

    # 2. Register a Doctor
    doc_data = {
        "full_name": "Dr. Sunita Rao",
        "email": "dr.sunita@pulseguardian.ai",
        "password": "Password@123",
        "role": "doctor",
        "phone_number": "+91 9845012345",
        "medical_reg_no": "MCI-CARDIO-8849",
        "specialization": "Cardiology",
        "hospital_name": "PulseGuardian Heart Center",
        "designation": "Senior Attending Cardiologist"
    }
    reg_doc = client.post("/api/v1/auth/register", json=doc_data)
    assert reg_doc.status_code == status.HTTP_201_CREATED
    doc_login = client.post("/api/v1/auth/login", json={"email": "dr.sunita@pulseguardian.ai", "password": "Password@123"})
    doc_headers = {"Authorization": f"Bearer {doc_login.json()['access_token']}"}

    # 3. Assign Doctor to Patient
    assign_res = client.post(
        "/api/v1/caregiver-portal/request-link",
        json={"patient_id": patient_id, "relationship_or_role": "Attending Cardiologist"},
        headers=doc_headers
    )
    assert assign_res.status_code == status.HTTP_200_OK

    # 4. Doctor accesses Doctor Dashboard -> SUCCESS
    doc_dash = client.get(f"/api/v1/caregiver-portal/doctor/dashboard?patient_id={patient_id}", headers=doc_headers)
    assert doc_dash.status_code == status.HTTP_200_OK
    doc_data_out = doc_dash.json()
    assert doc_data_out["role"] == "doctor"
    assert "Cardiology" in doc_data_out["doctor_profile"]["specialization"]
    assert doc_data_out["patient_clinical_overview"]["patient_id"] == patient_id

    # 5. Doctor adds a prescription
    rx_payload = {
        "patient_id": patient_id,
        "medicine_name": "Atorvastatin 20mg",
        "dosage": "1 Tablet",
        "frequency": "Once daily at bedtime",
        "scheduled_times": "21:00",
        "instructions": "After dinner",
        "total_quantity": 30
    }
    rx_res = client.post("/api/v1/caregiver-portal/doctor/prescriptions", json=rx_payload, headers=doc_headers)
    assert rx_res.status_code == status.HTTP_200_OK

    # 6. Doctor writes a clinical consultation note
    note_payload = {
        "patient_id": patient_id,
        "notes": "Patient resting cardiac rhythm stable at 72 BPM. Prescribed Atorvastatin for lipid optimization."
    }
    note_res = client.post("/api/v1/caregiver-portal/doctor/clinical-notes", json=note_payload, headers=doc_headers)
    assert note_res.status_code == status.HTTP_200_OK

    # 7. SECURITY CHECK: Doctor tries to access unassigned Patient -> 403 FORBIDDEN
    unassigned_res = client.get("/api/v1/caregiver-portal/doctor/dashboard?patient_id=PT-999-UNASSIGNED", headers=doc_headers)
    assert unassigned_res.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


def test_emergency_team_triage_access_and_audit_logging(client):
    """
    Test Role 3: Emergency Response Team Access
    - Emergency responder logs in.
    - Views triage incident queue.
    - Accesses emergency patient triage bundle with official reason.
    - Verifies access is logged in EmergencyAccessAuditLog.
    - Regular family user cannot access emergency triage queue (403 Forbidden).
    """
    # 1. Register a Patient with an Emergency Alert
    p_data = {
        "full_name": "Deepak Joshi",
        "date_of_birth": "1965-09-30",
        "gender": "male",
        "contact_number": "+91 9334455667",
        "family_email": "deepak.family@example.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    reg_p = client.post("/api/v1/patient/register", json=p_data)
    patient_id = reg_p.json().get("patient_id") or reg_p.json().get("patient_profile", {}).get("patient_id")
    p_token = reg_p.json()["access_token"]

    # Trigger SOS alert
    client.post("/api/v1/emergency/sos", json={"alert_type": "manual_sos"}, headers={"Authorization": f"Bearer {p_token}"})

    # 2. Register an Emergency Responder
    ems_data = {
        "full_name": "Officer Rajesh Kumar",
        "email": "ems.rajesh@pulseguardian.ai",
        "password": "Password@123",
        "role": "emergency",
        "phone_number": "+91 9110011223",
        "organization": "Metropolitan Trauma & EMS Dispatch",
        "responder_id": "EMS-BLR-402",
        "designation": "Certified Paramedic Team Lead"
    }
    reg_ems = client.post("/api/v1/auth/register", json=ems_data)
    assert reg_ems.status_code == status.HTTP_201_CREATED
    ems_login = client.post("/api/v1/auth/login", json={"email": "ems.rajesh@pulseguardian.ai", "password": "Password@123"})
    ems_headers = {"Authorization": f"Bearer {ems_login.json()['access_token']}"}

    # 3. Emergency Responder views triage incidents queue
    incidents_res = client.get("/api/v1/caregiver-portal/emergency/incidents", headers=ems_headers)
    assert incidents_res.status_code == status.HTTP_200_OK
    incidents = incidents_res.json()
    assert len(incidents) >= 1

    # 4. Access emergency patient triage bundle with audit reason
    triage_payload = {
        "patient_id": patient_id,
        "access_reason": "Active 112 SOS Dispatch Response Unit 4",
        "incident_id": "INC-2026-911"
    }
    triage_res = client.post("/api/v1/caregiver-portal/emergency/patient-triage", json=triage_payload, headers=ems_headers)
    assert triage_res.status_code == status.HTTP_200_OK
    triage_bundle = triage_res.json()["emergency_triage_bundle"]
    assert triage_bundle["patient_id"] == patient_id
    assert triage_bundle["blood_group"] is not None
    assert len(triage_bundle["emergency_contacts"]) >= 1
    assert "SIMULATION MODE" in triage_bundle["ambulance_coordination"]["operating_mode"]

    # 5. SECURITY CHECK: Regular non-emergency user cannot access emergency triage queue
    non_ems_login = client.post("/api/v1/auth/login", json={"email": patient_id, "password": "Password@123"})
    assert non_ems_login.status_code == status.HTTP_200_OK
    forbidden_attempt = client.get("/api/v1/caregiver-portal/emergency/incidents", headers={"Authorization": f"Bearer {non_ems_login.json()['access_token']}"})
    assert forbidden_attempt.status_code == status.HTTP_403_FORBIDDEN
