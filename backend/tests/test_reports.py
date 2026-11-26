def test_health_dashboard_endpoint(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/health/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "latest_vitals" in data
    assert "summary_24h" in data
    assert "disclaimer" in data


def test_daily_and_weekly_reports(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}

    # Daily report
    daily_res = client.get("/api/v1/health/reports/daily", headers=headers)
    assert daily_res.status_code == 200
    daily_data = daily_res.json()
    assert "hourly_timeline" in daily_data
    assert len(daily_data["hourly_timeline"]) == 24

    # Weekly report
    weekly_res = client.get("/api/v1/health/reports/weekly", headers=headers)
    assert weekly_res.status_code == 200
    weekly_data = weekly_res.json()
    assert "daily_breakdown" in weekly_data


def test_export_health_records(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}

    # JSON export
    res_json = client.get("/api/v1/health/reports/export?format=json&days=7", headers=headers)
    assert res_json.status_code == 200
    assert "records" in res_json.json()

    # CSV export
    res_csv = client.get("/api/v1/health/reports/export?format=csv&days=7", headers=headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
