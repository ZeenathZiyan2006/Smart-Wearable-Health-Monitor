# PulseGuardian AI – Smart Wearable Health & Emergency Protection Backend

PulseGuardian AI is an enterprise-grade IoT backend and intelligent telemetry processing pipeline designed for elderly health monitoring, multi-tier caregiver escalation, and multilingual regional voice assistance.

## Technology Stack
- **Framework**: FastAPI (Python 3.10+)
- **ORM & Database**: SQLAlchemy 2.0 with Alembic database migrations (PostgreSQL & SQLite supported)
- **Security**: JWT (PyJWT), Argon2-cffi password hashing, Role-Based Access Control (RBAC)
- **AI & Analytics**: Scikit-learn (Isolation Forest for unsupervised acute anomaly detection), EWMA & linear trend analysis for Health Drift Intelligence, Personalized Digital Twin Baselines
- **Voice & Multilingual**: OpenAI Whisper STT, AI4Bharat IndicTrans2 / GPT-4o-mini translation, Text-To-Speech (TTS), Emergency Dictionaries, WebSockets, Audio duration and EBML/WAV validators
- **Wearable Hardware**: ESP32 microcontroller, MAX30102 (Heart Rate & SpO2), MPU6050 (Inertial 3-axis Accelerometer / Fall Detection), NEO-6M GPS

---

## Architecture Overview

```
                                      ┌────────────────────────────────────────────────┐
                                      │             PulseGuardian AI Backend           │
                                      │  (FastAPI + SQLAlchemy + Pydantic + Security)  │
┌────────────────────────┐            ├────────────────────────────────────────────────┤
│ ESP32 Smart Wearable   │            │ 1. Telemetry Ingestion Pipeline                │
│ - MAX30102 (HR/SpO2)   │───HTTP/WS─►│    (MAX30102, MPU6050 Accelerometer, GPS)      │
│ - MPU6050 (Fall Accel) │            │ 2. Digital Twin & Health Drift Intelligence    │
│ - GPS NEO-6M           │            │    (Adaptive Baselines, Trajectory Shifts)     │
└────────────────────────┘            │ 3. Acute Anomaly & Emergency Escalation Ladder │
                                      │    (SOS, Fall Impact, Multi-tier Caregivers)   │
┌────────────────────────┐            │ 4. Multilingual Voice & Regional Messaging     │
│ Patient & Caregiver    │◄──REST/WS──┤    (Kannada, Hindi, Malayalam, English, etc.)  │
│ Web / Mobile Dashboards│            │ 5. Device Management, Reports & Audit Logs     │
└────────────────────────┘            └────────────────────────────────────────────────┘
```

---

## Quickstart Guide

### 1. Environment Setup
```powershell
cd "C:\Users\User\Documents\thisha_mydetails\Smart wareable device\backend"

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate   # Windows PowerShell
# source venv/bin/activate # Linux / macOS

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
For local zero-dependency development (without Docker/PostgreSQL), configure `.env`:
```ini
DATABASE_URL="sqlite:///./pulseguardian.db"
VOICE_STT_PROVIDER="mock_development"
VOICE_TRANSLATION_PROVIDER="mock_development"
VOICE_TTS_PROVIDER="mock_development"
```

### 3. Run Database Migrations
Apply all schema migrations via Alembic:
```powershell
python -m alembic upgrade head
```

### 4. Seed Demo Data
Populate the database with realistic patients, caregivers, 24h vitals, GPS, digital twin baselines, and conversation threads:
```powershell
python -m app.scripts.seed_demo_data --clean
```
**Demo Accounts Created:**
- **Patient**: `patient@pulseguardian.ai` / `Patient@123` (Preferred Language: Kannada `kn`)
- **Primary Caregiver**: `caregiver@pulseguardian.ai` / `Caregiver@123` (Preferred Language: English `en`)
- **Secondary Caregiver**: `caregiver2@pulseguardian.ai` / `Caregiver@123` (Preferred Language: Hindi `hi`)

### 5. Launch Development Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **API Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Interactive Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **System Health Check**: [http://localhost:8000/](http://localhost:8000/)

### 6. Run Automated Tests
```powershell
python -m pytest tests -v
```
All **160 test cases** across all modules run automatically with zero external dependencies using an isolated in-memory test database.

---

## Complete API Module Reference

### 1. Authentication & Profile (`/api/v1/auth`)
- `POST /api/v1/auth/register`: Register patient or caregiver with profile initialization.
- `POST /api/v1/auth/login`: Issue JWT access and refresh tokens.
- `POST /api/v1/auth/refresh`: Refresh expired JWT access token.
- `GET  /api/v1/auth/me`: Retrieve currently authenticated user profile.
- `PUT  /api/v1/auth/me`: Update profile (full_name, phone_number, preferred_language).
- `POST /api/v1/auth/change-password`: Change password with Argon2 verification.
- `POST /api/v1/auth/logout`: Invalidate session.
- `POST /api/v1/auth/forgot-password`: Request password reset token.
- `POST /api/v1/auth/reset-password`: Reset password using token.

### 2. Wearable Device Management (`/api/v1/devices`)
- `POST /api/v1/devices/pair`: Pair physical ESP32 or simulated device to patient.
- `GET  /api/v1/devices`: List registered devices.
- `GET  /api/v1/devices/{device_id}`: Get device status, battery level, firmware version.
- `PUT  /api/v1/devices/{device_id}/config`: Configure sampling rates, thresholds, sensor toggles.
- `POST /api/v1/devices/{device_id}/sync`: Trigger manual sync and refresh online state.
- `POST /api/v1/devices/{device_id}/disconnect`: Disconnect device.
- `GET  /api/v1/devices/{device_id}/history`: Retrieve device connection & sync logs.
- `POST /api/v1/devices/{device_id}/simulate`: Test simulator generating clearly-labeled synthetic telemetry.

### 3. Health Telemetry & Reports (`/api/v1/health`)
- `POST /api/v1/health/telemetry`: Ingest single wearable telemetry point (HR, SpO2, Temp, Accel, Fall, BP, Respiration).
- `POST /api/v1/health/telemetry/batch`: Ingest buffered offline telemetry with duplicate deduplication.
- `GET  /api/v1/health/latest`: Retrieve most recent vitals reading.
- `GET  /api/v1/health/history`: Historical telemetry with date-range filtering and pagination.
- `GET  /api/v1/health/trends`: Health trend analysis over 24h, 7d, 30d windows.
- `GET  /api/v1/health/device-status`: Online/offline status, battery %, hardware staleness checks.
- `GET  /api/v1/health/dashboard`: Consolidated view (latest vitals, 24h summary, device status).
- `GET  /api/v1/health/reports/daily`: 24-hour breakdown report with hourly averages.
- `GET  /api/v1/health/reports/weekly`: 7-day day-by-day aggregated metrics.
- `GET  /api/v1/health/reports/export`: Downloadable health export in JSON or CSV format.

### 4. Emergency SOS & Escalation (`/api/v1/emergency`)
- `POST /api/v1/emergency/sos`: Trigger emergency SOS with automatic GPS backfill and localized summary.
- `POST /api/v1/emergency/assistance`: Request "I'm Not Okay" caregiver assistance.
- `GET  /api/v1/emergency/alerts`: List active and historical emergency alerts.
- `GET  /api/v1/emergency/{alert_id}`: Retrieve alert details and escalation timeline.
- `POST /api/v1/emergency/{alert_id}/acknowledge`: Caregiver acknowledges alert and halts escalation ladder.
- `POST /api/v1/emergency/{alert_id}/reject`: Caregiver marks alert as false alarm.
- `GET  /api/v1/emergency/{alert_id}/escalation-history`: Complete audit trail of dispatched caregiver notifications.

### 5. In-App Notifications (`/api/v1/notifications`)
- `GET   /api/v1/notifications`: List in-app notifications with filtering (`unread_only`, `type`).
- `GET   /api/v1/notifications/unread-count`: Unread notification badge count.
- `PATCH /api/v1/notifications/{id}/read`: Mark notification as read.
- `POST  /api/v1/notifications/read-all`: Mark all notifications as read.
- `DELETE /api/v1/notifications/{id}`: Archive/dismiss notification.

### 6. AI Engine & Digital Twin (`/api/v1/ai`)
- `POST /api/v1/ai/analyze`: Multi-signal vitals anomaly analysis (acute redlines, exercise distinction, cardiorespiratory stress).
- `GET  /api/v1/ai/health-status`: Patient composite AI health rating and wellness state.
- `GET  /api/v1/ai/anomalies`: Historical AI anomaly logs with severity filtering.
- `GET  /api/v1/ai/digital-twin`: Retrieve full Digital Twin baseline model.
- `GET  /api/v1/ai/digital-twin/baseline`: Learned physiological normal bounds.
- `GET  /api/v1/ai/health-timeline`: Composite health events and anomalies timeline.

### 7. Health Drift Intelligence (`/api/v1/ai/health-drift`)
- `GET  /api/v1/ai/health-drift/summary`: Multi-window trajectory analysis (HR, SpO2, Temp, Steps, Sleep).
- `GET  /api/v1/ai/health-drift/metric/{metric_name}`: Detailed EWMA and slope metrics for a single biomarker.
- `GET  /api/v1/ai/health-drift/timeline`: Chronological drift trajectory logs.
- `POST /api/v1/ai/health-drift/analyze`: Trigger custom-window statistical drift calculation.

### 8. Multilingual Voice Assistance & Messaging (`/api/v1/voice`)
- `GET  /api/v1/voice/languages`: Supported languages (Kannada `kn`, English `en`, Hindi `hi`, Malayalam `ml`, Tamil `ta`, Telugu `te`, Urdu `ur`).
- `GET  /api/v1/voice/consent`: Retrieve voice recording and translation consent status.
- `POST /api/v1/voice/consent`: Grant or revoke affirmative voice consent.
- `POST /api/v1/voice/transcribe`: Speech-To-Text (STT) audio transcription with EBML/WAV duration validation.
- `POST /api/v1/voice/translate`: Multilingual text translation.
- `POST /api/v1/voice/synthesize`: Text-To-Speech (TTS) speech synthesis.
- `GET  /api/v1/voice/conversations`: List active patient-caregiver conversation threads.
- `GET  /api/v1/voice/conversations/{partner_id}`: Retrieve message history between patient and caregiver.
- `POST /api/v1/voice/conversations/{partner_id}/read-all`: Mark all messages in thread as read.
- `POST /api/v1/voice/messages`: Send bilingual message (stores original text, translated text, language codes).
- `GET  /api/v1/voice/messages/unread-count`: Unread conversation messages badge count.
- `PATCH /api/v1/voice/messages/{id}/read`: Mark message as read.
- `POST /api/v1/voice/workflow/dispatch`: End-to-end voice workflow (STT -> Translate -> Anomaly Check -> TTS).
- `WS   /api/v1/voice/ws`: Real-time WebSocket channel for streaming voice messages.

### 9. GPS Geolocation Tracking (`/api/v1/location`)
- `POST /api/v1/location/track`: Ingest GPS coordinates from wearable NEO-6M module.
- `POST /api/v1/location/track/batch`: Ingest buffered GPS fixes.
- `GET  /api/v1/location/latest`: Most recent coordinates and fix staleness.
- `GET  /api/v1/location/history`: Historical location track logs with date filtering.

### 10. Patients, Caregivers & Associations (`/api/v1/users`)
- `GET    /api/v1/users/patients`: List patient profiles (caregiver/admin).
- `GET    /api/v1/users/patients/{id}`: Get patient medical profile.
- `PUT    /api/v1/users/patients/{id}`: Update patient profile.
- `GET    /api/v1/users/caregivers`: List caregiver profiles.
- `POST   /api/v1/users/associations`: Link patient and caregiver with escalation tier (Tier 1, Tier 2).
- `DELETE /api/v1/users/associations/{id}`: Remove patient-caregiver association.

### 11. System Audit Logs (`/api/v1/audit`)
- `GET  /api/v1/audit`: List immutable system audit events (logins, registrations, device pairings, emergencies).
- `POST /api/v1/audit/log`: Record critical administrative or system event.

---

## Safety & Medical Disclaimer
PulseGuardian AI is an educational prototype. Readings, anomaly detections, and AI-generated alerts do not replace professional medical devices, medical diagnosis, or emergency dispatch services (911/112).
