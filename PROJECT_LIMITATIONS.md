# PulseGuardian AI — Project Limitations & Academic Transparency

This document outlines the engineering boundaries, architectural constraints, and real-world considerations of the **PulseGuardian AI: Smart Wearable Health Monitor** project. Clear acknowledgment of these factors demonstrates rigorous academic honesty during project evaluations.

---

## 1. Hardware & Sensor Domain Limitations

### 1.1 MAX30102 Optical PPG vs Clinical Diagnostic ECG
- **Current Prototype Hardware**: The physical prototype utilizes the **Maxim Integrated MAX30102** sensor module, which operates via **optical Photoplethysmography (PPG)**. It measures reflected infrared and red light to infer arterial volume fluctuations.
- **Limitation**: PPG cannot detect myocardial electrical depolarization vectors (P-wave, QRS-complex voltage morphology, ST-segment elevation/depression).
- **Academic Distinction**: The real-time ECG waveform shown on the application dashboard is a **realistic digital signal processing (DSP) mathematical simulation** modeled after cardiac Lead I electrophysiology.
- **Clinical Prerequisite for True ECG**: Diagnosing clinical arrhythmias (e.g., Atrial Fibrillation, STEMI) requires dedicated biopotential instrumentation amplifiers (e.g., **Analog Devices AD8232** or **Texas Instruments ADS1292R**) paired with differential Ag/AgCl wet electrode leads.

### 1.2 Motion Artifacts & Ambient Light Sensitivity
- Optical PPG signals are susceptible to motion artifacts (walking, wrist movement) and loose skin contact.
- In production medical devices, complex dual-channel photodiode filtering, adaptive LMS (Least Mean Squares) noise cancellation, and tight hardware wrist-coupling are mandatory.

---

## 2. Regulatory & Medical Device Non-Certification

### 2.1 Assistive Monitoring vs Medical Diagnosis
- **Important Notice**: PulseGuardian AI is an **assistive academic health monitoring prototype**, NOT a certified medical diagnostic device.
- It has not been evaluated or certified by regulatory bodies such as:
  - US FDA (510(k) Premarket Notification or De Novo clearance).
  - CE Mark (European Medical Device Regulation - MDR 2017/745).
  - CDSCO (Central Drugs Standard Control Organisation, India).
- It must not be utilized as the sole basis for clinical diagnostic decisions, acute cardiac monitoring, or life-support emergency dispatch without human verification.

---

## 3. Artificial Intelligence & Third-Party Service Dependencies

### 3.1 Cloud AI Adapter Fallbacks (Whisper & LLMs)
- Voice transcription (STT) and clinical translation rely on OpenAI APIs (Whisper, GPT translation) or equivalent cloud AI endpoints.
- When valid API keys or active internet connectivity are absent, the application gracefully degrades to **mock development mode**:
  - Voice queries use pre-programmed acoustic pattern recognition.
  - Multilingual translations leverage deterministic emergency medical dictionary lookups.
- This ensures the application remains fully testable offline, but full conversational fluidity requires active cloud subscriptions.

### 3.2 Digital Twin Baseline Sample Size
- The **Isolation Forest** multivariate anomaly detector and **EWMA drift analysis** achieve statistical significance only after a minimum of **14 to 30 continuous days of telemetry** has been logged.
- For short-term demonstrations, baseline data is pre-seeded with synthetic variance to demonstrate algorithmic drift behavior.

---

## 4. Connectivity, Power & Operational Constraints

### 4.1 Battery Life & Continuous Sampling
- The ESP32 microcontroller with active Wi-Fi transmission consumes 80–150 mA, draining a typical 500 mAh Li-Po battery in 4 to 6 hours if continuously streaming.
- **Production Mitigation Strategy**: In real-world deployments, ESP32 deep sleep modes, batch transmission (e.g., transmitting once every 5 minutes), and Bluetooth Low Energy (BLE) peripheral mode must be adopted to achieve multi-day battery autonomy.

### 4.2 Network Latency & Offline Geolocation
- Emergency SOS dispatch and GPS geofencing rely on browser GNSS coordinates and stable HTTP/WebSocket internet connectivity.
- In environments with cellular blind spots or offline patients, edge-based cellular fallback modules (e.g., SIM800L / SIM7000 4G LTE) with onboard GPS antennas would be necessary for mission-critical SOS delivery.
