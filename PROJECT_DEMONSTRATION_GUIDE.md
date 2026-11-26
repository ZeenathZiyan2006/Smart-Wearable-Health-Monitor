# PulseGuardian AI — Complete Project Demonstration Guide

This guide provides an exact, step-by-step walkthrough for demonstrating the **PulseGuardian AI: Smart Wearable Health Monitor** during project evaluations and technical vivas.

---

## 1. System Prerequisites & Launch Sequence

### 1.1 Prerequisites
- **Python**: 3.10+ (Verified on Python 3.13)
- **Node.js**: v18+ (Verified on Node.js v24)
- **Database**: SQLite (built-in file `backend/pulseguardian.db`) or PostgreSQL.

### 1.2 Step 1: Start Backend API Server
Open a terminal in the project root:
```powershell
cd "C:\Users\User\Documents\thisha_mydetails\Smart wareable device\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API URL**: `http://127.0.0.1:8000`
- **Swagger Interactive API Docs**: `http://127.0.0.1:8000/docs`
- **Health Check Endpoint**: `http://127.0.0.1:8000/api/v1/health-check` (returns `{"status": "ok"}`)

### 1.3 Step 2: Start Frontend Application
Open a second terminal:
```powershell
cd "C:\Users\User\Documents\thisha_mydetails\Smart wareable device\frontend"
npm run dev
```
- **Frontend Web Application URL**: `http://localhost:5173`

---

## 2. Demonstration Accounts & Credentials

The pre-seeded database contains both **Patient** and **Caregiver** roles:

| Role | Email Address | Password | Name / Title | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Patient** | `patient@pulseguardian.ai` | `password123` | Ramesh Kumar | Monitored individual with wearable band paired |
| **Primary Caregiver** | `caregiver@pulseguardian.ai` | `password123` | Dr. Sunita Rao | Primary physician receiving urgent escalations |
| **Secondary Caregiver** | `caregiver2@pulseguardian.ai` | `password123` | Nurse Anita Sharma | Secondary caregiver on the escalation ladder |

---

## 3. End-to-End Demonstration Workflow

### Workflow 1: Patient Authentication
1. Open `http://localhost:5173` in a browser (or incognito window).
2. The UI displays the customized split-screen Login page matching design specifications (medical care illustration on the left, branded login card on the right).
3. Toggle the role tab to **Patient**.
4. Enter credentials:
   - **Email**: `patient@pulseguardian.ai`
   - **Password**: `password123`
5. Click **Sign In**.
6. The app stores the JWT Bearer token in local storage and redirects to `/dashboard`.

---

### Workflow 2: Patient Health Dashboard Overview
Showcase the main dashboard widgets matching the approved design reference:
1. **Header Banner**: "Good Morning, Ramesh! Stay healthy, stay happy, and live longer."
2. **Device Status**: Shows `PulseGuardian Band v2`, Battery `92%`, and `Your wearable is connected`.
3. **Core Vitals Grid**:
   - **Heart Rate**: `72 BPM` (+2% vs baseline, green indicator).
   - **SpO2**: `98%` (+1% optimal oxygenation).
   - **Body Temperature**: `36.8 °C` (Normal range).
   - **Steps**: `4,820 / 6,000` (80% goal progress bar).
   - **Sleep**: `7h 20m` (Excellent quality).
4. **Live ECG Monitor Card**: Real-time canvas waveform renderer simulating Lead I at 250 Hz with PR (98 ms), QRS (82 ms), and QT (380 ms) interval readouts.
5. **AI Health Insights Card**: Summary indicating resting heart rate stability and personalized rest recommendation.
6. **Digital Twin Card**: Neon holographic human avatar displaying `Status: Stable` vs baseline.

---

### Workflow 3: Live ECG Simulation & Academic Disclaimer
1. Click **ECG Monitor** in the left sidebar (`/ecg`).
2. Show the evaluator the live, dynamic waveform visualization.
3. **Point out the Engineering Transparency Disclaimer** displayed prominently in the amber card:
   > *"Academic & Hardware Notice: The physical PulseGuardian band prototype utilizes the MAX30102 optical PPG sensor (measuring blood volume pulse). The waveform displayed here is a realistic DSP mathematical simulation of an ECG Lead I electrical rhythm. A clinical diagnostic ECG requires differential biopotential electrodes (e.g., AD8232 or TI ADS1292R)."*
4. Explain how this separates optical photoplethysmography from biopotential electrophysiology in academic examinations.

---

### Workflow 4: AI Health Insights & Digital Twin Drift Analysis
1. Navigate to **AI Insights** (`/ai-insights`) or click **View Details** on the Digital Twin card.
2. Present the baseline metrics computed by the backend:
   - Baseline Heart Rate Mean: `72.0 BPM` (Standard Deviation: 4.5).
   - Current EWMA (Exponentially Weighted Moving Average): `76.5 BPM`.
   - Z-Score Drift: `+1.0` (Mild upward drift detected).
3. Explain the **Isolation Forest** multivariate anomaly detector that flags multivariate deviations when resting vitals drift beyond statistical boundaries.

---

### Workflow 5: GPS Geofencing & Safety Tracking
1. Navigate to **GPS Tracking** (`/gps`).
2. The page uses the browser's HTML5 Geolocation API with a fallback to the registered safe home coordinates (`Lat: 13.0827, Lon: 80.2707`).
3. Click **Check Geofence Status**.
4. The backend computes the exact distance using the **Haversine Formula**:
   \[
   d = 2r \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)
   \]
5. If inside 500 meters, it confirms `Inside Safe Zone: Home`. If coordinates are simulated outside, it logs a geofence breach.

---

### Workflow 6: Emergency SOS Trigger (Press-and-Hold)
1. On the dashboard or in the sidebar, locate the **Emergency SOS** module.
2. Explain the safety UI feature: A simple click is prevented from triggering false alarms.
3. **Press and hold the red SOS button for 2 full seconds**.
4. A circular progress ring animates to 100%. Upon release, the frontend captures the current GPS latitude/longitude and sends a POST request to `/api/v1/health/emergency-sos`.
5. The backend initiates the **Caregiver Escalation Ladder**:
   - Creates an `emergency_alerts` record (`status: triggered`, `severity: critical`).
   - Automatically dispatches in-app notifications and SMS/webhook alerts to Primary Caregiver (`Dr. Sunita Rao`).
   - Starts an escalation timer to secondary caregivers if unacknowledged within 3 minutes.
6. The UI updates to show `SOS Dispatched — Help is on the way`.

---

### Workflow 7: Caregiver Login & Emergency Acknowledgement
1. Open a **new browser window or incognito session** at `http://localhost:5173`.
2. Toggle role to **Caregiver**.
3. Log in with:
   - **Email**: `caregiver@pulseguardian.ai`
   - **Password**: `password123`
4. The Caregiver dashboard opens.
5. In the top notification bell or on the active alert card, the critical SOS alert from **Ramesh Kumar** appears with exact GPS coordinates and timestamp.
6. Click **Acknowledge Alert**.
7. The backend changes the alert status from `triggered` to `acknowledged` with the caregiver's user ID and timestamp, stopping the escalation ladder.

---

### Workflow 8: Multilingual Caregiver-Patient Communication
1. In the Caregiver portal, click **Communication** (`/communication`).
2. Select patient **Ramesh Kumar**.
3. Type a message in English: `"Please sit down, rest, and drink water. Help is arriving in 5 minutes."`
4. Select destination language: **Tamil (ta)** or **Hindi (hi)**.
5. Click **Send Message**.
6. Switch back to the Patient window: The message arrives translated into the patient's preferred language with options to hear it read out via Text-to-Speech (TTS).

---

### Workflow 9: Voice Assistant Interaction
1. Click the **Voice Assistant** widget on the right sidebar of the Patient dashboard.
2. Click the microphone icon to record or select a quick query:
   - *"Are my vitals normal?"*
   - *"Show my health report"*
   - *"Call caregiver"*
3. The query is processed by the voice interpretation engine (via `/api/v1/voice/query` or WebSocket `/api/v1/voice/ws`).
4. The system provides a spoken and transcribed clinical response:
   > *"Your heart rate is 72 beats per minute and oxygen saturation is 98 percent. All vital parameters are within normal resting thresholds."*

---

### Workflow 10: Health History & Medical Report Export
1. Navigate to **Health History** (`/history`).
2. View the chronological telemetry logs with date filters.
3. Click **Export CSV** or **Export PDF/JSON Summary**.
4. The browser downloads the formatted health report containing statistical averages, peak heart rates, and recorded anomalies suitable for clinical review.

---

## 4. Disaster Recovery & Troubleshooting

| Symptom | Probable Cause | Instant Solution |
| :--- | :--- | :--- |
| **Frontend cannot reach backend (Network Error)** | Backend server is not running on port 8000 | Ensure `uvicorn app.main:app --port 8000` is running and accessible at `http://127.0.0.1:8000/docs`. |
| **Login fails with 401 Unauthorized** | Typing error in credentials | Use `patient@pulseguardian.ai` with `password123` (all lowercase). |
| **Vite shows Port 5174 instead of 5173** | Another process is holding port 5173 | The application functions identically on port 5174; update the browser URL accordingly. |
| **Database file locked or reset** | File permissions | The database file is located at `backend/pulseguardian.db`. Run `python -m pytest tests -q` to verify internal database integrity. |
