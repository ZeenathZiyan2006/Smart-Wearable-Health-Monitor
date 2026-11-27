# PulseGuardian AI ❤️
### Advanced AI-Powered Wearable Healthcare, Emergency Protection & Multilingual Caregiver Ecosystem

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19.3-61DAFB.svg?style=flat&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

PulseGuardian AI is an intelligent, full-stack healthcare ecosystem designed for elderly individuals, chronic care patients, family caregivers, attending physicians, and emergency response teams (EMS).

It unites IoT wearable telemetry, an AI personal health digital twin, bi-directional real-time multilingual translation, high-volume emergency alarms, and role-based clinical dashboards into a unified platform.

---

## 🌟 System Architecture

```
                                  +-----------------------------+
                                  |   ESP32 / Wearable Device   |
                                  | (Heart Rate, SpO2, GPS, SOS)|
                                  +--------------+--------------+
                                                 | (HTTP / BLE / WS)
                                                 v
+---------------------------------------------------------------------------------------------------+
|                                  FastAPI Backend Core (Port 8000)                                 |
|                                                                                                   |
|  [Security & RBAC]      [AI Digital Twin]      [Multilingual NLP]       [Telemetry & Emergency]   |
|  - Patient Auth         - Baseline Learning    - IndicTrans2            - Fall Detection (112)    |
|  - Family Caregiver     - Isolation Forest     - Audio STT / TTS        - Geofence & GPS Tracking |
|  - Attending Doctor     - Anomaly Detector     - WebSocket Chat Feed    - Medication Scheduler    |
+------------------------------------------------+--------------------------------------------------+
                                                 |
         +---------------------------------------+---------------------------------------+
         v                                                                               v
+-------------------------------+                               +-----------------------------------+
|      Database Engine          |                               |   React + Vite Frontend (Port 5173)|
| - Default: SQLite (portable)  |                               |                                   |
| - Production: PostgreSQL 16   |                               | 1. Patient Self-Care Portal       |
| - Cache & Broker: Redis 7     |                               | 2. Family Caregiver Dashboard     |
+-------------------------------+                               | 3. Attending Doctor Clinical Hub  |
                                                                | 4. Emergency Response (EMS) Hub   |
                                                                +-----------------------------------+
```

---

## 🚀 Quick Start: Run on Any System

You can run this project on **Windows, macOS, Linux, or via Docker** in minutes.

### Option 1: Docker Compose (Recommended - Single Command)

Pre-requisite: [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

```bash
# 1. Clone the repository
git clone https://github.com/ZeenathZiyan2006/Smart-Wearable-Health-Monitor.git
cd Smart-Wearable-Health-Monitor

# 2. Build and launch all services (PostgreSQL + Redis + FastAPI Backend + React Nginx Frontend)
docker compose up --build
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173) (also available on [http://localhost:80](http://localhost:80))
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: 1-Click Scripts (No Docker Required)

Out of the box, PulseGuardian AI automatically uses an embedded portable SQLite database (`pulseguardian.db`) and auto-seeds all demo accounts on first launch—**no PostgreSQL installation or manual database setup required!**

#### On Windows:
Double-click `run.bat` or open PowerShell / Command Prompt:
```cmd
cd "Smart-Wearable-Health-Monitor"
.\run.bat
```
*(If it is your first time running, `run.bat` will automatically invoke `setup.bat` to configure your virtual environment and install dependencies).*

#### On macOS / Linux:
Make the launch scripts executable and run:
```bash
chmod +x setup.sh run.sh
./run.sh
```

---

### Option 3: Manual Terminal Setup

#### 1. Backend Setup:
```bash
cd backend

# Create and activate Python virtual environment
python3 -m venv .venv
# On Windows: .venv\Scripts\activate
# On macOS/Linux: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file from example template
cp .env.example .env

# Launch FastAPI backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup:
In a separate terminal:
```bash
cd frontend

# Copy environment template
cp .env.example .env

# Install dependencies
npm install

# Start Vite development server
npm run dev -- --host 0.0.0.0 --port 5173
```

---

## 👥 Demo Login Credentials

The database automatically seeds complete demo profiles for all four system roles upon first launch:

| Role | Email | Password | Access & Dashboard |
| :--- | :--- | :--- | :--- |
| **1. Patient** | `monisha@pulseguardian.ai` | `Password@123` | Patient self-care portal, live telemetry, medication alarms, multilingual chat, Nova assistant, QR health pass |
| **2. Family Caregiver** | `caregiver@pulseguardian.ai` | `Password@123` | Family monitoring view, live GPS tracking, medication logs, real-time translated chat & alert feeds |
| **3. Attending Doctor** | `dr.sunita@pulseguardian.ai` | `Password@123` | Clinical diagnostic dashboard, EHR, ECG waveforms, active prescriptions management, clinical notes |
| **4. Emergency Response (EMS)** | `ems.rajesh@pulseguardian.ai` | `Password@123` | Emergency dispatch portal, live SOS coordinates, triage vitals, medical history, turn-by-turn map routing |

> **Default Verified Patient ID**: `PT-2026-000001`  
> **Default Patient Name**: `Ramesh Kumar` / `monisha`

---

## 🔑 Key Features & Innovations

1. **Role-Separated Dashboards**:
   - Strictly isolated views for Patient, Family, Doctor, and Emergency Team.
   - Authorized caregiver verification via Patient ID (`PT-YYYY-XXXXXX`) or QR token scan.

2. **Multilingual Caregiver Communication**:
   - Real-time bidirectional translation between Patient and Caregivers.
   - Native audio pronunciation (Kannada, Hindi, Tamil, Telugu, Malayalam, English).
   - Real-time notification dispatch to caregiver email and dashboard feed.

3. **Active Prescription & Medication Alarm**:
   - Continuous 100% volume audio alarm at scheduled dosage times.
   - Atomic **Taken** button that locks until the next alarm cycle and decrements inventory.
   - Low-stock and out-of-stock emergency alerts sent to caregivers.

4. **Nova Voice Assistant**:
   - Activated via screen long-press or saying the wake word **"Nova"**.
   - Direct emergency dialing to verified emergency contacts.
   - Multilingual voice responses with speech synthesis fallback.

5. **Verified Emergency QR Health Pass**:
   - Universal scan & verify modal for smartphones and hospital terminals.
   - Instant emergency medical summary, blood group, allergies, and uploaded PDF health reports.

---

## 🧪 Automated Testing & Verification

Run the full backend test suite (192 unit and integration tests):
```bash
cd backend
python -m pytest tests/ -v
```

Verify frontend TypeScript compilation and production build:
```bash
cd frontend
npm run build
```

---

## ⚙️ Environment Variables Reference

### Backend (`backend/.env`):
- `DATABASE_URL`: Defaults to portable `sqlite:///./pulseguardian.db`. Can be switched to `postgresql+psycopg2://user:pass@host:5432/db` for PostgreSQL.
- `SECRET_KEY`: JWT authentication signing key.
- `BACKEND_CORS_ORIGINS`: Allowed client origins (defaults to localhost:5173, localhost:3000, localhost:80).
- `ENVIRONMENT`: Set to `development`, `testing`, or `production`.

### Frontend (`frontend/.env`):
- `VITE_API_BASE_URL`: Base URL for the FastAPI backend (`http://localhost:8000/api/v1`).

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
