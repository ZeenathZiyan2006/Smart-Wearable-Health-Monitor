# PulseGuardian AI — Technical Viva Questions and Answers

This reference document prepares students and engineers for rigorous technical questioning during college project examinations, software architecture reviews, and oral defenses. Every answer is grounded directly in the actual source code of the repository.

---

## SECTION 1: ARCHITECTURE & SYSTEM DESIGN

### Q1: What is the high-level architecture of PulseGuardian AI?
**Answer:**
PulseGuardian AI employs a **modern, decoupled 3-tier client-server micro-monolith architecture**:
1. **Edge/Device Tier**: ESP32 microcontrollers communicating over Wi-Fi (HTTP REST batch telemetry) or Bluetooth Low Energy (BLE GATT characteristics) with sensor modules (optical PPG MAX30102).
2. **Backend Services Tier**: Built with Python 3.13 and FastAPI, structured in clean layered modules:
   - *Routers*: `/api/v1/auth`, `/health`, `/voice`, `/analytics`, `/devices`.
   - *Business Logic & Services*: Drift detection, baseline calculation, geofencing, emergency escalation ladders, translation/TTS adapters.
   - *Data Layer*: SQLAlchemy ORM 2.0 with declarative base models, repository patterns, and Alembic database migrations.
3. **Frontend Application Tier**: Single Page Application (SPA) built using React 19, TypeScript, Tailwind CSS, Lucide icons, and Vite, featuring lazy-loaded routes and authenticated WebSocket context for bi-directional streaming.

---

### Q2: Why did you choose FastAPI over traditional frameworks like Django or Flask?
**Answer:**
1. **Asynchronous Concurrency (`async`/`await`)**: FastAPI runs on Starlette and ASGI (Uvicorn), allowing thousands of concurrent I/O-bound requests (e.g., telemetry streaming, WebSockets, external AI API calls) on a single event loop without blocking thread pools.
2. **Type Safety & Automatic Validation**: Deep integration with Pydantic v2 ensures request payloads and query parameters are validated against strict type hints at runtime, eliminating boilerplate validation code.
3. **Native OpenAPI / Swagger Documentation**: Generates interactive documentation (`/docs`) directly from Python type annotations, streamlining frontend-backend contract validation.
4. **Lightweight & High Performance**: Flask lacks native ASGI async support, while Django includes heavy ORM and template abstractions unnecessary for a high-throughput REST/WebSocket telemetry backend.

---

### Q3: How is state and data persisted, and how does the system support both SQLite and PostgreSQL?
**Answer:**
The system uses **SQLAlchemy 2.0** as an Object-Relational Mapper. The database engine is instantiated dynamically from the `DATABASE_URL` environment variable:
- For local demonstration and offline test runners: `sqlite:///./pulseguardian.db` (zero external dependencies).
- For production Docker deployments: `postgresql+asyncpg://user:pass@db:5432/pulseguardian`.
All database schema evolution is managed via **Alembic migrations** (under `backend/alembic/`), ensuring deterministic table creation across environments.

---

## SECTION 2: EMBEDDED & SENSOR HARDWARE (MAX30102 vs ECG)

### Q4: Explain the difference between MAX30102 and true ECG hardware. Does your prototype measure true ECG?
**Answer:**
**Academic Truth & Distinction:**
- **MAX30102**: This is an **optical photoplethysmography (PPG)** sensor. It shines red (660 nm) and infrared (880 nm) LEDs through capillary blood vessels in the skin and measures reflected light using a photodiode. By analyzing blood volume pulsatile changes (AC/DC ratio), it calculates **Heart Rate (HR)** and **Oxygen Saturation (SpO2)** via the Beer-Lambert law.
- **True ECG (Electrocardiogram)**: Measures the **electrical biopotential voltage depolarization and repolarization vectors** of cardiac myocardium across the body (P wave, QRS complex, T wave). True ECG requires differential instrumentation amplifiers with ultra-high common-mode rejection ratio (CMRR), such as the **Analog Devices AD8232** or **Texas Instruments ADS1292R**, connected to physical Ag/AgCl wet electrodes.
- **Our System**: The physical wearable band prototype interfaces the MAX30102 optical sensor for genuine HR and SpO2 readings. The real-time ECG waveform shown on the dashboard is a **realistic digital signal processing (DSP) mathematical simulation** modeled on Lead I cardiac electrophysiology. We explicitly display this engineering disclaimer on our ECG dashboard to maintain academic integrity.

---

### Q5: How does the ESP32 communicate with the backend?
**Answer:**
The ESP32 firmware supports two primary modes:
1. **Wi-Fi REST Batch Telemetry**: Samples PPG vitals at fixed intervals (e.g., 25–50 Hz), buffers the readings in circular memory, and sends an aggregated JSON payload every 5–10 seconds to `POST /api/v1/health/telemetry/batch` using standard HTTP POST requests with a device Bearer token.
2. **BLE (Bluetooth Low Energy) GATT Services**: When paired to a mobile or gateway device, it advertises the standard Heart Rate Service (`UUID 0x180D`) and custom characteristics for battery and SpO2.

---

## SECTION 3: AI, DATA SCIENCE & CLINICAL ANALYTICS

### Q6: How does the AI Health Drift and Digital Twin engine work?
**Answer:**
Rather than relying on simplistic static thresholds (e.g., "HR > 100"), PulseGuardian AI computes a **personalized physiological baseline**:
1. **Baseline Computation**: The system calculates a 14-day rolling mean ($\mu$) and standard deviation ($\sigma$) for each vital sign (resting heart rate, daytime SpO2, sleep duration).
2. **EWMA (Exponentially Weighted Moving Average)**:
   \[
   S_t = \alpha \cdot Y_t + (1 - \alpha) \cdot S_{t-1}
   \]
   Here, $\alpha \in [0.2, 0.3]$ balances historical stability with recent physiological trends, filtering out momentary motion artifacts.
3. **Z-Score Drift Assessment**:
   \[
   Z = \frac{\text{EWMA} - \mu}{\sigma}
   \]
   - $|Z| \le 1.0$: Baseline Stable (Green).
   - $1.0 < |Z| \le 2.0$: Mild Physiological Drift (Yellow).
   - $|Z| > 2.0$: Significant Anomaly Drift (Red / Alert).
4. **Multivariate Anomaly Detection**: When sufficient telemetry points exist ($\ge 30$), the system fits an **Isolation Forest** (from `scikit-learn`) over multidimensional vital vectors (HR, SpO2, temperature, motion variance) to detect multivariate anomalies that univariate thresholds miss.

---

### Q7: How are Voice Assistance and Multilingual Caregiver Messaging implemented?
**Answer:**
The system is designed with an **Adapter Design Pattern** allowing both live cloud AI models and offline local development modes:
1. **Speech-to-Text (STT)**: Uses OpenAI Whisper API (`v1/audio/transcriptions`) over `httpx.AsyncClient` with audio format validation. In development/offline mode, a mock adapter transcribes local query audio cleanly.
2. **Clinical Translation**: Uses LLM translation prompt chaining or translation endpoints with specialized emergency dictionaries ensuring medical terms (e.g., "dyspnea", "chest discomfort", "tachycardia") are not lost in colloquial translation.
3. **Text-to-Speech (TTS)**: Translates clinical responses back into audio streams using OpenAI TTS (`tts-1` / `alloy` / `shimmer`) or Web Speech synthesis on the client side.

---

## SECTION 4: EMERGENCY SOS & SAFETY LOGIC

### Q8: Describe the Emergency SOS Escalation Ladder and how false alarms are prevented.
**Answer:**
1. **False Alarm Mitigation**:
   - In the frontend UI: A **2.0-second continuous press-and-hold** is required to trigger SOS, accompanied by visual progress bar filling and tactile feedback.
   - Accidental single clicks or keyboard events are completely ignored.
2. **Escalation Ladder Logic (`EmergencyEscalationService`)**:
   - **Stage 1 (T=0)**: SOS event created (`status: triggered`). Primary designated caregiver (`role: caregiver`) is alerted immediately via in-app notifications and urgent webhooks/SMS.
   - **Stage 2 (T=3 min)**: If the alert remains unacknowledged, the background worker automatically escalates to Secondary Caregivers and family contacts.
   - **Stage 3 (T=7 min)**: If still unacknowledged, an escalation notice is logged to emergency medical dispatch channels.
   - **State Transition**: As soon as any caregiver clicks **Acknowledge**, the alert state updates to `acknowledged`, the `acknowledged_at` timestamp and `caregiver_id` are stored, and the escalation timer halts.

---

### Q9: How does the GPS Geofencing mechanism work mathematically?
**Answer:**
The backend implements the **Haversine Great-Circle Distance Formula** in `app.services.geofence_service`:
\[
a = \sin^2\left(\frac{\Delta \text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta \text{lon}}{2}\right)
\]
\[
c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)
\]
\[
d = R \cdot c \quad (R = 6,371,000 \text{ meters})
\]
If the calculated distance $d$ between the patient's current coordinate and their registered safe center point (e.g., home) exceeds the configured radius (e.g., 500 meters), a `GEOFENCE_BREACH` event is recorded and dispatched to the caregiver's notification feed.

---

## SECTION 5: SECURITY, AUTHENTICATION & TESTING

### Q10: How is security and Role-Based Access Control (RBAC) enforced?
**Answer:**
1. **Password Hashing**: Passwords are never stored in plaintext; they are hashed using **bcrypt** with a cost factor (salt).
2. **Stateless JWT Authentication**: On login, the backend issues an HMAC-SHA256 signed JSON Web Token containing `sub` (user email), `user_id`, and `role` (`patient` or `caregiver`), with a configured expiration time.
3. **Route Protection**: FastAPI dependencies (`get_current_user`, `require_patient`, `require_caregiver`) inspect the `Authorization: Bearer <token>` header, decode the token, check revocation, and abort with `HTTP 401 Unauthorized` or `HTTP 403 Forbidden` if permissions do not match.
4. **WebSocket Authentication**: The `/api/v1/voice/ws` endpoint requires token passing during connection handshake to prevent unauthorized audio or telemetry interception.

---

### Q11: What is the extent of your automated test suite?
**Answer:**
The backend features an exhaustive **pytest** suite with **175 passing unit and integration tests** (`python -m pytest tests -q` runs in under 20 seconds):
- Authentication & password hashing tests.
- Role-based authorization tests for patients vs caregivers.
- Vital bounds validation and telemetry ingestion tests.
- AI drift calculation and EWMA math verification.
- Haversine geofence boundary tests.
- SOS escalation ladder transition tests.
- Audio validation and Whisper adapter tests.
- End-to-end multi-role workflow tests (`test_e2e_integration.py`).
- Frontend production builds have **zero TypeScript compiler errors** (`npm run build`).
