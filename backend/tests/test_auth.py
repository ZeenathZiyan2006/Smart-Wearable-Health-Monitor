def test_register_patient_success(client):
    payload = {
        "email": "newpatient@pulseguardian.ai",
        "password": "securepassword123",
        "full_name": "Ananya Sharma",
        "role": "patient",
        "phone_number": "+919876500001",
        "preferred_language": "hi",
        "blood_group": "B+",
        "device_uuid": "PG-DEV-999"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newpatient@pulseguardian.ai"
    assert data["role"] == "patient"
    assert data["patient_profile"] is not None
    assert data["patient_profile"]["blood_group"] == "B+"
    assert data["patient_profile"]["device_uuid"] == "PG-DEV-999"
    assert data["caregiver_profile"] is None


def test_register_caregiver_success(client):
    payload = {
        "email": "newcaregiver@pulseguardian.ai",
        "password": "securepassword123",
        "full_name": "Vikram Patel",
        "role": "caregiver",
        "phone_number": "+919876500002",
        "preferred_language": "en",
        "relationship_type": "Son",
        "organization": "Home Care",
        "notification_preference": "all"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newcaregiver@pulseguardian.ai"
    assert data["role"] == "caregiver"
    assert data["caregiver_profile"] is not None
    assert data["caregiver_profile"]["relationship_type"] == "Son"
    assert data["patient_profile"] is None


def test_register_duplicate_email_fails(client, test_patient_user):
    payload = {
        "email": test_patient_user.email,
        "password": "password123",
        "full_name": "Duplicate User",
        "role": "patient"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_register_invalid_role_fails(client):
    payload = {
        "email": "invalidrole@pulseguardian.ai",
        "password": "password123",
        "full_name": "Invalid Role User",
        "role": "superman"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "Invalid role" in response.json()["detail"]


def test_login_success(client, test_patient_user):
    payload = {
        "email": test_patient_user.email,
        "password": "patient123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == test_patient_user.email
    assert data["role"] == "patient"


def test_login_wrong_password_fails(client, test_patient_user):
    payload = {
        "email": test_patient_user.email,
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_email_fails(client):
    payload = {
        "email": "nonexistent@pulseguardian.ai",
        "password": "somepassword"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_refresh_token_success(client, test_patient_user):
    # First login to get a real refresh token
    login_resp = client.post("/api/v1/auth/login", json={
        "email": test_patient_user.email,
        "password": "patient123"
    })
    refresh_tok = login_resp.json()["refresh_token"]

    # Use refresh token
    refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_tok})
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_with_invalid_token_fails(client):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.jwt.token"})
    assert response.status_code == 401
    assert "Invalid or expired refresh token" in response.json()["detail"]


def test_get_current_user_me_success(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_patient_user.email
    assert data["patient_profile"]["device_uuid"] == "PG-ESP32-001"


def test_get_current_user_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
