import pytest
from app.schemas.hardware_stream import ECGIngestRequest, GeofenceCheckRequest
from app.services.voice.adapters.whisper_adapter import HostedWhisperSTTAdapter
from app.services.voice.adapters.translation_adapter import HostedTranslationAdapter
from app.services.voice.adapters.tts_adapter import HostedOpenAITTSAdapter


def test_real_whisper_adapter_missing_key():
    adapter = HostedWhisperSTTAdapter(api_key="")
    with pytest.raises(RuntimeError) as exc:
        adapter.transcribe(b"fake audio data", content_type="audio/wav")
    assert "OPENAI_API_KEY is not configured" in str(exc.value)


def test_real_translation_adapter_missing_key():
    adapter = HostedTranslationAdapter(api_key="")
    with pytest.raises(RuntimeError) as exc:
        adapter.translate("Take vitamins", source_language="en", target_language="ta")
    assert "TRANSLATION_API_KEY" in str(exc.value) or "API key" in str(exc.value)


def test_real_tts_adapter_missing_key():
    adapter = HostedOpenAITTSAdapter(api_key="")
    with pytest.raises(RuntimeError) as exc:
        adapter.synthesize("Take medicine", language_code="en")
    assert "TTS_API_KEY" in str(exc.value) or "API key" in str(exc.value)


def test_ecg_stream_ingestion(client):
    # Simulated 250 Hz signal window (500 samples = 2.0s)
    samples = [0.0] * 500
    for i in range(0, 500, 60):
        samples[i] = 2.5 # Simulated R-peaks

    res = client.post("/api/v1/health/ecg/stream", json={
        "device_uuid": "PG-TEST-ECG",
        "sampling_rate_hz": 250,
        "lead": "Lead I",
        "samples": samples,
        "is_simulated": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["samples_received"] == 500
    assert data["duration_seconds"] == 2.0
    assert "Simulated DSP" in data["disclaimer"]


def test_geofence_boundary_within_safe_zone(client):
    res = client.post("/api/v1/health/geofence/check", json={
        "latitude": 12.9718,
        "longitude": 77.5948,
        "center_latitude": 12.9716,
        "center_longitude": 77.5946,
        "radius_meters": 500.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_inside"] is True
    assert data["alert_triggered"] is False
    assert data["distance_from_center_meters"] < 50.0


def test_geofence_boundary_breach_alert(client):
    # 2.5 km away from center
    res = client.post("/api/v1/health/geofence/check", json={
        "latitude": 12.9950,
        "longitude": 77.5950,
        "center_latitude": 12.9716,
        "center_longitude": 77.5946,
        "radius_meters": 500.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_inside"] is False
    assert data["alert_triggered"] is True
    assert data["distance_from_center_meters"] > 2000.0
