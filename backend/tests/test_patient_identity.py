import pytest
from fastapi import status

def test_patient_registration_generates_unique_id(client):
    """Scenario 1: New patient registration generates a unique Patient ID (PT-2026-XXXXXX)."""
    payload = {
        "full_name": "Rahul Kumar",
        "date_of_birth": "1995-04-12",
        "gender": "male",
        "contact_number": "+91 9876543210",
        "individual_email": "rahul.personal@gmail.com",
        "family_email": "family.kumar@gmail.com",
        "address": "42 MG Road, Bangalore",
        "emergency_contact": "+91 9876543211",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    res = client.post("/api/v1/patient/register", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["status"] == "success"
    assert data["patient_name"] == "Rahul Kumar"
    assert data["patient_id"].startswith("PT-2026-")
    assert "access_token" in data
    assert data["family_email"] == "family.kumar@gmail.com"


def test_two_patients_can_share_same_family_email(client):
    """Scenario 2: Two patients can share the same family email with distinct Patient IDs."""
    # 1. Register Patient 1
    p1 = {
        "full_name": "Rahul Kumar",
        "date_of_birth": "1995-04-12",
        "gender": "male",
        "contact_number": "+91 9876543210",
        "family_email": "family.kumar@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    res1 = client.post("/api/v1/patient/register", json=p1)
    assert res1.status_code == status.HTTP_201_CREATED
    id1 = res1.json()["patient_id"]

    # 2. Register Patient 2 with same family email
    p2 = {
        "full_name": "Priya Kumar",
        "date_of_birth": "1998-08-22",
        "gender": "female",
        "contact_number": "+91 9876543222",
        "family_email": "family.kumar@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    res2 = client.post("/api/v1/patient/register", json=p2)
    assert res2.status_code == status.HTTP_201_CREATED
    id2 = res2.json()["patient_id"]

    assert id1 != id2
    assert id1.startswith("PT-2026-")
    assert id2.startswith("PT-2026-")


def test_duplicate_patient_detection_and_confirmation(client):
    """Scenario 3: Duplicate patient detection warns user, but allows confirmed family member."""
    # Register initial patient
    payload = {
        "full_name": "Rahul Kumar",
        "date_of_birth": "1995-04-12",
        "gender": "male",
        "contact_number": "+91 9876543210",
        "family_email": "family.kumar@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }
    res = client.post("/api/v1/patient/register", json=payload)
    assert res.status_code == status.HTTP_201_CREATED

    # Attempt to register again without force_duplicate
    dup_res = client.post("/api/v1/patient/register", json={**payload, "force_duplicate": False})
    assert dup_res.status_code == status.HTTP_409_CONFLICT
    err = dup_res.json()
    assert "detail" in err

    # Confirm and register with force_duplicate=True
    confirmed_res = client.post("/api/v1/patient/register", json={**payload, "force_duplicate": True})
    assert confirmed_res.status_code == status.HTTP_201_CREATED
    data2 = confirmed_res.json()
    assert data2["patient_name"] == "Rahul Kumar"
    assert data2["patient_id"].startswith("PT-2026-")


def test_existing_patient_can_login_with_patient_id(client):
    """Scenario 4: Existing patient can log in using their Patient ID and password."""
    # 1. Register
    reg_payload = {
        "full_name": "Amit Sharma",
        "contact_number": "+91 9123456789",
        "family_email": "sharma.family@gmail.com",
        "password": "Secret@Password99",
        "confirm_password": "Secret@Password99"
    }
    reg_res = client.post("/api/v1/patient/register", json=reg_payload)
    assert reg_res.status_code == status.HTTP_201_CREATED
    pat_id = reg_res.json()["patient_id"]

    # 2. Login via /api/v1/patient/login
    login_res = client.post("/api/v1/patient/login", json={
        "patient_id": pat_id,
        "password": "Secret@Password99"
    })
    assert login_res.status_code == status.HTTP_200_OK
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["patient_id"] == pat_id
    assert token_data["full_name"] == "Amit Sharma"

    # 3. Invalid password yields generic error without leaking info
    bad_login = client.post("/api/v1/patient/login", json={
        "patient_id": pat_id,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid Patient ID or password" in bad_login.json()["detail"]


def test_forgot_patient_id_otp_recovery(client):
    """Scenario 5: Forgot Patient ID OTP request and verification recovers patient IDs."""
    # Register two patients under same family email
    client.post("/api/v1/patient/register", json={
        "full_name": "Rahul Kumar",
        "contact_number": "+91 9876543210",
        "family_email": "family.kumar@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })
    client.post("/api/v1/patient/register", json={
        "full_name": "Priya Kumar",
        "contact_number": "+91 9876543222",
        "family_email": "family.kumar@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })

    # 1. Request OTP
    otp_req = client.post("/api/v1/patient/forgot-id/request-otp", json={
        "email_or_phone": "family.kumar@gmail.com"
    })
    assert otp_req.status_code == status.HTTP_200_OK
    req_data = otp_req.json()
    assert "demo_otp" in req_data
    demo_otp = req_data["demo_otp"]

    # 2. Verify OTP and recover patient IDs
    verify_res = client.post("/api/v1/patient/forgot-id/verify-otp", json={
        "email_or_phone": "family.kumar@gmail.com",
        "otp_code": demo_otp
    })
    assert verify_res.status_code == status.HTTP_200_OK
    rec_data = verify_res.json()
    assert rec_data["status"] == "success"
    assert len(rec_data["patients"]) >= 2
    names = [p["patient_name"] for p in rec_data["patients"]]
    assert "Rahul Kumar" in names
    assert "Priya Kumar" in names
    for p in rec_data["patients"]:
        assert p["patient_id"].startswith("PT-2026-")


def test_secure_family_email_recovery_distinguishes_same_names(client):
    """Scenario 6: Distinguishes patients with identical names under family account and includes age, DOB, and blood group."""
    # Register Senior Ramesh Kumar (age 68)
    client.post("/api/v1/patient/register", json={
        "full_name": "Ramesh Kumar",
        "date_of_birth": "1958-05-15",
        "gender": "male",
        "contact_number": "+91 9876500001",
        "family_email": "secure.family@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })
    # Register Junior Ramesh Kumar (age 25) with force_duplicate=True
    client.post("/api/v1/patient/register", json={
        "full_name": "Ramesh Kumar",
        "date_of_birth": "2001-09-20",
        "gender": "male",
        "contact_number": "+91 9876500002",
        "family_email": "secure.family@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "force_duplicate": True
    })

    # Request OTP
    otp_req = client.post("/api/v1/patient/forgot-id/request-otp", json={
        "email_or_phone": "secure.family@gmail.com"
    })
    assert otp_req.status_code == status.HTTP_200_OK
    demo_otp = otp_req.json().get("otp_demo") or otp_req.json().get("demo_otp")

    # Verify OTP
    verify_res = client.post("/api/v1/patient/forgot-id/verify-otp", json={
        "email_or_phone": "secure.family@gmail.com",
        "otp_code": demo_otp
    })
    assert verify_res.status_code == status.HTTP_200_OK
    patients = verify_res.json()["patients"]
    assert len(patients) == 2

    # Both have the same name, but distinct IDs, DOBs, and ages
    assert patients[0]["patient_id"] != patients[1]["patient_id"]
    dobs = {str(p["date_of_birth"]) for p in patients}
    assert "1958-05-15" in dobs
    assert "2001-09-20" in dobs
    for p in patients:
        assert p["age"] is not None
        assert p["authorized_for_recovery"] is True


def test_individual_patient_email_recovery_isolation(client):
    """Scenario 7: Individual patient email recovers only their profile, not all family profiles."""
    # Register Patient A with individual email
    client.post("/api/v1/patient/register", json={
        "full_name": "Ananya Sen",
        "date_of_birth": "1992-03-10",
        "contact_number": "+91 9888800001",
        "individual_email": "ananya.sen@workmail.com",
        "family_email": "sen.family@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })
    # Register Patient B under same family email
    client.post("/api/v1/patient/register", json={
        "full_name": "Vikram Sen",
        "date_of_birth": "1990-11-25",
        "contact_number": "+91 9888800002",
        "family_email": "sen.family@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })

    # Request OTP using individual email
    otp_req = client.post("/api/v1/patient/forgot-id/request-otp", json={
        "email_or_phone": "ananya.sen@workmail.com"
    })
    assert otp_req.status_code == status.HTTP_200_OK
    demo_otp = otp_req.json().get("otp_demo") or otp_req.json().get("demo_otp")

    # Verify OTP
    verify_res = client.post("/api/v1/patient/forgot-id/verify-otp", json={
        "email_or_phone": "ananya.sen@workmail.com",
        "otp_code": demo_otp
    })
    assert verify_res.status_code == status.HTTP_200_OK
    patients = verify_res.json()["patients"]
    # Should ONLY return Ananya Sen, never Vikram Sen
    assert len(patients) == 1
    assert patients[0]["patient_name"] == "Ananya Sen"


def test_patient_selection_confirmation_and_audit_log(client):
    """Scenario 8: Selection of patient logs audit trail and returns confirmed ID."""
    reg_res = client.post("/api/v1/patient/register", json={
        "full_name": "Sunil Varma",
        "contact_number": "+91 9777700001",
        "family_email": "varma.family@gmail.com",
        "password": "Password@123",
        "confirm_password": "Password@123"
    })
    pat_id = reg_res.json()["patient_id"]

    # Confirm selection
    confirm_res = client.post("/api/v1/patient/forgot-id/confirm-selection", json={
        "email": "varma.family@gmail.com",
        "patient_id": pat_id
    })
    assert confirm_res.status_code == status.HTTP_200_OK
    data = confirm_res.json()
    assert data["status"] == "success"
    assert data["patient_id"] == pat_id
    assert data["patient_name"] == "Sunil Varma"
    assert "confirmation_timestamp" in data

    # Unauthorized patient selection is blocked
    bad_confirm = client.post("/api/v1/patient/forgot-id/confirm-selection", json={
        "email": "different.family@gmail.com",
        "patient_id": pat_id
    })
    assert bad_confirm.status_code == status.HTTP_403_FORBIDDEN
