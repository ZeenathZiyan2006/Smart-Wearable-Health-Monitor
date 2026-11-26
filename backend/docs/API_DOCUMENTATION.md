# PulseGuardian AI – Backend API Documentation (v1)

Base URL: `http://localhost:8000/api/v1`  
Interactive Swagger UI: `http://localhost:8000/api/v1/docs`  
Interactive ReDoc UI: `http://localhost:8000/api/v1/redoc`

---

## 1. Authentication & User Management

### 1.1 User Registration
* **Endpoint**: `POST /api/v1/auth/register`
* **Access**: Public
* **Description**: Register a new patient or caregiver with automatic profile initialization.

**Request JSON (Patient):**
```json
{
  "email": "ramesh.kumar@pulseguardian.ai",
  "password": "securepassword123",
  "full_name": "Ramesh Kumar",
  "role": "patient",
  "phone_number": "+919876543210",
  "preferred_language": "kn",
  "date_of_birth": "1954-06-15",
  "gender": "Male",
  "blood_group": "O+",
  "emergency_contact_phone": "+919876543211",
  "device_uuid": "PG-ESP32-001"
}
```

**Response JSON (201 Created):**
```json
{
  "id": 1,
  "email": "ramesh.kumar@pulseguardian.ai",
  "full_name": "Ramesh Kumar",
  "role": "patient",
  "phone_number": "+919876543210",
  "preferred_language": "kn",
  "is_active": true,
  "created_at": "2026-11-23T15:00:00Z",
  "updated_at": "2026-11-23T15:00:00Z",
  "patient_profile": {
    "id": 1,
    "user_id": 1,
    "date_of_birth": "1954-06-15",
    "gender": "Male",
    "blood_group": "O+",
    "medical_history": null,
    "emergency_contact_phone": "+919876543211",
    "device_uuid": "PG-ESP32-001",
    "device_status": "offline",
    "last_sync_at": null,
    "created_at": "2026-11-23T15:00:00Z",
    "updated_at": "2026-11-23T15:00:00Z"
  },
  "caregiver_profile": null
}
```

---

### 1.2 User Login
* **Endpoint**: `POST /api/v1/auth/login`
* **Access**: Public
* **Description**: Authenticate with email and password to receive JWT access and refresh tokens.

**Request JSON:**
```json
{
  "email": "ramesh.kumar@pulseguardian.ai",
  "password": "securepassword123"
}
```

**Response JSON (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": 1,
  "email": "ramesh.kumar@pulseguardian.ai",
  "role": "patient",
  "full_name": "Ramesh Kumar"
}
```

---

## 2. Wearable Health Data Ingestion

### 2.1 Real-Time Health Telemetry Ingestion
* **Endpoint**: `POST /api/v1/health/telemetry`
* **Access**: Hardware ESP32 (`device_uuid`) or Authenticated Patient (Bearer JWT)
* **Description**: Ingests real-time vitals, accelerometer readings, fall status and battery level. Performs acute anomaly pre-screening and idempotent deduplication.

**Request JSON:**
```json
{
  "device_uuid": "PG-ESP32-001",
  "heart_rate": 74.0,
  "spo2": 98.5,
  "temperature": 36.6,
  "temperature_unit": "C",
  "step_count": 3400,
  "activity_type": "walking",
  "sleep_duration_minutes": 420,
  "fall_detected": false,
  "accelerometer_x": 0.02,
  "accelerometer_y": 0.98,
  "accelerometer_z": 0.15,
  "battery_percentage": 82.0,
  "recorded_at": "2026-11-23T15:30:00Z"
}
```

**Response JSON (201 Created):**
```json
{
  "id": 101,
  "patient_id": 1,
  "device_uuid": "PG-ESP32-001",
  "heart_rate": 74.0,
  "spo2": 98.5,
  "temperature": 36.6,
  "temperature_unit": "C",
  "step_count": 3400,
  "activity_type": "walking",
  "sleep_duration_minutes": 420,
  "fall_detected": false,
  "accelerometer_x": 0.02,
  "accelerometer_y": 0.98,
  "accelerometer_z": 0.15,
  "battery_percentage": 82.0,
  "is_anomalous": false,
  "anomaly_score": 0.0,
  "anomaly_reason": null,
  "recorded_at": "2026-11-23T15:30:00Z",
  "created_at": "2026-11-23T15:30:01Z"
}
```

---

### 2.2 Offline Synchronization Batch Telemetry Ingestion
* **Endpoint**: `POST /api/v1/health/telemetry/batch`
* **Access**: Hardware ESP32 (`device_uuid`) or Authenticated Patient (Bearer JWT)
* **Description**: Ingests offline-buffered readings from wearable flash storage. Detects and skips existing timestamps to guarantee idempotency.

**Request JSON:**
```json
{
  "device_uuid": "PG-ESP32-001",
  "readings": [
    {
      "heart_rate": 72.0,
      "spo2": 98.0,
      "temperature": 36.6,
      "temperature_unit": "C",
      "step_count": 3100,
      "activity_type": "resting",
      "battery_percentage": 85.0,
      "recorded_at": "2026-11-23T15:15:00Z"
    },
    {
      "heart_rate": 142.0,
      "spo2": 94.0,
      "temperature": 37.1,
      "temperature_unit": "C",
      "step_count": 3250,
      "activity_type": "resting",
      "battery_percentage": 84.0,
      "recorded_at": "2026-11-23T15:20:00Z"
    }
  ]
}
```

**Response JSON (201 Created):**
```json
{
  "total_received": 2,
  "inserted": 2,
  "duplicates_skipped": 0,
  "readings": [
    {
      "id": 102,
      "patient_id": 1,
      "device_uuid": "PG-ESP32-001",
      "heart_rate": 72.0,
      "spo2": 98.0,
      "temperature": 36.6,
      "temperature_unit": "C",
      "step_count": 3100,
      "activity_type": "resting",
      "sleep_duration_minutes": null,
      "fall_detected": false,
      "battery_percentage": 85.0,
      "is_anomalous": false,
      "anomaly_score": 0.0,
      "anomaly_reason": null,
      "recorded_at": "2026-11-23T15:15:00Z",
      "created_at": "2026-11-23T15:31:00Z"
    },
    {
      "id": 103,
      "patient_id": 1,
      "device_uuid": "PG-ESP32-001",
      "heart_rate": 142.0,
      "spo2": 94.0,
      "temperature": 37.1,
      "temperature_unit": "C",
      "step_count": 3250,
      "activity_type": "resting",
      "sleep_duration_minutes": null,
      "fall_detected": false,
      "battery_percentage": 84.0,
      "is_anomalous": true,
      "anomaly_score": 0.7,
      "anomaly_reason": "Resting Tachycardia: High heart rate (142.0 BPM)",
      "recorded_at": "2026-11-23T15:20:00Z",
      "created_at": "2026-11-23T15:31:00Z"
    }
  ]
}
```

---

### 2.3 Latest Health Vitals
* **Endpoint**: `GET /api/v1/health/latest`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Query Params**: `patient_id` (optional for patient, required for caregiver/admin)

**Response JSON (200 OK):**
```json
{
  "id": 103,
  "patient_id": 1,
  "device_uuid": "PG-ESP32-001",
  "heart_rate": 142.0,
  "spo2": 94.0,
  "temperature": 37.1,
  "temperature_unit": "C",
  "step_count": 3250,
  "activity_type": "resting",
  "sleep_duration_minutes": null,
  "fall_detected": false,
  "accelerometer_x": null,
  "accelerometer_y": null,
  "accelerometer_z": null,
  "battery_percentage": 84.0,
  "is_anomalous": true,
  "anomaly_score": 0.7,
  "anomaly_reason": "Resting Tachycardia: High heart rate (142.0 BPM)",
  "recorded_at": "2026-11-23T15:20:00Z",
  "created_at": "2026-11-23T15:31:00Z"
}
```

---

### 2.4 Health History
* **Endpoint**: `GET /api/v1/health/history`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Query Params**: `patient_id`, `start_time`, `end_time`, `anomalies_only`, `skip`, `limit`

**Response JSON (200 OK):**
```json
[
  {
    "id": 103,
    "patient_id": 1,
    "heart_rate": 142.0,
    "spo2": 94.0,
    "temperature": 37.1,
    "is_anomalous": true,
    "anomaly_reason": "Resting Tachycardia: High heart rate (142.0 BPM)",
    "recorded_at": "2026-11-23T15:20:00Z"
  },
  {
    "id": 102,
    "patient_id": 1,
    "heart_rate": 72.0,
    "spo2": 98.0,
    "temperature": 36.6,
    "is_anomalous": false,
    "anomaly_reason": null,
    "recorded_at": "2026-11-23T15:15:00Z"
  }
]
```

---

### 2.5 Health Trends & Aggregation
* **Endpoint**: `GET /api/v1/health/trends`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Query Params**: `patient_id`, `hours` (e.g. 24 for daily, 168 for weekly)

**Response JSON (200 OK):**
```json
{
  "patient_id": 1,
  "time_window_hours": 24,
  "total_readings": 48,
  "heart_rate_trend": "stable",
  "avg_heart_rate": 74.2,
  "min_heart_rate": 58.0,
  "max_heart_rate": 142.0,
  "avg_spo2": 97.8,
  "min_spo2": 93.0,
  "max_spo2": 99.0,
  "avg_temperature": 36.7,
  "min_temperature": 36.2,
  "max_temperature": 37.4,
  "total_steps": 4820,
  "total_sleep_minutes": 420,
  "total_falls": 0,
  "anomaly_count": 1,
  "hourly_averages": [
    {
      "hour": "2026-11-23 14:00",
      "avg_hr": 71.5,
      "avg_spo2": 98.0,
      "avg_temp": 36.6
    },
    {
      "hour": "2026-11-23 15:00",
      "avg_hr": 82.0,
      "avg_spo2": 97.2,
      "avg_temp": 36.8
    }
  ]
}
```

---

### 2.6 Wearable Device Status & Battery
* **Endpoint**: `GET /api/v1/health/device-status`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Query Params**: `patient_id` or `device_uuid`

**Response JSON (200 OK):**
```json
{
  "patient_id": 1,
  "device_uuid": "PG-ESP32-001",
  "device_status": "online",
  "battery_percentage": 82.0,
  "is_online": true,
  "is_stale": false,
  "last_sync_at": "2026-11-23T15:30:00Z",
  "last_recorded_at": "2026-11-23T15:30:00Z",
  "sensor_status": {
    "max30102_heart_rate_spo2": "active",
    "mpu6050_accelerometer": "active",
    "gps_neo6m": "active"
  }
}
```

---

## 3. GPS Location Tracking

### 3.1 Record GPS Location
* **Endpoint**: `POST /api/v1/location/track`
* **Access**: Hardware ESP32 (`device_uuid`) or Authenticated Patient (Bearer JWT)
* **Description**: Records real-time GPS coordinates. When GPS fix is lost or unavailable, `is_gps_available=false` records the unavailable status without inventing false coordinates.

**Request JSON (Active GPS Fix):**
```json
{
  "device_uuid": "PG-ESP32-001",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "altitude": 920.0,
  "accuracy": 4.2,
  "speed": 1.2,
  "is_gps_available": true,
  "device_battery": 82.0,
  "recorded_at": "2026-11-23T15:30:00Z"
}
```

**Response JSON (201 Created):**
```json
{
  "id": 51,
  "patient_id": 1,
  "device_uuid": "PG-ESP32-001",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "altitude": 920.0,
  "accuracy": 4.2,
  "speed": 1.2,
  "is_gps_available": true,
  "device_battery": 82.0,
  "recorded_at": "2026-11-23T15:30:00Z",
  "created_at": "2026-11-23T15:30:01Z"
}
```

**Request JSON (GPS Unavailable Indoors):**
```json
{
  "device_uuid": "PG-ESP32-001",
  "is_gps_available": false,
  "device_battery": 81.0,
  "recorded_at": "2026-11-23T15:35:00Z"
}
```

**Response JSON (201 Created - Coordinates Never Invented):**
```json
{
  "id": 52,
  "patient_id": 1,
  "device_uuid": "PG-ESP32-001",
  "latitude": null,
  "longitude": null,
  "altitude": null,
  "accuracy": null,
  "speed": null,
  "is_gps_available": false,
  "device_battery": 81.0,
  "recorded_at": "2026-11-23T15:35:00Z",
  "created_at": "2026-11-23T15:35:01Z"
}
```

---

### 3.2 Latest Patient GPS Location
* **Endpoint**: `GET /api/v1/location/latest/{patient_id}`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Returns latest known coordinate with freshness status. Automatically detects stale fixes (>15 minutes) or lost satellite locks.

**Response JSON (Active Fix - 200 OK):**
```json
{
  "patient_id": 1,
  "has_location": true,
  "is_stale": false,
  "status": "active",
  "latest_location": {
    "id": 51,
    "patient_id": 1,
    "device_uuid": "PG-ESP32-001",
    "latitude": 12.9716,
    "longitude": 77.5946,
    "altitude": 920.0,
    "accuracy": 4.2,
    "speed": 1.2,
    "is_gps_available": true,
    "device_battery": 82.0,
    "recorded_at": "2026-11-23T15:30:00Z",
    "created_at": "2026-11-23T15:30:01Z"
  },
  "message": "Real-time fix active."
}
```

**Response JSON (Stale Fix - >15 Minutes Old - 200 OK):**
```json
{
  "patient_id": 1,
  "has_location": true,
  "is_stale": true,
  "status": "stale",
  "latest_location": {
    "id": 51,
    "patient_id": 1,
    "latitude": 12.9716,
    "longitude": 77.5946,
    "recorded_at": "2026-11-23T14:45:00Z"
  },
  "message": "Fix age: 45 minute(s) old."
}
```

**Response JSON (GPS Unavailable - 200 OK):**
```json
{
  "patient_id": 1,
  "has_location": false,
  "is_stale": true,
  "status": "unavailable",
  "latest_location": null,
  "message": "GPS hardware was unavailable or indoor without satellite lock at last fix."
}
```

---

### 3.3 Patient Location History (Breadcrumb Trail)
* **Endpoint**: `GET /api/v1/location/history/{patient_id}`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Query Params**: `start_time`, `end_time`, `valid_fixes_only` (default true), `skip`, `limit`
* **Description**: Returns ordered list of historical GPS points for drawing route trajectories on caregiver maps.

**Response JSON (200 OK):**
```json
[
  {
    "id": 51,
    "patient_id": 1,
    "latitude": 12.9716,
    "longitude": 77.5946,
    "altitude": 920.0,
    "accuracy": 4.2,
    "speed": 1.2,
    "is_gps_available": true,
    "recorded_at": "2026-11-23T15:30:00Z",
    "created_at": "2026-11-23T15:30:01Z"
  },
  {
    "id": 50,
    "patient_id": 1,
    "latitude": 12.9712,
    "longitude": 77.5941,
    "altitude": 918.0,
    "accuracy": 4.0,
    "speed": 1.0,
    "is_gps_available": true,
    "recorded_at": "2026-11-23T15:25:00Z",
    "created_at": "2026-11-23T15:25:01Z"
  }
]
```


---

## 4. Emergency SOS & Caregiver Escalation

### 4.1 Trigger Manual SOS or Fall Detection Alert
* **Endpoint**: `POST /api/v1/emergency/sos`
* **Access**: Hardware ESP32 (`device_uuid`) or Authenticated Patient (Bearer JWT)
* **Description**: Instantly creates a critical emergency alert, automatically attaches latest known GPS breadcrumbs if omitted, and dispatches the multi-tier caregiver escalation ladder via background Celery workers.

**Request JSON:**
```json
{
  "device_uuid": "PG-ESP32-001",
  "alert_type": "manual_sos",
  "severity": "critical",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "location_accuracy": 4.5
}
```

**Response JSON (201 Created):**
```json
{
  "id": 1,
  "patient_id": 1,
  "device_uuid": "PG-ESP32-001",
  "alert_type": "manual_sos",
  "severity": "critical",
  "status": "escalating",
  "current_escalation_tier": 1,
  "latitude": 12.9716,
  "longitude": 77.5946,
  "location_accuracy": 4.5,
  "assistance_message": null,
  "voice_transcript": null,
  "detected_language": null,
  "translated_summary": null,
  "acknowledged_by_id": null,
  "acknowledged_at": null,
  "rejected_by_id": null,
  "rejected_at": null,
  "rejection_reason": null,
  "resolved_at": null,
  "resolution_notes": null,
  "created_at": "2026-11-23T16:00:00Z",
  "audit_logs": [
    {
      "id": 1,
      "alert_id": 1,
      "tier": 1,
      "notified_caregiver_id": 1,
      "notification_channel": "all",
      "provider": "development_mock",
      "recipient_address": "+919876543220",
      "status": "dispatched_mock",
      "message_payload": "Alert: manual_sos | Severity: critical | Location: Lat: 12.9716, Lon: 77.5946 (±4.5m)",
      "error_message": null,
      "retry_count": 0,
      "sent_at": "2026-11-23T16:00:01Z"
    }
  ]
}
```

---

### 4.2 "I'm Not Okay" Assistance Request
* **Endpoint**: `POST /api/v1/emergency/assistance`
* **Access**: Authenticated Patient (Bearer JWT) or Hardware Client (`device_uuid`)
* **Description**: Allows a patient to signal non-acute or acute distress with an optional symptom or situation message. Initiates caregiver escalation.

**Request JSON:**
```json
{
  "message": "Feeling severe dizziness and chest tightness after taking morning medication",
  "severity": "high",
  "latitude": 12.9710,
  "longitude": 77.5940
}
```

**Response JSON (201 Created):**
```json
{
  "id": 2,
  "patient_id": 1,
  "device_uuid": null,
  "alert_type": "not_okay_assistance",
  "severity": "high",
  "status": "escalating",
  "current_escalation_tier": 1,
  "latitude": 12.9710,
  "longitude": 77.5940,
  "location_accuracy": null,
  "assistance_message": "Feeling severe dizziness and chest tightness after taking morning medication",
  "created_at": "2026-11-23T16:05:00Z"
}
```

---

### 4.3 List Emergency Alerts
* **Endpoint**: `GET /api/v1/emergency/alerts`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Query Params**: `patient_id`, `status` (`triggered`, `escalating`, `acknowledged`, `rejected`, `timeout_exhausted`), `severity`, `skip`, `limit`

**Response JSON (200 OK):**
```json
[
  {
    "id": 1,
    "patient_id": 1,
    "alert_type": "manual_sos",
    "severity": "critical",
    "status": "escalating",
    "current_escalation_tier": 1,
    "latitude": 12.9716,
    "longitude": 77.5946,
    "created_at": "2026-11-23T16:00:00Z"
  }
]
```

---

### 4.4 Get Single Alert Details
* **Endpoint**: `GET /api/v1/emergency/{alert_id}`
* **Access**: Patient (Self) / Assigned Caregiver / Admin

**Response JSON (200 OK):**
```json
{
  "id": 1,
  "patient_id": 1,
  "alert_type": "manual_sos",
  "severity": "critical",
  "status": "escalating",
  "current_escalation_tier": 1,
  "latitude": 12.9716,
  "longitude": 77.5946,
  "location_accuracy": 4.5,
  "created_at": "2026-11-23T16:00:00Z",
  "audit_logs": [
    {
      "id": 1,
      "alert_id": 1,
      "tier": 1,
      "notified_caregiver_id": 1,
      "notification_channel": "all",
      "provider": "development_mock",
      "recipient_address": "+919876543220",
      "status": "dispatched_mock",
      "sent_at": "2026-11-23T16:00:01Z"
    }
  ]
}
```

---

### 4.5 Caregiver Acknowledge Alert
* **Endpoint**: `POST /api/v1/emergency/{alert_id}/acknowledge`
* **Access**: Assigned Caregiver / Admin (Patients cannot self-acknowledge)
* **Description**: Caregiver acknowledges receipt of emergency alert. Immediately halts the multi-tier escalation ladder and marks the responder identity and notes.

**Request JSON:**
```json
{
  "notes": "Spoke to patient via phone. Reaching patient residence in 5 minutes."
}
```

**Response JSON (200 OK):**
```json
{
  "id": 1,
  "patient_id": 1,
  "alert_type": "manual_sos",
  "severity": "critical",
  "status": "acknowledged",
  "current_escalation_tier": 1,
  "acknowledged_by_id": 2,
  "acknowledged_at": "2026-11-23T16:02:15Z",
  "resolution_notes": "Spoke to patient via phone. Reaching patient residence in 5 minutes.",
  "created_at": "2026-11-23T16:00:00Z"
}
```

---

### 4.6 Caregiver Reject / False Alarm
* **Endpoint**: `POST /api/v1/emergency/{alert_id}/reject`
* **Access**: Assigned Caregiver / Admin
* **Description**: Caregiver verifies that the alert was triggered accidentally or is a false alarm. Halts escalation ladder and logs the justification.

**Request JSON:**
```json
{
  "reason": "Patient called to confirm physical wearable SOS button was pressed accidentally during gardening."
}
```

**Response JSON (200 OK):**
```json
{
  "id": 1,
  "patient_id": 1,
  "alert_type": "manual_sos",
  "severity": "critical",
  "status": "rejected",
  "current_escalation_tier": 1,
  "rejected_by_id": 2,
  "rejected_at": "2026-11-23T16:03:00Z",
  "rejection_reason": "Patient called to confirm physical wearable SOS button was pressed accidentally during gardening.",
  "created_at": "2026-11-23T16:00:00Z"
}
```

---

### 4.7 Escalation Audit Trail History
* **Endpoint**: `GET /api/v1/emergency/{alert_id}/escalation-history`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Retrieves chronological history of every dispatch attempt, retry, caregiver notification, and acknowledgement.

**Response JSON (200 OK):**
```json
[
  {
    "id": 1,
    "alert_id": 1,
    "tier": 1,
    "notified_caregiver_id": 1,
    "notification_channel": "all",
    "provider": "development_mock",
    "recipient_address": "+919876543220",
    "status": "dispatched_mock",
    "message_payload": "Alert: manual_sos | Severity: critical | Location: Lat: 12.9716, Lon: 77.5946",
    "error_message": null,
    "retry_count": 0,
    "sent_at": "2026-11-23T16:00:01Z"
  },
  {
    "id": 2,
    "alert_id": 1,
    "tier": 2,
    "notified_caregiver_id": 2,
    "notification_channel": "all",
    "provider": "development_mock",
    "recipient_address": "+919999111122",
    "status": "dispatched_mock",
    "message_payload": "Alert: manual_sos | Severity: critical | Location: Lat: 12.9716, Lon: 77.5946",
    "error_message": null,
    "retry_count": 0,
    "sent_at": "2026-11-23T16:02:01Z"
  },
  {
    "id": 3,
    "alert_id": 1,
    "tier": 2,
    "notified_caregiver_id": 2,
    "notification_channel": "system",
    "provider": "system_auth",
    "recipient_address": "nurse.priya@pulseguardian.ai",
    "status": "acknowledged",
    "message_payload": "Acknowledged by Nurse Priya: Patient safe, attending now.",
    "error_message": null,
    "retry_count": 0,
    "sent_at": "2026-11-23T16:02:30Z"
  }
]
```


---

## 5. AI Engine – Personal Health Digital Twin & Anomaly Detection

PulseGuardian AI's AI Engine implements an adaptive Personal Health Digital Twin baseline learner, multi-tier statistical Z-score anomaly detector, circadian day/night profile analyzer, multi-signal cardiorespiratory stress correlator, and Scikit-learn multivariate Isolation Forest outlier detector.

> [!IMPORTANT]
> **Medical Disclaimer**: PulseGuardian AI provides health tracking and anomaly detection for observational purposes only. It is not a medical diagnosis or disease prediction tool. Please consult a qualified healthcare professional.

---

### 5.1 On-Demand & Telemetry AI Anomaly Analysis
* **Endpoint**: `POST /api/v1/ai/analyze`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Evaluates vital signs against the patient's personalized Digital Twin baseline, circadian time-of-day expectations, acute clinical safety redlines, multi-signal patterns, and Scikit-learn Isolation Forest. When `vitals` are omitted, automatically fetches the patient's latest ingested wearable telemetry.

**Request JSON (Evaluating Acute Vitals Payload):**
```json
{
  "patient_id": 1,
  "vitals": {
    "heart_rate": 118.0,
    "spo2": 91.0,
    "temperature": 37.9,
    "temperature_unit": "C",
    "step_count": 0,
    "activity_type": "resting",
    "fall_detected": false
  }
}
```

**Response JSON (200 OK - Multi-Signal Anomaly Flagged):**
```json
{
  "patient_id": 1,
  "analysis_timestamp": "2026-11-23T16:30:00Z",
  "overall_status": "anomalous",
  "severity": "high",
  "confidence_score": 0.94,
  "data_quality_status": "good",
  "personal_baseline": {
    "resting_hr": 70.5,
    "hr_min_normal": 58.0,
    "hr_max_normal": 83.0,
    "spo2": 98.0,
    "spo2_min_normal": 95.0,
    "temperature": 36.6,
    "cold_start": false,
    "samples_count": 48
  },
  "current_readings": {
    "heart_rate": 118.0,
    "spo2": 91.0,
    "temperature": 37.9,
    "temperature_unit": "C",
    "step_count": 0,
    "activity_type": "resting",
    "fall_detected": false,
    "battery_percentage": 85.0,
    "recorded_at": "2026-11-23T16:30:00Z"
  },
  "detected_anomalies": [
    {
      "parameter": "heart_rate",
      "current_value": 118.0,
      "baseline_value": 70.5,
      "deviation": 3.82,
      "unit": "Z-score (BPM)",
      "severity": "high",
      "explanation": "Heart rate 118.0 BPM is +3.8 standard deviations above personal resting baseline (70.5 ± 5.0 BPM)."
    },
    {
      "parameter": "spo2",
      "current_value": 91.0,
      "baseline_value": 98.0,
      "deviation": 7.0,
      "unit": "%",
      "severity": "moderate",
      "explanation": "Blood oxygen 91.0% dropped below personal normal threshold (95.0%)."
    },
    {
      "parameter": "temperature",
      "current_value": 37.9,
      "baseline_value": 36.6,
      "deviation": 1.3,
      "unit": "°C",
      "severity": "moderate",
      "explanation": "Mild hyperthermia: Temperature 37.9°C exceeds personal normal envelope (37.5°C)."
    },
    {
      "parameter": "multi_signal",
      "current_value": 118.0,
      "baseline_value": 70.5,
      "deviation": null,
      "unit": "HR+SpO2",
      "severity": "high",
      "explanation": "Cardiorespiratory stress pattern: Concurrent low oxygen saturation and compensatory resting tachycardia."
    }
  ],
  "isolation_forest_triggered": true,
  "isolation_forest_score": 0.184,
  "explanation": "Resting heart rate (+3.8σ) exceeds personal baseline. | SpO2 91.0% dropped below personal baseline threshold. | Multi-signal cardiorespiratory stress pattern detected. | Multivariate Isolation Forest identified an outlier physiological cluster (anomaly score: 0.184).",
  "recommendations": [
    "Sit down in a comfortable position and rest for 5 minutes. Re-check heart rate once relaxed.",
    "Verify the pulse oximeter sensor has snug contact with your skin. Take deep, slow breaths.",
    "Stay hydrated and rest in a well-ventilated room. Re-measure temperature periodically.",
    "Alert your primary caregiver or healthcare provider if acute symptoms persist or worsen."
  ],
  "medical_disclaimer": "PulseGuardian AI provides health tracking and anomaly detection for observational purposes only. It is not a medical diagnosis or disease prediction tool. Please consult a qualified healthcare professional."
}
```

---

### 5.2 Real-Time AI Health Status Overview
* **Endpoint**: `GET /api/v1/ai/health-status`
* **Query Parameters**: `patient_id` (Optional, required for Caregivers/Admins)
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Returns consolidated real-time health overview including latest vital readings, baseline comparisons, active anomalies count over the past 24 hours, and sensor freshness.

**Response JSON (200 OK):**
```json
{
  "patient_id": 1,
  "current_status": "normal",
  "last_reading_at": "2026-11-23T16:28:10Z",
  "latest_vitals": {
    "heart_rate": 72.0,
    "spo2": 98.5,
    "temperature": 36.65,
    "temperature_unit": "C",
    "step_count": 340,
    "activity_type": "walking",
    "fall_detected": false,
    "is_anomalous": false,
    "anomaly_reason": null
  },
  "baseline_summary": {
    "resting_hr": 70.5,
    "hr_min_normal": 58.0,
    "hr_max_normal": 83.0,
    "spo2": 98.0,
    "spo2_min_normal": 95.0,
    "temperature": 36.6,
    "cold_start": false,
    "samples_count": 48
  },
  "active_anomalies_count": 0,
  "cold_start": false,
  "data_quality_status": "good",
  "disclaimer": "PulseGuardian AI provides health tracking and anomaly detection for observational purposes only. It is not a medical diagnosis or disease prediction tool. Please consult a qualified healthcare professional."
}
```

---

### 5.3 Historical Anomaly Records
* **Endpoint**: `GET /api/v1/ai/anomalies`
* **Query Parameters**:
  * `patient_id` (Optional, required for Caregivers/Admins)
  * `limit` (Default: 20, Max: 100)
  * `severity` (Optional: `'critical'`, `'high'`, `'moderate'`, `'low'`)
  * `start_time` (Optional UTC ISO timestamp)
  * `end_time` (Optional UTC ISO timestamp)
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Lists historical anomalous telemetry records flagged by the AI engine with severity ratings, explanations, and corresponding sensor readings.

**Response JSON (200 OK):**
```json
{
  "patient_id": 1,
  "total_anomalies": 1,
  "anomalies": [
    {
      "telemetry_id": 142,
      "patient_id": 1,
      "recorded_at": "2026-11-23T15:10:00Z",
      "vitals": {
        "heart_rate": 142.0,
        "spo2": 88.0,
        "temperature": 38.9,
        "temperature_unit": "C",
        "step_count": 0,
        "activity_type": "resting",
        "fall_detected": false
      },
      "anomaly_score": 0.9,
      "anomaly_reason": "Critical hypoxemia and resting tachycardia",
      "severity": "critical"
    }
  ]
}
```

---

### 5.4 Digital Twin Model & Circadian Patterns
* **Endpoint**: `GET /api/v1/ai/digital-twin`
* **Query Parameters**: `patient_id` (Optional, required for Caregivers/Admins)
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Returns the comprehensive Personal Health Digital Twin model, including cold-start indicators, baseline parameters, and circadian profile breakdowns (day vs night resting heart rates and hourly profiles).

**Response JSON (200 OK):**
```json
{
  "patient_id": 1,
  "status": "active",
  "cold_start": false,
  "samples_count": 48,
  "min_samples_required": 20,
  "baseline_resting_hr": 70.5,
  "hr_min_normal": 58.0,
  "hr_max_normal": 83.0,
  "hr_std_dev": 5.0,
  "baseline_spo2": 98.0,
  "spo2_min_normal": 95.0,
  "baseline_temperature": 36.6,
  "temp_min_normal": 36.1,
  "temp_max_normal": 37.2,
  "circadian_profile": {
    "status": "active",
    "samples_analyzed": 48,
    "day_hr_average": 72.4,
    "night_hr_average": 64.2,
    "resting_hr_average": 68.1,
    "active_hr_average": 88.5,
    "hourly_hr_profile": {
      "0": 63.5,
      "1": 62.8,
      "6": 66.0,
      "12": 74.2,
      "18": 71.8,
      "22": 67.4
    }
  },
  "last_calculated_at": "2026-11-23T16:20:00Z"
}
```

---

### 5.5 Digital Twin Baseline Parameters & Recalculation
* **Endpoint**: `GET /api/v1/ai/digital-twin/baseline`
* **Query Parameters**:
  * `patient_id` (Optional, required for Caregivers/Admins)
  * `recalculate` (Default: `false`. When `true`, triggers re-learning of baseline from recent telemetry)
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Retrieves or recalculates patient baseline parameters.

**Response JSON (Cold Start Mode - 200 OK):**
```json
{
  "patient_id": 2,
  "status": "cold_start",
  "cold_start": true,
  "samples_count": 6,
  "min_samples_required": 20,
  "baseline_resting_hr": 72.0,
  "hr_min_normal": 55.0,
  "hr_max_normal": 100.0,
  "hr_std_dev": 8.0,
  "baseline_spo2": 98.0,
  "spo2_min_normal": 95.0,
  "baseline_temperature": 36.8,
  "temp_min_normal": 36.1,
  "temp_max_normal": 37.2,
  "circadian_profile": {
    "status": "cold_start",
    "samples_count": 6,
    "min_required": 20,
    "message": "Digital Twin is in cold start mode. Collected 6/20 readings."
  },
  "last_calculated_at": "2026-11-23T16:25:00Z"
}
```

---

### 5.6 Health Timeline (Vitals vs Personal Baseline Envelope)
* **Endpoint**: `GET /api/v1/ai/health-timeline`
* **Query Parameters**:
  * `patient_id` (Optional, required for Caregivers/Admins)
  * `hours` (Default: 24, Range: 1 to 168)
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Returns chronological telemetry mapped with personal upper and lower baseline envelope bounds. Tailored for frontend charts and visual drift inspection.

**Response JSON (200 OK):**
```json
{
  "patient_id": 1,
  "time_range_hours": 24,
  "total_points": 2,
  "timeline": [
    {
      "timestamp": "2026-11-23T14:00:00Z",
      "heart_rate": 72.0,
      "spo2": 98.0,
      "temperature": 36.6,
      "step_count": 10,
      "activity_type": "resting",
      "is_anomalous": false,
      "anomaly_reason": null,
      "baseline_resting_hr": 70.5,
      "hr_lower_bound": 58.0,
      "hr_upper_bound": 83.0,
      "baseline_spo2": 98.0,
      "spo2_lower_bound": 95.0
    },
    {
      "timestamp": "2026-11-23T15:00:00Z",
      "heart_rate": 118.0,
      "spo2": 91.0,
      "temperature": 37.9,
      "step_count": 0,
      "activity_type": "resting",
      "is_anomalous": true,
      "anomaly_reason": "Cardiorespiratory stress pattern: low SpO2 and resting tachycardia",
      "baseline_resting_hr": 70.5,
      "hr_lower_bound": 58.0,
      "hr_upper_bound": 83.0,
      "baseline_spo2": 98.0,
      "spo2_lower_bound": 95.0
    }
  ],
  "cold_start": false
}
```


---

## 6. AI Engine – Health Drift Intelligence

PulseGuardian AI's Health Drift Intelligence module identifies subtle, gradual shifts in a patient's baseline physiological and lifestyle patterns over configurable timeframes (3-day, 7-day, 30-day windows). Utilizing Exponentially Weighted Moving Averages (EWMA), simple moving averages, and linear regression slopes, the engine distinguishes persistent physiological drift from transient fluctuations.

> [!IMPORTANT]
> **Medical Disclaimer**: PulseGuardian AI provides health tracking and anomaly detection for observational purposes only. It is not a medical diagnosis or disease prediction tool. Please consult a qualified healthcare professional.

---

### 6.1 Overall Health Drift Summary
* **Endpoint**: `GET /api/v1/ai/health-drift/summary`
* **Query Parameters**:
  * `patient_id` (Optional, required for Caregivers/Admins)
  * `window_days` (Default: 7, Range: 3 to 90 days)
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Returns consolidated multi-metric drift analysis across resting heart rate, SpO2, body temperature, sleep duration, and daily step count. Includes comparative 3-day, 7-day, and 30-day trend summaries.

**Response JSON (200 OK):**
```json
{
  "patient_id": 1,
  "analysis_timestamp": "2026-11-24T08:30:00Z",
  "window_days": 7,
  "period_start": "2026-11-17T08:30:00Z",
  "period_end": "2026-11-24T08:30:00Z",
  "overall_drift_status": "moderate_drift",
  "overall_confidence": "high",
  "data_completeness_percentage": 100.0,
  "metrics_summary": {
    "heart_rate": {
      "metric_name": "heart_rate",
      "display_name": "Resting Heart Rate",
      "unit": "BPM",
      "baseline_value": 72.0,
      "current_value": 81.4,
      "drift_delta": 9.4,
      "drift_percentage": 13.1,
      "trend_direction": "upward",
      "slope_per_day": 1.714,
      "persistence_score": 1.0,
      "is_persistent": true,
      "classification": "persistent_drift",
      "significance": "moderate_drift",
      "data_sufficiency": "sufficient",
      "recorded_days_count": 7,
      "total_window_days": 7,
      "explanation": "Resting Heart Rate exhibits a gradual upward drift over the observed window: current EWMA is 81.4 BPM (+13.1% from baseline 72.0 BPM) with a rate of +1.71 BPM/day. Consistency was maintained across 7 of 7 days, indicating persistent moderate drift.",
      "data_points": [
        { "date": "2026-11-18", "value": 72.0, "moving_avg": 72.0, "baseline": 72.0 },
        { "date": "2026-11-19", "value": 74.0, "moving_avg": 73.3, "baseline": 72.0 },
        { "date": "2026-11-20", "value": 76.0, "moving_avg": 75.1, "baseline": 72.0 },
        { "date": "2026-11-21", "value": 78.0, "moving_avg": 77.0, "baseline": 72.0 },
        { "date": "2026-11-22", "value": 80.0, "moving_avg": 79.0, "baseline": 72.0 },
        { "date": "2026-11-23", "value": 82.0, "moving_avg": 81.0, "baseline": 72.0 },
        { "date": "2026-11-24", "value": 84.0, "moving_avg": 83.0, "baseline": 72.0 }
      ]
    },
    "spo2": {
      "metric_name": "spo2",
      "display_name": "Blood Oxygen (SpO2)",
      "unit": "%",
      "baseline_value": 98.0,
      "current_value": 98.0,
      "drift_delta": 0.0,
      "drift_percentage": 0.0,
      "trend_direction": "stable",
      "slope_per_day": 0.0,
      "persistence_score": 0.0,
      "is_persistent": false,
      "classification": "stable",
      "significance": "stable",
      "data_sufficiency": "sufficient",
      "recorded_days_count": 7,
      "total_window_days": 7,
      "explanation": "Blood Oxygen (SpO2) is stable over the observed period (current 98.0 % vs baseline 98.0 %, deviation 0.0%).",
      "data_points": []
    }
  },
  "multi_window_trends": {
    "3d": {
      "heart_rate": { "drift_delta": 11.0, "drift_percentage": 15.3, "trend_direction": "upward" },
      "spo2": { "drift_delta": 0.0, "drift_percentage": 0.0, "trend_direction": "stable" },
      "temperature": { "drift_delta": 0.0, "drift_percentage": 0.0, "trend_direction": "stable" }
    },
    "7d": {
      "heart_rate": { "drift_delta": 11.0, "drift_percentage": 15.3, "trend_direction": "upward" },
      "spo2": { "drift_delta": 0.0, "drift_percentage": 0.0, "trend_direction": "stable" },
      "temperature": { "drift_delta": 0.0, "drift_percentage": 0.0, "trend_direction": "stable" }
    },
    "30d": {
      "heart_rate": { "drift_delta": 11.0, "drift_percentage": 15.3, "trend_direction": "upward" },
      "spo2": { "drift_delta": 0.0, "drift_percentage": 0.0, "trend_direction": "stable" },
      "temperature": { "drift_delta": 0.0, "drift_percentage": 0.0, "trend_direction": "stable" }
    }
  },
  "key_findings": [
    "Resting Heart Rate: Persistent upward drift (+13.1% vs baseline)."
  ],
  "recommendations": [
    "Consider sharing this trend summary with your assigned caregiver or healthcare provider during your next routine consultation.",
    "Resting heart rate has trended higher across multiple days. Ensure adequate hydration, rest, and minimize stimulants."
  ],
  "medical_disclaimer": "PulseGuardian AI provides health tracking and anomaly detection for observational purposes only. It is not a medical diagnosis or disease prediction tool. Please consult a qualified healthcare professional."
}
```

---

### 6.2 Individual Metric Drift Breakdown
* **Endpoint**: `GET /api/v1/ai/health-drift/metric/{metric_name}`
* **Path Parameter**: `metric_name` (`heart_rate`, `spo2`, `temperature`, `sleep_duration`, `daily_steps`)
* **Query Parameters**:
  * `patient_id` (Optional, required for Caregivers/Admins)
  * `window_days` (Default: 7, Range: 3 to 90 days)
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Returns granular mathematical trajectory, linear regression rate of change per day, consistency ratio, persistence classification, and daily chart coordinates for the chosen metric.

**Response JSON (200 OK):**
```json
{
  "metric_name": "spo2",
  "display_name": "Blood Oxygen (SpO2)",
  "unit": "%",
  "baseline_value": 98.0,
  "current_value": 95.3,
  "drift_delta": -2.7,
  "drift_percentage": -2.8,
  "trend_direction": "downward",
  "slope_per_day": -0.5,
  "persistence_score": 1.0,
  "is_persistent": true,
  "classification": "persistent_drift",
  "significance": "moderate_drift",
  "data_sufficiency": "sufficient",
  "recorded_days_count": 7,
  "total_window_days": 7,
  "explanation": "Blood Oxygen (SpO2) exhibits a gradual downward drift over the observed window: current EWMA is 95.3 % (-2.8% from baseline 98.0 %) with a rate of -0.50 %/day. Consistency was maintained across 7 of 7 days, indicating persistent moderate drift.",
  "data_points": [
    { "date": "2026-11-18", "value": 98.0, "moving_avg": 98.0, "baseline": 98.0 },
    { "date": "2026-11-19", "value": 97.5, "moving_avg": 97.7, "baseline": 98.0 },
    { "date": "2026-11-20", "value": 97.0, "moving_avg": 97.2, "baseline": 98.0 },
    { "date": "2026-11-21", "value": 96.5, "moving_avg": 96.7, "baseline": 98.0 },
    { "date": "2026-11-22", "value": 96.0, "moving_avg": 96.2, "baseline": 98.0 },
    { "date": "2026-11-23", "value": 95.5, "moving_avg": 95.7, "baseline": 98.0 },
    { "date": "2026-11-24", "value": 95.0, "moving_avg": 95.3, "baseline": 98.0 }
  ]
}
```

---

### 6.3 Historical Drift Timeline Audit
* **Endpoint**: `GET /api/v1/ai/health-drift/timeline`
* **Query Parameters**:
  * `patient_id` (Optional, required for Caregivers/Admins)
  * `metric_name` (Optional: e.g. `'heart_rate'`)
  * `limit` (Default: 50, Range: 1 to 100)
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Lists historical persistent drift records logged to the database audit trail over time.

**Response JSON (200 OK):**
```json
{
  "patient_id": 1,
  "total_records": 1,
  "records": [
    {
      "id": 1,
      "patient_id": 1,
      "period_start": "2026-11-17T08:30:00Z",
      "period_end": "2026-11-24T08:30:00Z",
      "drift_parameter": "heart_rate",
      "baseline_value": 72.0,
      "current_period_value": 81.4,
      "drift_delta": 9.4,
      "drift_percentage": 13.1,
      "significance": "moderate_drift",
      "ai_recommendation": "Resting Heart Rate exhibits a gradual upward drift over the observed window: current EWMA is 81.4 BPM (+13.1% from baseline 72.0 BPM) with a rate of +1.71 BPM/day.",
      "created_at": "2026-11-24T08:30:05Z"
    }
  ]
}
```

---

### 6.4 Configurable Time-Window Analysis (On-Demand)
* **Endpoint**: `POST /api/v1/ai/health-drift/analyze`
* **Access**: Patient (Self) / Assigned Caregiver / Admin
* **Description**: Evaluates health drift for custom timeframes (e.g., 14, 30, or 60 days) and arbitrary metric subsets.

**Request JSON:**
```json
{
  "patient_id": 1,
  "window_days": 14,
  "metrics": [
    "heart_rate",
    "spo2",
    "sleep_duration"
  ],
  "persist": true
}
```

**Response JSON (200 OK):**
Returns standard `OverallHealthDriftSummary` calculated over the requested 14-day window.


---

## 7. Multilingual Voice Assistance Foundation (Phase 7 – Stage 2A)

The Voice Assistance Foundation establishes privacy-conscious, multilingual processing across 7 regional languages (Kannada, English, Hindi, Malayalam, Tamil, Telugu, and Urdu) using pluggable provider adapters and affirmative user consent enforcement.

> [!IMPORTANT]
> **Safety Notice**: Manual wearable push-button SOS and accelerometer fall detection remain 100% independent of voice recognition, translation, network availability, and AI processing. Voice processing operates in ephemeral memory; raw audio files are not stored on persistent storage without explicit user authorization.

---

### 7.1 Supported Languages Metadata
* **Endpoint**: `GET /api/v1/voice/languages`
* **Access**: Authenticated Patient / Caregiver / Admin
* **Description**: Returns metadata for all 7 supported South Asian languages, native names, scripts, text directions, adapter capabilities, active mock mode status, and privacy consent notices.

**Response JSON (200 OK):**
```json
{
  "languages": [
    {
      "code": "kn",
      "name": "Kannada",
      "native_name": "ಕನ್ನಡ",
      "script": "Kannada",
      "direction": "ltr",
      "stt_supported": true,
      "translation_supported": true,
      "tts_supported": true,
      "privacy_consent_required": true
    },
    {
      "code": "en",
      "name": "English",
      "native_name": "English",
      "script": "Latin",
      "direction": "ltr",
      "stt_supported": true,
      "translation_supported": true,
      "tts_supported": true,
      "privacy_consent_required": true
    },
    {
      "code": "hi",
      "name": "Hindi",
      "native_name": "हिन्दी",
      "script": "Devanagari",
      "direction": "ltr",
      "stt_supported": true,
      "translation_supported": true,
      "tts_supported": true,
      "privacy_consent_required": true
    },
    {
      "code": "ml",
      "name": "Malayalam",
      "native_name": "മലയാളം",
      "script": "Malayalam",
      "direction": "ltr",
      "stt_supported": true,
      "translation_supported": true,
      "tts_supported": true,
      "privacy_consent_required": true
    },
    {
      "code": "ta",
      "name": "Tamil",
      "native_name": "தமிழ்",
      "script": "Tamil",
      "direction": "ltr",
      "stt_supported": true,
      "translation_supported": true,
      "tts_supported": true,
      "privacy_consent_required": true
    },
    {
      "code": "te",
      "name": "Telugu",
      "native_name": "తెలుగు",
      "script": "Telugu",
      "direction": "ltr",
      "stt_supported": true,
      "translation_supported": true,
      "tts_supported": true,
      "privacy_consent_required": true
    },
    {
      "code": "ur",
      "name": "Urdu",
      "native_name": "اردو",
      "script": "Perso-Arabic",
      "direction": "rtl",
      "stt_supported": true,
      "translation_supported": true,
      "tts_supported": true,
      "privacy_consent_required": true
    }
  ],
  "total_supported": 7,
  "default_language": "en",
  "mock_mode_active": true,
  "privacy_notice": "PulseGuardian AI handles voice interactions in ephemeral memory. Explicit patient consent is mandatory before processing audio data. Raw audio files are not persisted to persistent storage without affirmative authorization."
}
```

---

### 7.2 Voice Processing Consent Management
* **Endpoint**: `GET /api/v1/voice/consent` & `POST /api/v1/voice/consent`
* **Access**: Authenticated User (Self)
* **Description**: Checks or updates persistent affirmative authorization for voice interactions and optional audio retention preferences.

**Update Request JSON:**
```json
{
  "consent_granted": true,
  "audio_retention_permitted": false
}
```

**Response JSON (200 OK):**
```json
{
  "user_id": 1,
  "consent_granted": true,
  "audio_retention_permitted": false,
  "privacy_policy_accepted": true,
  "updated_at": "2026-11-24T09:00:00Z"
}
```

---

### 7.3 Speech-to-Text Transcription (Phase 7 – Stage 2B.1: Real & Mock STT)
* **Endpoint**: `POST /api/v1/voice/transcribe`
* **Access**: Authenticated User (Patient, Caregiver, or Admin)
* **Description**: Transcribes base64-encoded audio payloads into text using the configured provider (`local_whisper`, `hosted_whisper`, or `mock_development`). All processing is performed strictly in ephemeral memory (`io.BytesIO`) without persisting raw audio to disk or database. Enforces strict input validation, maximum payload size limits, affirmative consent checks, and calibrated uncertainty handling.

#### Audio Input Validation & Safety Constraints
* **Supported MIME Types**: `audio/wav`, `audio/x-wav`, `audio/mpeg`, `audio/mp3`, `audio/ogg`, `audio/webm`, `audio/x-m4a`, `audio/flac` (returns `400 Bad Request` if unsupported).
* **Maximum Audio Size**: 10 MB (`10,485,760` bytes) decoded audio buffer (returns `413 Request Entity Too Large` if exceeded).
* **Maximum Audio Duration (Pre-flight Validation)**: Configurable via `VOICE_MAX_AUDIO_DURATION_SECONDS` (default 60.0 seconds). Duration is inspected strictly in ephemeral memory from stream headers (WAV, MP3, OGG, FLAC, M4A, WebM). Files exceeding the duration limit are rejected with `HTTP 413 Request Entity Too Large`. Corrupted, unparseable, or missing duration metadata is rejected with `HTTP 400 Bad Request`. Rejection occurs before calling STT adapters.
* **Base64 Encoding**: Non-empty, strictly validated base64 payload (returns `400 Bad Request` if invalid or empty).
* **Consent Requirement**: Explicit `consent_confirmed: true` in request OR active user consent preference in database (returns `403 Forbidden` if missing).
* **Supported Languages for STT & Detection**: Kannada (`kn`), English (`en`), Hindi (`hi`), Malayalam (`ml`), Tamil (`ta`), Telugu (`te`), Urdu (`ur`).
* **Confidence & Uncertainty Calibration**: Real Whisper models do not output calibrated sentence confidence. In adherence to safety guidelines, `confidence` is returned as `null` (rather than invented scores), and `uncertain_speech` is flagged as `true` if language probability is low, speech is silence/noise, or language is outside the 7 supported languages (`detected_language: "unsupported"`).

**Request JSON:**
```json
{
  "audio_base64": "UklGRi4AAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
  "audio_format": "audio/wav",
  "language_hint": "kn",
  "consent_confirmed": true
}
```

**Response JSON (Real Provider - Hosted/Local Whisper - 200 OK):**
```json
{
  "transcript": "ನನ್ನ ಎದೆ ಬಡಿತ ವೇಗವಾಗಿದೆ",
  "detected_language": "kn",
  "confidence": null,
  "provider": "hosted_whisper",
  "is_mock": false,
  "disclaimer": "REAL STT: Speech recognized using automated acoustic AI models. Non-emergency assistive interaction only. Automated transcripts must not be relied upon for clinical diagnosis or life-critical emergency dispatch.",
  "uncertain_speech": false
}
```

**Response JSON (Uncertain / Unsupported Language - 200 OK):**
```json
{
  "transcript": "Bonjour, comment allez-vous",
  "detected_language": "unsupported",
  "confidence": null,
  "provider": "hosted_whisper",
  "is_mock": false,
  "disclaimer": "REAL STT: Speech recognized using automated acoustic AI models. Non-emergency assistive interaction only. Automated transcripts must not be relied upon for clinical diagnosis or life-critical emergency dispatch.",
  "uncertain_speech": true
}
```

**Response JSON (Mock Development Adapter - 200 OK):**
```json
{
  "transcript": "[Simulated Audio Transcription (KN)]: Mock audio payload received (44 bytes, type: audio/wav). No acoustic speech model was executed.",
  "detected_language": "kn",
  "confidence": 0.85,
  "provider": "mock_development",
  "is_mock": true,
  "disclaimer": "MOCK TRANSCRIPTION: Simulated placeholder. No actual speech recognition or audio ML was performed on the input payload.",
  "uncertain_speech": false
}
```

---

### 7.4 Multilingual Translation (Phase 7 – Stage 2B.2: Real & Mock Translation)
* **Endpoint**: `POST /api/v1/voice/translate`
* **Access**: Authenticated User (Patient, Caregiver, or Admin)
* **Description**: Translates health text between the 7 supported regional languages (`kn`, `en`, `hi`, `ml`, `ta`, `te`, `ur`) using the configured provider (`hosted_translation`, `local_indictrans`, or `mock_development`). All processing is performed strictly in ephemeral memory. Ephemeral audit logs record only character counts and language codes; raw translation text is never stored or logged.

#### Translation Constraints & Safety Rules
* **Supported Languages**: Kannada (`kn`), English (`en`), Hindi (`hi`), Malayalam (`ml`), Tamil (`ta`), Telugu (`te`), Urdu (`ur`).
* **Maximum Text Length**: 5,000 characters (returns `400 Bad Request` if empty, whitespace-only, or exceeding 5,000 chars).
* **Script Detection**: Best-effort Unicode script analysis when `source_language` is omitted (`None`). Latin script is flagged as uncertain (not automatically assumed English); Devanagari is flagged as uncertain (not automatically assumed Hindi); Perso-Arabic is flagged as uncertain (not automatically assumed Urdu). Ambiguous text sets `uncertain_translation: true`.
* **Confidence Representation**: NMT models do not produce calibrated posterior sentence probabilities. `confidence` is returned strictly as `null`, avoiding artificial certainty.
* **Emergency Decoupling**: Text translation never triggers emergency SOS alerts, fall detection, or caregiver escalation ladders.
* **Error Handling**:
  - Missing API credentials or uninstalled local models: `503 Service Unavailable`
  - External provider timeout: `504 Gateway Timeout`
  - External provider network connection failure: `502 Bad Gateway`
  - Invalid input, empty text, or unsupported language code: `400 Bad Request`
  - Missing affirmative consent: `403 Forbidden`

**Request JSON (Explicit Source Language):**
```json
{
  "text": "My blood pressure is high and I feel dizzy.",
  "source_language": "en",
  "target_language": "kn",
  "consent_confirmed": true
}
```

**Response JSON (Real Provider - Hosted Translation - 200 OK):**
```json
{
  "original_text": "My blood pressure is high and I feel dizzy.",
  "translated_text": "ನನ್ನ ರಕ್ತದೊತ್ತಡ ಹೆಚ್ಚಾಗಿದೆ ಮತ್ತು ನನಗೆ ತಲೆತಿರುಗುವಿಕೆ ಅನಿಸುತ್ತಿದೆ.",
  "source_language": "en",
  "target_language": "kn",
  "confidence": null,
  "provider": "hosted_translation",
  "is_mock": false,
  "disclaimer": "REAL TRANSLATION: Translated using automated multilingual neural machine translation models. Non-emergency assistive interaction only. Automated translations must not be treated as verified medical instructions or clinical advice.",
  "uncertain_translation": false
}
```

**Response JSON (Auto-Detected Ambiguous Source Script - 200 OK):**
```json
{
  "original_text": "Severe chest pressure",
  "translated_text": "ತೀವ್ರ ಎದೆ ಒತ್ತಡ",
  "source_language": "en",
  "target_language": "kn",
  "confidence": null,
  "provider": "hosted_translation",
  "is_mock": false,
  "disclaimer": "REAL TRANSLATION: Translated using automated multilingual neural machine translation models. Non-emergency assistive interaction only. Automated translations must not be treated as verified medical instructions or clinical advice.",
  "uncertain_translation": true
}
```

**Response JSON (Development Mock Adapter - 200 OK):**
```json
{
  "original_text": "My blood pressure is high",
  "translated_text": "[Simulated KN Translation]: My blood pressure is high",
  "source_language": "en",
  "target_language": "kn",
  "confidence": null,
  "provider": "mock_development",
  "is_mock": true,
  "disclaimer": "MOCK TRANSLATION: Simulated placeholder for interface testing. Does not represent a clinically or linguistically verified translation.",
  "uncertain_translation": false
}
```

---

### 7.5 Speech Synthesis / Text-to-Speech (Phase 7 – Stage 2B.3: Real & Mock TTS)
* **Endpoint**: `POST /api/v1/voice/synthesize`
* **Access**: Authenticated User (Bearer JWT)
* **Description**: Synthesizes assistive patient health communications into acoustic speech for all 7 supported languages (`kn`, `en`, `hi`, `ml`, `ta`, `te`, `ur`). Dispatches to configured adapter: Hosted OpenAI Audio Speech API (`VOICE_TTS_PROVIDER=hosted_tts`), Local offline engine (`VOICE_TTS_PROVIDER=local_tts`), or Development Mock (`VOICE_TTS_PROVIDER=mock_development`).
* **Audio Processing & Safety**:
  - Enforces affirmative patient authorization (`consent_confirmed: true` or active database preference; returns `HTTP 403`).
  - Text length enforced up to `VOICE_MAX_TTS_CHARS = 2000` characters (returns `HTTP 400`).
  - Returns safe base64-encoded audio payload in memory; raw audio is never stored on disk or in persistent databases.
  - Ephemeral audit logs capture metadata only (character counts, provider, language code, timestamp); patient health text and audio bytes are never logged.

**Supported Audio Formats (`audio_format`):**
- `audio/mp3` (default), `audio/mpeg`
- `audio/wav`, `audio/x-wav`
- `audio/ogg`, `audio/opus`
- `audio/aac`
- `audio/flac`

**Voice Mapping (`voice_gender`):**
- `neutral`: Balanced neutral profile (`alloy`)
- `female`: Clear female voice profile (`nova`)
- `male`: Deep male voice profile (`onyx`)
- Direct voice overrides: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

**Request JSON (Real or Mock):**
```json
{
  "text": "ನಿಮ್ಮ ರಕ್ತದೊತ್ತಡ ಸಾಮಾನ್ಯವಾಗಿದೆ.",
  "language_code": "kn",
  "voice_gender": "female",
  "audio_format": "audio/mp3",
  "consent_confirmed": true
}
```

**Real Response JSON (`VOICE_TTS_PROVIDER=hosted_tts` – 200 OK):**
```json
{
  "language_code": "kn",
  "audio_payload": "//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAAYAA...",
  "audio_format": "audio/mp3",
  "is_mock": false,
  "is_playable": true,
  "provider": "hosted_tts",
  "disclaimer": "REAL TTS: Acoustic speech synthesized using automated text-to-speech models. Non-emergency assistive interaction only. Automated speech must not be treated as clinical instructions or medical diagnoses."
}
```

**Mock Response JSON (`VOICE_TTS_PROVIDER=mock_development` – 200 OK):**
```json
{
  "language_code": "kn",
  "audio_payload": "TU9DS19UVFNfQVVESU9fQlVGRkVSX0tOXy4uLg==",
  "audio_format": "audio/mock-synthesized",
  "is_mock": true,
  "is_playable": false,
  "provider": "mock_development",
  "disclaimer": "MOCK TTS: Simulated audio payload placeholder. No playable acoustic speech was generated."
}
```

**Status & Error Codes:**
* `200 OK`: Synthesis succeeded; returns base64 audio payload and metadata.
* `400 Bad Request`: Empty text, text exceeding maximum character limit (2,000 chars), unsupported language code, unsupported audio format, or invalid voice gender.
* `401 Unauthorized`: Missing, expired, or invalid JWT authentication token.
* `403 Forbidden`: User consent not granted or not confirmed.
* `502 Bad Gateway`: Network or provider communication failure when connecting to hosted TTS service.
* `503 Service Unavailable`: TTS API key not configured or local synthesis engine dependencies missing.
* `504 Gateway Timeout`: Hosted TTS synthesis request timed out.

---

### 7.6 Patient-Caregiver Multilingual Messaging
* **Endpoint Base**: `/api/v1/voice`
* **Access**: Authenticated Patient or Caregiver (Bearer JWT)
* **Authorization & Privacy Rules**:
  - Strict relationship validation: A patient can only communicate with assigned caregivers; a caregiver only with assigned patients.
  - Ownership enforcement: Non-participants cannot view, translate, reply to, or mark messages as read (`HTTP 403`).
  - Separation of representations: Original text and translated text are permanently preserved as distinct attributes; translations never overwrite original clinical or patient inputs.
  - Affirmative consent required for AI processing; metadata-only audit logging ensures no private messages or credentials leak into application logs.

#### 7.6.1 List Conversations
* **Endpoint**: `GET /api/v1/voice/conversations`
* **Description**: Returns all conversation partner summaries with unread message counts, partner profiles, and last message previews.

#### 7.6.2 Get Conversation Message History
* **Endpoint**: `GET /api/v1/voice/conversations/{partner_id}?limit=50&offset=0&since=ISO_TIMESTAMP`
* **Description**: Chronological message thread with full translation metadata, uncertainty flags, and delivery statuses.

#### 7.6.3 Send Multilingual Message
* **Endpoint**: `POST /api/v1/voice/messages`
* **Request JSON:**
```json
{
  "recipient_id": 2,
  "text": "ನನಗೆ ತಲೆನೋವು ಹೆಚ್ಚಾಗಿದೆ",
  "source_language": "kn",
  "target_language": "en",
  "auto_translate": true,
  "consent_confirmed": true,
  "reply_to_id": null
}
```
* **Response JSON (201 Created):**
```json
{
  "id": 42,
  "sender_id": 1,
  "recipient_id": 2,
  "source_language": "kn",
  "target_language": "en",
  "original_text": "ನನಗೆ ತಲೆನೋವು ಹೆಚ್ಚಾಗಿದೆ",
  "translated_text": "My headache has increased.",
  "is_read": false,
  "read_at": null,
  "delivery_status": "delivered",
  "translation_status": "completed",
  "is_uncertain": false,
  "reply_to_id": null,
  "audio_payload": null,
  "audio_format": null,
  "consent_confirmed": true,
  "stt_provider": "none",
  "translation_provider": "hosted_translation",
  "tts_provider": "none",
  "created_at": "2026-11-24T16:35:00Z",
  "disclaimer": "REAL TRANSLATION: Translated using automated multilingual neural machine translation models. Non-emergency assistive interaction only."
}
```

#### 7.6.4 Reply to Message
* **Endpoint**: `POST /api/v1/voice/messages/{message_id}/reply`
* **Description**: Threaded reply to an earlier message with reciprocal language translation.

#### 7.6.5 Translate Message On Demand
* **Endpoint**: `POST /api/v1/voice/messages/{message_id}/translate`
* **Request JSON:**
```json
{
  "target_language": "hi",
  "consent_confirmed": true
}
```

#### 7.6.6 Synthesize Message Audio On Demand
* **Endpoint**: `POST /api/v1/voice/messages/{message_id}/synthesize`
* **Request JSON:**
```json
{
  "language_code": "kn",
  "voice_gender": "female",
  "audio_format": "audio/mp3",
  "consent_confirmed": true
}
```

#### 7.6.7 Mark Message as Read
* **Endpoint**: `PATCH /api/v1/voice/messages/{message_id}/read`
* **Endpoint**: `POST /api/v1/voice/conversations/{partner_id}/read-all`

---

### 7.7 End-to-End Multilingual Voice Message Workflow
* **Endpoint**: `POST /api/v1/voice/workflow/dispatch`
* **Access**: Authenticated Patient or Caregiver (Bearer JWT)
* **Description**: Orchestrates the complete end-to-end multilingual workflow across speech recognition, language identification, text translation, message persistence, and text-to-speech audio generation.

**Request JSON (Audio Speech Input):**
```json
{
  "recipient_id": 2,
  "audio_base64": "UklGRi...",
  "audio_format": "audio/wav",
  "language_hint": "kn",
  "target_language": "en",
  "generate_tts": true,
  "voice_gender": "female",
  "tts_audio_format": "audio/mp3",
  "consent_confirmed": true
}
```

**Response JSON (200 OK):**
```json
{
  "message_id": 43,
  "sender_id": 1,
  "recipient_id": 2,
  "stage_statuses": {
    "audio_validation": "completed",
    "stt_transcription": "completed",
    "language_detection": "completed",
    "translation": "completed",
    "tts_synthesis": "completed"
  },
  "source_language": "kn",
  "target_language": "en",
  "original_text": "ನನ್ನ ನಾಡಿಮಿಡಿತ ಸ್ಥಿರವಾಗಿದೆ.",
  "translated_text": "My pulse is steady.",
  "uncertain_speech": false,
  "uncertain_translation": false,
  "is_uncertain": false,
  "audio_payload": "//uQZ...",
  "audio_format": "audio/mp3",
  "stt_provider": "hosted_whisper",
  "translation_provider": "hosted_translation",
  "tts_provider": "hosted_tts",
  "disclaimers": [
    "REAL STT: Speech recognized using automated acoustic AI models.",
    "REAL TRANSLATION: Translated using automated multilingual neural machine translation models.",
    "REAL TTS: Acoustic speech synthesized using automated text-to-speech models."
  ],
  "created_at": "2026-11-24T16:40:00Z"
}
```

---

### 7.8 Real-Time Communication WebSocket
* **Endpoint**: `ws://<host>:<port>/api/v1/voice/ws?token=<jwt_access_token>`
* **Description**: Authenticated WebSocket connection for receiving instantaneous event dispatches when messages arrive or read receipts are updated. Heartbeat ping/pong supported. Polling-compatible REST endpoints `/conversations` and `/messages/unread-count` serve as robust fallbacks.

```
