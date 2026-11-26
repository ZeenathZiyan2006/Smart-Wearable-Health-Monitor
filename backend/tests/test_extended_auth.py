def test_update_profile(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    update_payload = {
        "full_name": "Ramesh Kumar Updated",
        "phone_number": "+919999988888",
        "preferred_language": "hi"
    }
    response = client.put("/api/v1/auth/me", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Ramesh Kumar Updated"
    assert data["preferred_language"] == "hi"


def test_change_password_workflow(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}

    # Wrong old password
    wrong_payload = {
        "old_password": "WrongPassword123",
        "new_password": "NewSecretPassword@123"
    }
    fail_res = client.post("/api/v1/auth/change-password", json=wrong_payload, headers=headers)
    assert fail_res.status_code == 400

    # Correct old password (from conftest test_patient_user is patient123)
    ok_payload = {
        "old_password": "patient123",
        "new_password": "NewSecretPassword@123"
    }
    ok_res = client.post("/api/v1/auth/change-password", json=ok_payload, headers=headers)
    assert ok_res.status_code == 200

    # Change back
    reset_back = {
        "old_password": "NewSecretPassword@123",
        "new_password": "patient123"
    }
    res_back = client.post("/api/v1/auth/change-password", json=reset_back, headers=headers)
    assert res_back.status_code == 200


def test_logout_and_forgot_password(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}

    # Logout
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # Forgot password
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": "patient@pulseguardian.ai"})
    assert forgot_res.status_code == 200
    token = forgot_res.json().get("reset_token")
    assert token is not None

    # Reset password with token
    reset_res = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "ResetPassword@123"})
    assert reset_res.status_code == 200

    # Reset back to original
    reset_back = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "patient123"})
    assert reset_back.status_code == 200
