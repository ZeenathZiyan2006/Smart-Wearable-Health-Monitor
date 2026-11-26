# PulseGuardian AI — Hardware Integration & Production Deployment Guide

## 1. ESP32 Wearable Firmware & Integration Structure

The backend accepts telemetry batches from wearable hardware at `/api/v1/health/telemetry/batch` and real-time continuous ECG buffers at `/api/v1/health/ecg/stream`.

### Target Hardware Bill of Materials (BOM)
- **MCU**: ESP32-WROOM-32 (Dual-core 240 MHz, 2.4 GHz Wi-Fi + BLE 4.2).
- **PPG Photoplethysmography Sensor**: MAX30102 (I2C: SDA GPIO 21, SCL GPIO 22) for continuous Heart Rate and SpO2.
- **IMU / Accelerometer**: MPU6050 6-DOF (I2C: 0x68) for step counting, activity kinematics, and fall shock detection.
- **GPS / GNSS Module**: u-blox NEO-6M (UART: TX GPIO 17, RX GPIO 16) for outdoor coordinate acquisition.
- **Power**: 3.7V 500mAh LiPo battery with TP4056 USB-C charging management and MAX17048 I2C fuel gauge.

---

### ESP32 Telemetry JSON Batch Payload Format
Endpoint: `POST /api/v1/health/telemetry/batch`  
Headers: `Content-Type: application/json`

```json
{
  "device_uuid": "PG-ESP32-8921",
  "readings": [
    {
      "heart_rate": 74.5,
      "spo2": 98.2,
      "temperature": 36.7,
      "temperature_unit": "C",
      "step_count": 4830,
      "activity_type": "walking",
      "accelerometer_x": 0.08,
      "accelerometer_y": 0.12,
      "accelerometer_z": 0.98,
      "fall_detected": false,
      "battery_percentage": 91.5,
      "recorded_at": "2026-11-26T08:30:00Z"
    }
  ]
}
```

---

### ESP32 Raw ECG Stream Format
Endpoint: `POST /api/v1/health/ecg/stream`  
Headers: `Content-Type: application/json`

```json
{
  "device_uuid": "PG-ESP32-8921",
  "sampling_rate_hz": 250,
  "lead": "Lead I",
  "samples": [0.12, 0.15, -0.05, 1.45, -0.22, 0.35, ...],
  "is_simulated": false
}
```

---

## 2. Real AI Services Configuration

Configure these environment variables in `backend/.env` to switch from development mocks to real cloud AI services:

```ini
# --- STT (Speech-to-Text) ---
# Options: "mock_development", "hosted_whisper", "local_whisper"
VOICE_STT_PROVIDER=hosted_whisper
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_API_KEY_HERE
OPENAI_API_BASE=https://api.openai.com/v1

# --- Multilingual Translation ---
# Options: "mock_development", "hosted_translation", "local_indictrans"
VOICE_TRANSLATION_PROVIDER=hosted_translation
TRANSLATION_API_KEY=sk-proj-YOUR_OPENAI_API_KEY_HERE
TRANSLATION_MODEL_NAME=gpt-4o-mini

# --- TTS (Text-to-Speech) ---
# Options: "mock_development", "hosted_tts", "local_tts"
VOICE_TTS_PROVIDER=hosted_tts
TTS_API_KEY=sk-proj-YOUR_OPENAI_API_KEY_HERE
TTS_MODEL_NAME=tts-1
```

---

## 3. Real-Time WebSocket Communication

Connect authenticated real-time WebSocket clients at:
```text
ws://localhost:8000/api/v1/voice/ws?token=<ACCESS_JWT_TOKEN>
```
- **Ping/Pong Heartbeat**: Send `"ping"` to receive `"pong"`.
- **Live Notifications**: Broadcasts inbound chat messages, translation updates, and emergency alert escalation receipts.

---

## 4. Production Deployment Checklist

1. **Database Setup**: Set `DATABASE_URL=postgresql+psycopg2://user:password@host:5432/pulseguardian_db`.
2. **Migrations**: Run `alembic upgrade head`.
3. **Frontend Build**: Execute `cd frontend && npm run build` and serve `/dist` via Nginx or Cloudflare CDN.
4. **Backend Server**: Run via Gunicorn with Uvicorn worker class:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
   ```
