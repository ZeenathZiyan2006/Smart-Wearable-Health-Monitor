from app.models.notification import InAppNotification
from datetime import datetime, timezone

def test_notification_lifecycle(client, patient_token, test_patient_user, db_session):
    # Seed 2 test notifications directly
    n1 = InAppNotification(
        user_id=test_patient_user.id,
        title="Abnormal Heart Rate",
        body="High heart rate detected: 135 BPM",
        notification_type="health",
        severity="warning",
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    n2 = InAppNotification(
        user_id=test_patient_user.id,
        title="Device Connected",
        body="ESP32 band is now connected",
        notification_type="device",
        severity="info",
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add_all([n1, n2])
    db_session.commit()
    db_session.refresh(n1)
    db_session.refresh(n2)

    headers = {"Authorization": f"Bearer {patient_token}"}

    # 1. Unread count
    count_res = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] >= 2

    # 2. List notifications
    list_res = client.get("/api/v1/notifications", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 2

    # 3. Mark one read
    read_res = client.patch(f"/api/v1/notifications/{n1.id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # 4. Mark all read
    read_all = client.post("/api/v1/notifications/read-all", headers=headers)
    assert read_all.status_code == 200

    # 5. Archive / Delete
    del_res = client.delete(f"/api/v1/notifications/{n2.id}", headers=headers)
    assert del_res.status_code == 200
