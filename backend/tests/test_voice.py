import base64
import io
import struct
import wave
import pytest
from app.models.voice import VoiceAuditLog, VoiceConsent
from app.schemas.voice import (
    MOCK_STT_DISCLAIMER,
    MOCK_TRANSLATION_DISCLAIMER,
    MOCK_TTS_DISCLAIMER,
    REAL_TTS_DISCLAIMER,
    SUPPORTED_LANGUAGE_CODES,
)
from app.services.voice.emergency_dictionary import get_draft_emergency_phrase


def make_synthetic_wav(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generates a valid in-memory PCM 16-bit mono WAV byte stream of specified duration."""
    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        total_frames = int(sample_rate * duration_seconds)
        w.writeframes(b"\x00\x00" * total_frames)
    return bio.getvalue()


def make_synthetic_mp3(frames_count: int = 40) -> bytes:
    """Generates a synthetic MPEG-1 Layer 3 byte stream (~1.045 seconds for 40 frames)."""
    frame_size = 417
    header = b"\xff\xfb\x90\x64"
    frame = header + b"\x00" * (frame_size - 4)
    return frame * frames_count


def make_synthetic_flac(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generates a minimal valid FLAC streaminfo header with specified duration."""
    total_samples = int(duration_seconds * sample_rate)
    sr_ch_bps_samples = (sample_rate << 44) | (0 << 41) | (15 << 36) | (total_samples & 0xFFFFFFFFF)
    return struct.pack(
        ">4sIHH3s3s8s16s",
        b"fLaC",
        0x80000022,
        4096,
        4096,
        b"\x00\x00\x00",
        b"\x00\x00\x00",
        sr_ch_bps_samples.to_bytes(8, "big"),
        b"\x00" * 16,
    )


def make_synthetic_m4a(duration_seconds: float = 3.5, timescale: int = 1000) -> bytes:
    """Generates an MP4/M4A header container with ftyp and moov->mvhd duration atom."""
    duration_val = int(duration_seconds * timescale)
    ftyp = struct.pack(">I4s4sI4s", 24, b"ftyp", b"M4A ", 0, b"mp42")
    mvhd_body = struct.pack(">4sB3sIIII", b"mvhd", 0, b"\x00\x00\x00", 0, 0, timescale, duration_val) + b"\x00" * 80
    mvhd = struct.pack(">I", len(mvhd_body) + 4) + mvhd_body
    moov = struct.pack(">I4s", len(mvhd) + 8, b"moov") + mvhd
    return ftyp + moov


def make_synthetic_webm(duration_seconds: float = 4.0) -> bytes:
    """Generates a valid WebM EBML header container with Duration tag (0x4489)."""
    dur_bytes = struct.pack(">f", float(duration_seconds * 1000.0))  # ms in float32
    return b"\x1a\x45\xdf\xa3" + b"\x00" * 10 + b"\x44\x89\x84" + dur_bytes


def test_get_supported_languages(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    response = client.get("/api/v1/voice/languages", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_supported"] == 7
    codes = [lang["code"] for lang in data["languages"]]
    for expected in SUPPORTED_LANGUAGE_CODES:
        assert expected in codes

    # Verify native script and direction for Urdu and Kannada
    urdu_info = next(l for l in data["languages"] if l["code"] == "ur")
    assert urdu_info["direction"] == "rtl"
    assert urdu_info["native_name"] == "اردو"

    kannada_info = next(l for l in data["languages"] if l["code"] == "kn")
    assert kannada_info["native_name"] == "ಕನ್ನಡ"
    assert kannada_info["direction"] == "ltr"

    assert data["mock_mode_active"] is True
    assert "privacy_notice" in data


def test_transcribe_with_consent_success(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(make_synthetic_wav(2.0)).decode("utf-8"),
        "audio_format": "audio/wav",
        "language_hint": "kn",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()

    assert res["is_mock"] is True
    assert res["provider"] == "mock_development"
    assert res["detected_language"] == "kn"
    assert res["disclaimer"] == MOCK_STT_DISCLAIMER
    assert "Simulated Audio Transcription" in res["transcript"]


def test_transcribe_without_consent_forbidden(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(b"test").decode("utf-8"),
        "language_hint": "en",
        "consent_confirmed": False
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Consent required" in response.json()["detail"]


def test_transcribe_unsupported_language_fails(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "language_hint": "xx",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Unsupported language code" in response.json()["detail"]


def test_translate_text_success(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "text": "Hello, how are you?",
        "source_language": "en",
        "target_language": "hi",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/translate", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()

    assert res["is_mock"] is True
    assert res["provider"] == "mock_development"
    assert res["target_language"] == "hi"
    assert res["disclaimer"] == MOCK_TRANSLATION_DISCLAIMER
    assert "[Simulated HI Translation]" in res["translated_text"]


def test_translate_unsupported_target_language_fails(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "text": "Hello",
        "target_language": "fr",  # French not in the 7 supported languages
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/translate", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Unsupported target language" in response.json()["detail"]


def test_synthesize_speech_mock(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "text": "Your resting heart rate is normal.",
        "language_code": "te",
        "voice_gender": "female",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/synthesize", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()

    assert res["is_mock"] is True
    assert res["is_playable"] is False
    assert res["provider"] == "mock_development"
    assert res["language_code"] == "te"
    assert res["disclaimer"] == MOCK_TTS_DISCLAIMER
    assert len(res["audio_payload"]) > 0


def test_voice_consent_update_and_query(client, patient_token, test_patient_user):
    headers = {"Authorization": f"Bearer {patient_token}"}

    # 1. Initial query before affirmative update
    get_res = client.get("/api/v1/voice/consent", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["consent_granted"] is False

    # 2. Update consent to True
    payload = {
        "consent_granted": True,
        "audio_retention_permitted": False
    }
    post_res = client.post("/api/v1/voice/consent", json=payload, headers=headers)
    assert post_res.status_code == 200
    assert post_res.json()["consent_granted"] is True

    # 3. Query again, confirms persistent true
    get_res2 = client.get("/api/v1/voice/consent", headers=headers)
    assert get_res2.status_code == 200
    assert get_res2.json()["consent_granted"] is True

    # 4. Now transcribe can succeed without request-level consent_confirmed=True
    req_payload = {
        "audio_base64": base64.b64encode(make_synthetic_wav(2.0)).decode("utf-8"),
        "language_hint": "en",
        "consent_confirmed": False  # user has persistent consent granted in DB
    }
    tx_res = client.post("/api/v1/voice/transcribe", json=req_payload, headers=headers)
    assert tx_res.status_code == 200


def test_voice_audit_logging_recorded(client, patient_token, test_patient_user, db_session):
    headers = {"Authorization": f"Bearer {patient_token}"}

    # Execute a translation
    payload = {
        "text": "Testing audit",
        "source_language": "en",
        "target_language": "kn",
        "consent_confirmed": True
    }
    client.post("/api/v1/voice/translate", json=payload, headers=headers)

    # Check database
    audit = db_session.query(VoiceAuditLog).filter(
        VoiceAuditLog.user_id == test_patient_user.id,
        VoiceAuditLog.operation_type == "translation"
    ).first()
    assert audit is not None
    assert audit.is_mock is True
    assert audit.provider == "mock_development"


def test_draft_emergency_dictionary_lookup():
    # Test all 7 languages return draft phrase
    for lang in SUPPORTED_LANGUAGE_CODES:
        phrase = get_draft_emergency_phrase("EMERGENCY_TRIGGERED", lang)
        assert len(phrase) > 0
        assert isinstance(phrase, str)


def test_voice_endpoints_unauthorized_without_jwt(client):
    res1 = client.get("/api/v1/voice/languages")
    assert res1.status_code == 401

    res2 = client.post("/api/v1/voice/transcribe", json={})
    assert res2.status_code == 401

    res3 = client.post("/api/v1/voice/translate", json={})
    assert res3.status_code == 401


# =============================================================================
# Stage 2B.1: Real STT Audio Input Validation Tests
# =============================================================================

def test_transcribe_audio_validation_missing_payload(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_format": "audio/wav",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Audio payload is required and cannot be empty." in response.json()["detail"]


def test_transcribe_audio_validation_invalid_base64(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": "!!!not_valid_base64_string!!!",
        "audio_format": "audio/wav",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Invalid base64 encoding" in response.json()["detail"]


def test_transcribe_audio_validation_empty_bytes(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(b"").decode("utf-8"),
        "audio_format": "audio/wav",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Audio payload is required and cannot be empty." in response.json()["detail"] or "empty" in response.json()["detail"]


def test_transcribe_audio_validation_unsupported_mime_type(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(b"dummy_audio_bytes").decode("utf-8"),
        "audio_format": "video/mp4",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Unsupported audio MIME type" in response.json()["detail"]


def test_transcribe_audio_validation_oversized_payload_returns_413(client, patient_token, monkeypatch):
    from app.core.config import settings
    # Set maximum limit to 100 bytes for deterministic test execution
    monkeypatch.setattr(settings, "VOICE_MAX_AUDIO_SIZE_BYTES", 100)

    headers = {"Authorization": f"Bearer {patient_token}"}
    oversized_data = b"X" * 150
    payload = {
        "audio_base64": base64.b64encode(oversized_data).decode("utf-8"),
        "audio_format": "audio/wav",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 413
    assert "exceeds the maximum allowed limit" in response.json()["detail"]


# =============================================================================
# Stage 2B.1: FasterWhisperSTTAdapter Unit Tests
# =============================================================================

def test_faster_whisper_adapter_uninstalled_raises_runtime_error(monkeypatch):
    import sys
    from app.services.voice.adapters.whisper_adapter import FasterWhisperSTTAdapter

    adapter = FasterWhisperSTTAdapter(model_size="tiny", device="cpu", compute_type="int8")

    # Simulate faster_whisper not installed
    with pytest.raises(RuntimeError) as exc_info:
        adapter.transcribe(b"dummy_audio_data")

    assert "faster-whisper is not installed" in str(exc_info.value)


def test_faster_whisper_adapter_empty_audio_raises_value_error():
    from app.services.voice.adapters.whisper_adapter import FasterWhisperSTTAdapter
    adapter = FasterWhisperSTTAdapter()

    with pytest.raises(ValueError) as exc_info:
        adapter.transcribe(b"")
    assert "Audio payload cannot be empty." in str(exc_info.value)


def test_faster_whisper_adapter_transcription_supported_language(monkeypatch):
    from unittest.mock import MagicMock
    from app.services.voice.adapters.whisper_adapter import FasterWhisperSTTAdapter
    from app.schemas.voice import REAL_STT_DISCLAIMER

    adapter = FasterWhisperSTTAdapter()

    # Mock the internal model
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "ನನ್ನ ಹೃದಯ ಬಡಿತ ಹೆಚ್ಚಾಗಿದೆ"
    mock_segment.no_speech_prob = 0.05
    mock_segment.avg_logprob = -0.3

    mock_info = MagicMock()
    mock_info.language = "kn"
    mock_info.language_probability = 0.98

    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    monkeypatch.setattr(adapter, "_get_model", lambda: mock_model)

    result = adapter.transcribe(b"mock_kannada_audio_bytes", hint_language="kn")

    assert result.is_mock is False
    assert result.provider == "local_whisper"
    assert result.detected_language == "kn"
    assert result.transcript == "ನನ್ನ ಹೃದಯ ಬಡಿತ ಹೆಚ್ಚಾಗಿದೆ"
    assert result.confidence is None  # Uncalibrated confidence represented as None
    assert result.uncertain_speech is False
    assert result.disclaimer == REAL_STT_DISCLAIMER


def test_faster_whisper_adapter_transcription_unsupported_language_marked_uncertain(monkeypatch):
    from unittest.mock import MagicMock
    from app.services.voice.adapters.whisper_adapter import FasterWhisperSTTAdapter

    adapter = FasterWhisperSTTAdapter()

    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "Bonjour, j'ai mal au coeur"
    mock_segment.no_speech_prob = 0.05

    mock_info = MagicMock()
    mock_info.language = "fr"  # French is not in the 7 supported Indic/English languages
    mock_info.language_probability = 0.95

    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    monkeypatch.setattr(adapter, "_get_model", lambda: mock_model)

    result = adapter.transcribe(b"mock_french_audio_bytes")

    assert result.detected_language == "unsupported"
    assert result.uncertain_speech is True
    assert result.confidence is None


def test_faster_whisper_adapter_transcription_low_probability_marked_uncertain(monkeypatch):
    from unittest.mock import MagicMock
    from app.services.voice.adapters.whisper_adapter import FasterWhisperSTTAdapter

    adapter = FasterWhisperSTTAdapter()

    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "muffled sound"
    mock_segment.no_speech_prob = 0.40

    mock_info = MagicMock()
    mock_info.language = "hi"
    mock_info.language_probability = 0.35  # Below VOICE_LANGUAGE_CONFIDENCE_THRESHOLD (0.50)

    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    monkeypatch.setattr(adapter, "_get_model", lambda: mock_model)

    result = adapter.transcribe(b"mock_noisy_audio_bytes")

    assert result.detected_language == "hi"
    assert result.uncertain_speech is True
    assert result.confidence is None


# =============================================================================
# Stage 2B.1: HostedWhisperSTTAdapter Unit Tests
# =============================================================================

def test_hosted_whisper_adapter_missing_key_raises_runtime_error():
    from app.services.voice.adapters.whisper_adapter import HostedWhisperSTTAdapter
    adapter = HostedWhisperSTTAdapter(api_key=None)

    with pytest.raises(RuntimeError) as exc_info:
        adapter.transcribe(b"sample_audio")
    assert "OPENAI_API_KEY is not configured" in str(exc_info.value)


def test_hosted_whisper_adapter_empty_audio_raises_value_error():
    from app.services.voice.adapters.whisper_adapter import HostedWhisperSTTAdapter
    adapter = HostedWhisperSTTAdapter(api_key="sk-test-key-12345")

    with pytest.raises(ValueError) as exc_info:
        adapter.transcribe(b"")
    assert "Audio payload cannot be empty." in str(exc_info.value)


def test_hosted_whisper_adapter_transcription_success(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.whisper_adapter import HostedWhisperSTTAdapter
    from app.schemas.voice import REAL_STT_DISCLAIMER

    adapter = HostedWhisperSTTAdapter(api_key="sk-test-key-mock")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "मुझे चक्कर आ रहे हैं",
        "language": "hi",
        "duration": 2.5
    }

    mock_client_instance = MagicMock()
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_client_instance.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_instance)

    result = adapter.transcribe(b"mock_hindi_audio", content_type="audio/wav", hint_language="hi")

    assert result.is_mock is False
    assert result.provider == "hosted_whisper"
    assert result.detected_language == "hi"
    assert result.transcript == "मुझे चक्कर आ रहे हैं"
    assert result.confidence is None
    assert result.uncertain_speech is False
    assert result.disclaimer == REAL_STT_DISCLAIMER


def test_hosted_whisper_adapter_transcription_unsupported_language(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.whisper_adapter import HostedWhisperSTTAdapter

    adapter = HostedWhisperSTTAdapter(api_key="sk-test-key-mock")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "Hola me siento mal",
        "language": "es",  # Spanish is not in 7 supported Indic/English languages
        "duration": 2.1
    }

    mock_client_instance = MagicMock()
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_client_instance.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_instance)

    result = adapter.transcribe(b"mock_spanish_audio")

    assert result.detected_language == "unsupported"
    assert result.uncertain_speech is True
    assert result.confidence is None


def test_hosted_whisper_adapter_transcription_401_unauthorized(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.whisper_adapter import HostedWhisperSTTAdapter

    adapter = HostedWhisperSTTAdapter(api_key="sk-invalid-secret-key-123")

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Incorrect API key provided"

    mock_client_instance = MagicMock()
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_client_instance.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_instance)

    with pytest.raises(RuntimeError) as exc_info:
        adapter.transcribe(b"audio_bytes")

    # Ensure secret key is NEVER leaked in error message
    assert "sk-invalid-secret-key-123" not in str(exc_info.value)
    assert "Invalid API credentials" in str(exc_info.value)


def test_hosted_whisper_adapter_transcription_429_rate_limit(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.whisper_adapter import HostedWhisperSTTAdapter

    adapter = HostedWhisperSTTAdapter(api_key="sk-test-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "Rate limit reached"

    mock_client_instance = MagicMock()
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_client_instance.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_instance)

    with pytest.raises(RuntimeError) as exc_info:
        adapter.transcribe(b"audio_bytes")
    assert "rate limit or quota exceeded" in str(exc_info.value)


def test_hosted_whisper_adapter_transcription_timeout(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.whisper_adapter import HostedWhisperSTTAdapter

    adapter = HostedWhisperSTTAdapter(api_key="sk-test-key")

    mock_client_instance = MagicMock()
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_client_instance.post.side_effect = httpx.TimeoutException("Read timed out")

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_instance)

    with pytest.raises(TimeoutError) as exc_info:
        adapter.transcribe(b"audio_bytes")
    assert "timed out" in str(exc_info.value)


# =============================================================================
# Stage 2B.1: STT Provider Factory & Integration Tests
# =============================================================================

def test_stt_provider_factory_selection_and_reset(monkeypatch):
    from app.core.config import settings
    from app.services.voice.adapters import (
        FasterWhisperSTTAdapter,
        HostedWhisperSTTAdapter,
        MockSTTAdapter,
        get_stt_adapter,
        reset_adapters,
    )

    # 1. Default mock
    monkeypatch.setattr(settings, "VOICE_STT_PROVIDER", "mock_development")
    reset_adapters()
    adapter1 = get_stt_adapter()
    assert isinstance(adapter1, MockSTTAdapter)

    # 2. Local Whisper
    monkeypatch.setattr(settings, "VOICE_STT_PROVIDER", "local_whisper")
    reset_adapters()
    adapter2 = get_stt_adapter()
    assert isinstance(adapter2, FasterWhisperSTTAdapter)

    # 3. Hosted Whisper
    monkeypatch.setattr(settings, "VOICE_STT_PROVIDER", "hosted_whisper")
    reset_adapters()
    adapter3 = get_stt_adapter()
    assert isinstance(adapter3, HostedWhisperSTTAdapter)

    # Reset back to mock for subsequent test safety
    reset_adapters()


def test_transcribe_endpoint_with_hosted_whisper_mocked(client, patient_token, monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.core.config import settings
    from app.schemas.voice import REAL_STT_DISCLAIMER
    from app.services.voice.adapters import reset_adapters

    monkeypatch.setattr(settings, "VOICE_STT_PROVIDER", "hosted_whisper")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-live-mocked-test-key")
    reset_adapters()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "मुझे सांस लेने में तकलीफ है",
        "language": "hi",
        "duration": 3.2
    }

    mock_client_instance = MagicMock()
    mock_client_instance.__enter__.return_value = mock_client_instance
    mock_client_instance.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_instance)

    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(make_synthetic_wav(3.2)).decode("utf-8"),
        "audio_format": "audio/wav",
        "language_hint": "hi",
        "consent_confirmed": True
    }

    try:
        response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["is_mock"] is False
        assert data["provider"] == "hosted_whisper"
        assert data["detected_language"] == "hi"
        assert data["transcript"] == "मुझे सांस लेने में तकलीफ है"
        assert data["confidence"] is None  # Confirms uncalibrated confidence returns null
        assert data["uncertain_speech"] is False
        assert data["disclaimer"] == REAL_STT_DISCLAIMER
    finally:
        reset_adapters()


# =============================================================================
# Stage 2B.1 Focused Correction: Pre-Transcription Audio Duration Validation Tests
# =============================================================================

def test_transcribe_valid_wav_duration_success(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(make_synthetic_wav(duration_seconds=2.5)).decode("utf-8"),
        "audio_format": "audio/wav",
        "language_hint": "kn",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["detected_language"] == "kn"
    assert "Simulated Audio Transcription" in data["transcript"]


def test_transcribe_audio_exceeding_duration_limit_returns_413(client, patient_token, monkeypatch):
    from app.core.config import settings
    # Set limit to 3.0 seconds for deterministic verification
    monkeypatch.setattr(settings, "VOICE_MAX_AUDIO_DURATION_SECONDS", 3.0)

    headers = {"Authorization": f"Bearer {patient_token}"}
    # Payload duration is 5.0s, exceeding the 3.0s limit
    payload = {
        "audio_base64": base64.b64encode(make_synthetic_wav(duration_seconds=5.0)).decode("utf-8"),
        "audio_format": "audio/wav",
        "language_hint": "en",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 413
    detail = response.json()["detail"]
    assert "exceeds the maximum allowed limit of 3.0 seconds" in detail
    assert "5.00s" in detail


def test_transcribe_malformed_wav_returns_400(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    # Corrupt WAV bytes with truncated/broken RIFF header
    corrupt_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00corrupted_data_not_pcm"
    payload = {
        "audio_base64": base64.b64encode(corrupt_wav).decode("utf-8"),
        "audio_format": "audio/wav",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Audio validation failed" in response.json()["detail"]


def test_transcribe_compressed_audio_mp3_duration_success(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(make_synthetic_mp3(frames_count=40)).decode("utf-8"),
        "audio_format": "audio/mp3",
        "language_hint": "hi",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["detected_language"] == "hi"


def test_transcribe_compressed_audio_flac_duration_success(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(make_synthetic_flac(duration_seconds=2.0)).decode("utf-8"),
        "audio_format": "audio/flac",
        "language_hint": "te",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["detected_language"] == "te"


def test_transcribe_compressed_audio_m4a_duration_success(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(make_synthetic_m4a(duration_seconds=3.5)).decode("utf-8"),
        "audio_format": "audio/x-m4a",
        "language_hint": "ta",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["detected_language"] == "ta"


def test_transcribe_compressed_audio_webm_duration_success(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "audio_base64": base64.b64encode(make_synthetic_webm(duration_seconds=4.0)).decode("utf-8"),
        "audio_format": "audio/webm",
        "language_hint": "ur",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["detected_language"] == "ur"


def test_transcribe_missing_or_unparseable_duration_returns_400(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    # WebM header without Duration tag
    broken_webm = b"\x1a\x45\xdf\xa3\x01\x00\x00\x00\x00\x00\x00\x00no_duration_tag_here"
    payload = {
        "audio_base64": base64.b64encode(broken_webm).decode("utf-8"),
        "audio_format": "audio/webm",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/transcribe", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Audio validation failed" in response.json()["detail"]


def test_rejected_audio_never_reaches_stt_adapter(client, patient_token, monkeypatch):
    from unittest.mock import MagicMock
    from app.core.config import settings
    from app.services.voice import adapters

    # Spy on stt_adapter.transcribe
    active_adapter = adapters.get_stt_adapter()
    mock_transcribe = MagicMock()
    monkeypatch.setattr(active_adapter, "transcribe", mock_transcribe)

    # 1. Test duration exceeding rejection
    monkeypatch.setattr(settings, "VOICE_MAX_AUDIO_DURATION_SECONDS", 2.0)
    headers = {"Authorization": f"Bearer {patient_token}"}
    oversized_payload = {
        "audio_base64": base64.b64encode(make_synthetic_wav(duration_seconds=4.0)).decode("utf-8"),
        "audio_format": "audio/wav",
        "consent_confirmed": True
    }
    res1 = client.post("/api/v1/voice/transcribe", json=oversized_payload, headers=headers)
    assert res1.status_code == 413
    assert mock_transcribe.call_count == 0  # Rejection happened BEFORE reaching adapter

    # 2. Test malformed audio rejection
    malformed_payload = {
        "audio_base64": base64.b64encode(b"completely_broken_unparseable_bytes").decode("utf-8"),
        "audio_format": "audio/wav",
        "consent_confirmed": True
    }
    res2 = client.post("/api/v1/voice/transcribe", json=malformed_payload, headers=headers)
    assert res2.status_code == 400
    assert mock_transcribe.call_count == 0  # Still zero calls to STT adapter


# =============================================================================
# Stage 2B.2: Real Multilingual Translation Tests
# =============================================================================

def test_detect_script_language_best_effort():
    from app.services.voice.adapters.translation_adapter import detect_script_language

    # 1. Clear Dravidian scripts (low ambiguity)
    kn_text = "ನನ್ನ ಎದೆ ಬಡಿತ ಹೆಚ್ಚಾಗಿದೆ"
    lang, uncertain = detect_script_language(kn_text)
    assert lang == "kn"
    assert uncertain is False

    ml_text = "എനിക്ക് ശ്വാസം മുട്ടൽ അനുഭവപ്പെടുന്നു"
    lang, uncertain = detect_script_language(ml_text)
    assert lang == "ml"
    assert uncertain is False

    ta_text = "எனக்கு நெஞ்சு வலி இருக்கிறது"
    lang, uncertain = detect_script_language(ta_text)
    assert lang == "ta"
    assert uncertain is False

    te_text = "నాకు గుండె వేగంగా కొట్టుకుంటోంది"
    lang, uncertain = detect_script_language(te_text)
    assert lang == "te"
    assert uncertain is False

    # 2. Devanagari script (ambiguous between Hindi, Marathi, Nepali - flagged uncertain)
    hi_text = "मुझे सांस लेने में तकलीफ हो रही है"
    lang, uncertain = detect_script_language(hi_text)
    assert lang == "hi"
    assert uncertain is True

    # 3. Perso-Arabic script (ambiguous between Urdu, Arabic, Persian, Kashmiri - flagged uncertain)
    ur_text = "مجھے سینے میں درد محسوس ہو رہا ہے"
    lang, uncertain = detect_script_language(ur_text)
    assert lang == "ur"
    assert uncertain is True

    # 4. Latin script (ambiguous between English, Spanish, French, transliteration - flagged uncertain)
    en_text = "I am experiencing severe chest pressure"
    lang, uncertain = detect_script_language(en_text)
    assert lang == "en"
    assert uncertain is True

    # 5. Mixed, numeric, or unresolvable script
    mixed_text = "12345 !@#$%"
    lang, uncertain = detect_script_language(mixed_text)
    assert lang is None or lang == "uncertain"
    assert uncertain is True


def test_translate_input_validation_empty_text_returns_400(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "text": "   ",
        "target_language": "hi",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/translate", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Translation source text cannot be empty" in response.json()["detail"]


def test_translate_input_validation_oversized_text_returns_400(client, patient_token, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "VOICE_MAX_TRANSLATION_CHARS", 100)

    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "text": "A" * 150,
        "target_language": "kn",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/translate", json=payload, headers=headers)
    assert response.status_code == 400
    assert "exceeds maximum limit" in response.json()["detail"]


def test_translate_unsupported_source_language_returns_400(client, patient_token):
    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "text": "Bonjour",
        "source_language": "fr",  # French unsupported
        "target_language": "en",
        "consent_confirmed": True
    }
    response = client.post("/api/v1/voice/translate", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Unsupported source language" in response.json()["detail"]


def test_hosted_translation_missing_key_raises_runtime_error():
    from app.services.voice.adapters.translation_adapter import HostedTranslationAdapter
    adapter = HostedTranslationAdapter(api_key=None)

    with pytest.raises(RuntimeError) as exc_info:
        adapter.translate("Hello", "en", "hi")
    assert "TRANSLATION_API_KEY (or OPENAI_API_KEY) is not configured" in str(exc_info.value)


def test_hosted_translation_success_all_seven_languages(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.translation_adapter import HostedTranslationAdapter
    from app.schemas.voice import REAL_TRANSLATION_DISCLAIMER

    adapter = HostedTranslationAdapter(api_key="sk-test-translation-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "ನನ್ನ ಹೃದಯ ಬಡಿತ ವೇಗವಾಗಿದೆ"}}]
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    # Test all 7 target languages
    test_targets = ["kn", "en", "hi", "ml", "ta", "te", "ur"]
    for tgt in test_targets:
        res = adapter.translate("My heart rate is elevated", source_language="en", target_language=tgt)
        assert res.is_mock is False
        assert res.provider == "hosted_translation"
        assert res.target_language == tgt
        assert res.confidence is None  # Uncalibrated confidence strictly None
        assert res.disclaimer == REAL_TRANSLATION_DISCLAIMER
        assert res.uncertain_translation is False


def test_hosted_translation_auto_detect_uncertain_source_flag(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.translation_adapter import HostedTranslationAdapter

    adapter = HostedTranslationAdapter(api_key="sk-test-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "मुझे सिरदर्द है"}}]
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    # Latin text with source_language=None should set uncertain_translation=True
    res = adapter.translate("I have a headache", source_language=None, target_language="hi")
    assert res.source_language == "en"
    assert res.uncertain_translation is True  # Latin script flagged as uncertain English


def test_hosted_translation_identity_passthrough():
    from app.services.voice.adapters.translation_adapter import HostedTranslationAdapter
    adapter = HostedTranslationAdapter(api_key="sk-test-key")

    res = adapter.translate("Hello world", source_language="en", target_language="en")
    assert res.translated_text == "Hello world"
    assert res.confidence is None
    assert res.uncertain_translation is False


def test_hosted_translation_errors_mapped_properly(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.translation_adapter import HostedTranslationAdapter

    adapter = HostedTranslationAdapter(api_key="sk-test-key-sensitive-123")

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client

    # 1. 401 Unauthorized -> RuntimeError without key leakage
    resp_401 = MagicMock(status_code=401)
    mock_client.post.return_value = resp_401
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    with pytest.raises(RuntimeError) as exc401:
        adapter.translate("Test text", "en", "kn")
    assert "sk-test-key-sensitive-123" not in str(exc401.value)
    assert "authentication failed" in str(exc401.value)

    # 2. 429 Rate limit -> RuntimeError
    resp_429 = MagicMock(status_code=429)
    mock_client.post.return_value = resp_429
    with pytest.raises(RuntimeError) as exc429:
        adapter.translate("Test text", "en", "kn")
    assert "rate limit or quota exceeded" in str(exc429.value)

    # 3. Timeout -> TimeoutError
    mock_client.post.side_effect = httpx.TimeoutException("Read timeout")
    with pytest.raises(TimeoutError) as excto:
        adapter.translate("Test text", "en", "kn")
    assert "timed out" in str(excto.value)

    # 4. Network error -> ConnectionError
    mock_client.post.side_effect = httpx.ConnectError("Connection refused")
    with pytest.raises(ConnectionError) as excconn:
        adapter.translate("Test text", "en", "kn")
    assert "Network error" in str(excconn.value)


def test_indictrans2_adapter_uninstalled_raises_runtime_error():
    from app.services.voice.adapters.translation_adapter import IndicTrans2TranslationAdapter
    adapter = IndicTrans2TranslationAdapter()

    with pytest.raises(RuntimeError) as exc_info:
        adapter.translate("ನನ್ನ ಎದೆ ನೋಯುತ್ತಿದೆ", source_language="kn", target_language="en")
    assert "IndicTrans2 dependencies (torch, transformers) are not installed" in str(exc_info.value)


def test_indictrans2_direction_validation():
    from app.services.voice.adapters.translation_adapter import IndicTrans2TranslationAdapter
    adapter = IndicTrans2TranslationAdapter()

    assert adapter._get_direction("hi", "en") == "indic-en"
    assert adapter._get_direction("en", "ta") == "en-indic"
    assert adapter._get_direction("kn", "te") == "indic-indic"

    with pytest.raises(ValueError) as exc:
        adapter._get_direction("fr", "en")
    assert "not supported" in str(exc.value)


def test_translation_provider_factory_selection_and_reset(monkeypatch):
    from app.core.config import settings
    from app.services.voice.adapters import (
        HostedTranslationAdapter,
        IndicTrans2TranslationAdapter,
        MockTranslationAdapter,
        get_translation_adapter,
        reset_adapters,
    )

    # 1. Default mock
    monkeypatch.setattr(settings, "VOICE_TRANSLATION_PROVIDER", "mock_development")
    reset_adapters()
    a1 = get_translation_adapter()
    assert isinstance(a1, MockTranslationAdapter)

    # 2. Hosted translation
    monkeypatch.setattr(settings, "VOICE_TRANSLATION_PROVIDER", "hosted_translation")
    reset_adapters()
    a2 = get_translation_adapter()
    assert isinstance(a2, HostedTranslationAdapter)

    # 3. Local IndicTrans2
    monkeypatch.setattr(settings, "VOICE_TRANSLATION_PROVIDER", "local_indictrans")
    reset_adapters()
    a3 = get_translation_adapter()
    assert isinstance(a3, IndicTrans2TranslationAdapter)

    reset_adapters()


def test_translate_endpoint_with_hosted_provider_mocked(client, patient_token, monkeypatch, db_session, test_patient_user):
    from unittest.mock import MagicMock
    import httpx
    from app.core.config import settings
    from app.models.voice import VoiceAuditLog
    from app.schemas.voice import REAL_TRANSLATION_DISCLAIMER
    from app.services.voice.adapters import reset_adapters

    monkeypatch.setattr(settings, "VOICE_TRANSLATION_PROVIDER", "hosted_translation")
    monkeypatch.setattr(settings, "TRANSLATION_API_KEY", "sk-test-live-mock-key")
    reset_adapters()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "నాకు రక్తపోటు ఎక్కువగా ఉంది"}}]
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "text": "My blood pressure is high",
        "source_language": "en",
        "target_language": "te",
        "consent_confirmed": True
    }

    try:
        response = client.post("/api/v1/voice/translate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["is_mock"] is False
        assert data["provider"] == "hosted_translation"
        assert data["source_language"] == "en"
        assert data["target_language"] == "te"
        assert data["translated_text"] == "నాకు రక్తపోటు ఎక్కువగా ఉంది"
        assert data["confidence"] is None  # Uncalibrated confidence returns null
        assert data["uncertain_translation"] is False
        assert data["disclaimer"] == REAL_TRANSLATION_DISCLAIMER

        # Verify audit log recorded character counts without sensitive text
        audit = db_session.query(VoiceAuditLog).filter(
            VoiceAuditLog.user_id == test_patient_user.id,
            VoiceAuditLog.operation_type == "translation",
            VoiceAuditLog.provider == "hosted_translation"
        ).first()
        assert audit is not None
        assert audit.input_character_count == len("My blood pressure is high")
        assert audit.output_character_count == len("నాకు రక్తపోటు ఎక్కువగా ఉంది")
        assert audit.is_mock is False
    finally:
        reset_adapters()


# =============================================================================
# Stage 2B.3: Real Multilingual Text-to-Speech (TTS) Tests
# =============================================================================

def test_hosted_tts_missing_key_raises_runtime_error(monkeypatch):
    from app.core.config import settings
    from app.services.voice.adapters.tts_adapter import HostedOpenAITTSAdapter

    monkeypatch.setattr(settings, "TTS_API_KEY", None)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)

    adapter = HostedOpenAITTSAdapter()
    with pytest.raises(RuntimeError) as exc_info:
        adapter.synthesize(
            text="Your vitals are within normal range.",
            language_code="en"
        )
    assert "TTS_API_KEY (or OPENAI_API_KEY) is not configured" in str(exc_info.value)


def test_hosted_tts_input_validation():
    from app.services.voice.adapters.tts_adapter import HostedOpenAITTSAdapter

    adapter = HostedOpenAITTSAdapter(api_key="sk-test-mock-key")

    # 1. Empty text
    with pytest.raises(ValueError, match="Text to synthesize cannot be empty"):
        adapter.synthesize(text="   ", language_code="en")

    # 2. Text exceeds 2000 chars
    long_text = "Heart rate stable. " * 150
    with pytest.raises(ValueError, match="exceeds maximum limit"):
        adapter.synthesize(text=long_text, language_code="en")

    # 3. Unsupported language code
    with pytest.raises(ValueError, match="Unsupported language code"):
        adapter.synthesize(text="Hello", language_code="es")

    # 4. Unsupported audio format
    with pytest.raises(ValueError, match="Unsupported audio format"):
        adapter.synthesize(text="Hello", language_code="en", audio_format="audio/midi")

    # 5. Invalid voice identifier
    with pytest.raises(ValueError, match="Invalid voice identifier"):
        adapter.synthesize(text="Hello", language_code="en", voice_gender="unknown_voice")


def test_hosted_tts_success_all_seven_languages(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.tts_adapter import HostedOpenAITTSAdapter

    sample_phrases = {
        "kn": "ನಿಮ್ಮ ನಾಡಿಮಿಡಿತ ಸಾಮಾನ್ಯವಾಗಿದೆ.",
        "en": "Your pulse is normal.",
        "hi": "आपकी नाड़ी सामान्य है।",
        "ml": "നിങ്ങളുടെ നാഡിമിടിപ്പ് സാധാരണമാണ്.",
        "ta": "உங்கள் நாடித்துடிப்பு சாதாரணமாக உள்ளது.",
        "te": "మీ నాడి సాధారణంగా ఉంది.",
        "ur": "آپ کی نبض معمول کے مطابق ہے۔",
    }

    dummy_audio_bytes = b"\xff\xfb\x90\x64" + b"\x00" * 200  # simulated mp3 audio bytes

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = dummy_audio_bytes

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    adapter = HostedOpenAITTSAdapter(api_key="sk-test-live-key")

    for lang, phrase in sample_phrases.items():
        result = adapter.synthesize(
            text=phrase,
            language_code=lang,
            voice_gender="female",
            audio_format="audio/mp3",
        )
        assert result.language_code == lang
        assert result.is_mock is False
        assert result.is_playable is True
        assert result.provider == "hosted_tts"
        assert result.disclaimer == REAL_TTS_DISCLAIMER
        assert result.audio_format == "audio/mp3"

        decoded = base64.b64decode(result.audio_payload)
        assert decoded == dummy_audio_bytes


def test_hosted_tts_voice_and_format_mappings(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.tts_adapter import HostedOpenAITTSAdapter

    captured_requests = []

    def mock_post(url, headers, json):
        captured_requests.append({"url": url, "headers": headers, "json": json})
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"AUDIO_DATA"
        return resp

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.side_effect = mock_post

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    adapter = HostedOpenAITTSAdapter(api_key="sk-test-key")

    # Test voice gender mapping
    adapter.synthesize("Test", "en", voice_gender="female")
    assert captured_requests[-1]["json"]["voice"] == "nova"

    adapter.synthesize("Test", "en", voice_gender="male")
    assert captured_requests[-1]["json"]["voice"] == "onyx"

    adapter.synthesize("Test", "en", voice_gender="neutral")
    assert captured_requests[-1]["json"]["voice"] == "alloy"

    adapter.synthesize("Test", "en", voice_gender="shimmer")
    assert captured_requests[-1]["json"]["voice"] == "shimmer"

    # Test format mapping
    adapter.synthesize("Test", "en", audio_format="audio/wav")
    assert captured_requests[-1]["json"]["response_format"] == "wav"

    adapter.synthesize("Test", "en", audio_format="audio/ogg")
    assert captured_requests[-1]["json"]["response_format"] == "opus"

    adapter.synthesize("Test", "en", audio_format="audio/aac")
    assert captured_requests[-1]["json"]["response_format"] == "aac"

    adapter.synthesize("Test", "en", audio_format="audio/flac")
    assert captured_requests[-1]["json"]["response_format"] == "flac"


def test_hosted_tts_errors_mapped_properly(monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.services.voice.adapters.tts_adapter import HostedOpenAITTSAdapter

    # 1. 401 Unauthorized
    mock_resp_401 = MagicMock(status_code=401)
    mock_client_401 = MagicMock()
    mock_client_401.__enter__.return_value = mock_client_401
    mock_client_401.post.return_value = mock_resp_401
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_401)

    adapter = HostedOpenAITTSAdapter(api_key="sk-test-key")
    with pytest.raises(RuntimeError, match="Hosted TTS authentication failed"):
        adapter.synthesize("Hello", "en")

    # 2. 429 Rate limit
    mock_resp_429 = MagicMock(status_code=429)
    mock_client_429 = MagicMock()
    mock_client_429.__enter__.return_value = mock_client_429
    mock_client_429.post.return_value = mock_resp_429
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_429)

    with pytest.raises(RuntimeError, match="Hosted TTS rate limit"):
        adapter.synthesize("Hello", "en")

    # 3. 500 Provider error
    mock_resp_500 = MagicMock(status_code=500)
    mock_client_500 = MagicMock()
    mock_client_500.__enter__.return_value = mock_client_500
    mock_client_500.post.return_value = mock_resp_500
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_500)

    with pytest.raises(ConnectionError, match="Hosted TTS provider error with status 500"):
        adapter.synthesize("Hello", "en")

    # 4. Timeout
    def mock_timeout(*args, **kwargs):
        raise httpx.TimeoutException("Connection timed out")

    mock_client_to = MagicMock()
    mock_client_to.__enter__.return_value = mock_client_to
    mock_client_to.post.side_effect = mock_timeout
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_to)

    with pytest.raises(TimeoutError, match="Hosted TTS synthesis service timed out"):
        adapter.synthesize("Hello", "en")

    # 5. Network Request Error
    def mock_net_err(*args, **kwargs):
        raise httpx.RequestError("Network is unreachable")

    mock_client_ne = MagicMock()
    mock_client_ne.__enter__.return_value = mock_client_ne
    mock_client_ne.post.side_effect = mock_net_err
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_ne)

    with pytest.raises(ConnectionError, match="Network error communicating with TTS provider"):
        adapter.synthesize("Hello", "en")

    # 6. Empty audio content returned
    mock_resp_empty = MagicMock(status_code=200, content=b"")
    mock_client_empty = MagicMock()
    mock_client_empty.__enter__.return_value = mock_client_empty
    mock_client_empty.post.return_value = mock_resp_empty
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_empty)

    with pytest.raises(RuntimeError, match="Received empty audio response from TTS provider"):
        adapter.synthesize("Hello", "en")


def test_local_tts_adapter():
    from app.services.voice.adapters.tts_adapter import LocalTTSAdapter

    adapter = LocalTTSAdapter()

    # Empty text check
    with pytest.raises(ValueError, match="Text to synthesize cannot be empty"):
        adapter.synthesize("  ", "en")

    # Unsupported language
    with pytest.raises(ValueError, match="Unsupported language code"):
        adapter.synthesize("Hello", "es")

    # Missing local engine dependencies
    with pytest.raises(RuntimeError, match="Local TTS engine dependencies are not installed"):
        adapter.synthesize("Hello", "en")


def test_tts_provider_factory_selection_and_reset(monkeypatch):
    from app.core.config import settings
    from app.services.voice.adapters import (
        HostedOpenAITTSAdapter,
        LocalTTSAdapter,
        MockTTSAdapter,
        get_tts_adapter,
        reset_adapters,
    )

    # 1. Default mock
    monkeypatch.setattr(settings, "VOICE_TTS_PROVIDER", "mock_development")
    reset_adapters()
    a1 = get_tts_adapter()
    assert isinstance(a1, MockTTSAdapter)

    # 2. Hosted TTS
    monkeypatch.setattr(settings, "VOICE_TTS_PROVIDER", "hosted_tts")
    reset_adapters()
    a2 = get_tts_adapter()
    assert isinstance(a2, HostedOpenAITTSAdapter)

    # 3. Local TTS
    monkeypatch.setattr(settings, "VOICE_TTS_PROVIDER", "local_tts")
    reset_adapters()
    a3 = get_tts_adapter()
    assert isinstance(a3, LocalTTSAdapter)

    reset_adapters()


def test_synthesize_input_validation_errors(client, patient_token, monkeypatch):
    from app.core.config import settings
    headers = {"Authorization": f"Bearer {patient_token}"}

    # 1. Empty text
    res = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "   ", "language_code": "en", "consent_confirmed": True},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Text to synthesize cannot be empty" in res.json()["detail"]

    # 2. Excessive text exceeding configured maximum limit
    monkeypatch.setattr(settings, "VOICE_MAX_TTS_CHARS", 50)
    res = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "X" * 60, "language_code": "en", "consent_confirmed": True},
        headers=headers,
    )
    assert res.status_code == 400
    assert "exceeds maximum limit" in res.json()["detail"]

    # 3. Unsupported language code
    res = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Hello", "language_code": "fr", "consent_confirmed": True},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Unsupported language code" in res.json()["detail"]

    # 4. Unsupported audio format
    res = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Hello", "language_code": "en", "audio_format": "audio/midi", "consent_confirmed": True},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Unsupported audio format" in res.json()["detail"]

    # 5. Invalid voice gender
    res = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Hello", "language_code": "en", "voice_gender": "robot", "consent_confirmed": True},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Invalid voice identifier" in res.json()["detail"]

    # 6. Without consent
    res = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Hello", "language_code": "en", "consent_confirmed": False},
        headers=headers,
    )
    assert res.status_code == 403
    assert "Consent required" in res.json()["detail"]


def test_synthesize_endpoint_with_hosted_provider_mocked(client, patient_token, monkeypatch, db_session, test_patient_user):
    from unittest.mock import MagicMock
    import httpx
    from app.core.config import settings
    from app.models.voice import VoiceAuditLog
    from app.services.voice.adapters import reset_adapters

    monkeypatch.setattr(settings, "VOICE_TTS_PROVIDER", "hosted_tts")
    monkeypatch.setattr(settings, "TTS_API_KEY", "sk-test-live-mock-key")
    reset_adapters()

    dummy_audio_bytes = b"\xff\xfb\x90\x64" + b"\x00" * 300

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = dummy_audio_bytes

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "text": "ನಿಮ್ಮ ರಕ್ತದೊತ್ತಡ ಸಾಮಾನ್ಯವಾಗಿದೆ.",
        "language_code": "kn",
        "voice_gender": "female",
        "audio_format": "audio/mp3",
        "consent_confirmed": True,
    }

    try:
        response = client.post("/api/v1/voice/synthesize", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["is_mock"] is False
        assert data["is_playable"] is True
        assert data["provider"] == "hosted_tts"
        assert data["language_code"] == "kn"
        assert data["audio_format"] == "audio/mp3"
        assert data["disclaimer"] == REAL_TTS_DISCLAIMER

        decoded_payload = base64.b64decode(data["audio_payload"])
        assert decoded_payload == dummy_audio_bytes

        # Verify audit log recorded character counts without storing audio or sensitive text
        audit = db_session.query(VoiceAuditLog).filter(
            VoiceAuditLog.user_id == test_patient_user.id,
            VoiceAuditLog.operation_type == "tts",
            VoiceAuditLog.provider == "hosted_tts"
        ).first()
        assert audit is not None
        assert audit.input_character_count == len(payload["text"])
        assert audit.output_character_count == len(data["audio_payload"])
        assert audit.is_mock is False
        assert audit.detected_language == "kn"
    finally:
        reset_adapters()


def test_synthesize_provider_error_mappings(client, patient_token, monkeypatch):
    from unittest.mock import MagicMock
    import httpx
    from app.core.config import settings
    from app.services.voice.adapters import reset_adapters

    headers = {"Authorization": f"Bearer {patient_token}"}
    payload = {
        "text": "Your vitals are steady.",
        "language_code": "en",
        "consent_confirmed": True,
    }

    # 1. Timeout -> 504
    monkeypatch.setattr(settings, "VOICE_TTS_PROVIDER", "hosted_tts")
    monkeypatch.setattr(settings, "TTS_API_KEY", "sk-test-key")
    reset_adapters()

    def mock_timeout(*args, **kwargs):
        raise httpx.TimeoutException("TTS service timed out")

    mock_client_to = MagicMock()
    mock_client_to.__enter__.return_value = mock_client_to
    mock_client_to.post.side_effect = mock_timeout
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_to)

    try:
        res = client.post("/api/v1/voice/synthesize", json=payload, headers=headers)
        assert res.status_code == 504
        assert "timed out" in res.json()["detail"]

        # 2. Connection failure -> 502
        def mock_conn_err(*args, **kwargs):
            raise httpx.RequestError("Host unreachable")

        mock_client_ce = MagicMock()
        mock_client_ce.__enter__.return_value = mock_client_ce
        mock_client_ce.post.side_effect = mock_conn_err
        monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client_ce)

        res = client.post("/api/v1/voice/synthesize", json=payload, headers=headers)
        assert res.status_code == 502
        assert "connection error" in res.json()["detail"]

        # 3. Missing API key -> 503
        monkeypatch.setattr(settings, "TTS_API_KEY", None)
        monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
        reset_adapters()

        res = client.post("/api/v1/voice/synthesize", json=payload, headers=headers)
        assert res.status_code == 503
        assert "service unavailable" in res.json()["detail"].lower()
    finally:
        reset_adapters()


# =============================================================================
# Stage 2C & 2D & 2E: Patient-Caregiver Multilingual Messaging & Voice Workflow Tests
# =============================================================================

def _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user):
    from app.models.user import PatientCaregiverAssociation
    existing = db_session.query(PatientCaregiverAssociation).filter(
        PatientCaregiverAssociation.patient_id == test_patient_user.patient_profile.id,
        PatientCaregiverAssociation.caregiver_id == test_caregiver_user.caregiver_profile.id,
    ).first()
    if not existing:
        assoc = PatientCaregiverAssociation(
            patient_id=test_patient_user.patient_profile.id,
            caregiver_id=test_caregiver_user.caregiver_profile.id,
            is_primary=True,
            escalation_tier=1
        )
        db_session.add(assoc)
        db_session.commit()


def test_messaging_send_and_receive_between_associated_patient_and_caregiver(
    client, db_session, test_patient_user, test_caregiver_user, patient_token, caregiver_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    caregiver_headers = {"Authorization": f"Bearer {caregiver_token}"}

    # 1. Patient sends Kannada message to caregiver
    payload = {
        "recipient_id": test_caregiver_user.id,
        "text": "ನನಗೆ ಎದೆ ನೋವು ಸ್ವಲ್ಪ ಇದೆ",
        "source_language": "kn",
        "target_language": "en",
        "auto_translate": True,
        "consent_confirmed": True
    }
    send_res = client.post("/api/v1/voice/messages", json=payload, headers=patient_headers)
    assert send_res.status_code == 201
    msg_data = send_res.json()

    assert msg_data["sender_id"] == test_patient_user.id
    assert msg_data["recipient_id"] == test_caregiver_user.id
    assert msg_data["source_language"] == "kn"
    assert msg_data["target_language"] == "en"
    assert msg_data["original_text"] == "ನನಗೆ ಎದೆ ನೋವು ಸ್ವಲ್ಪ ಇದೆ"
    assert msg_data["translated_text"] is not None
    assert msg_data["is_read"] is False
    assert msg_data["delivery_status"] == "delivered"
    assert msg_data["translation_status"] in ("completed", "uncertain")

    msg_id = msg_data["id"]

    # 2. Caregiver views conversation history
    hist_res = client.get(f"/api/v1/voice/conversations/{test_patient_user.id}", headers=caregiver_headers)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total_messages"] >= 1
    assert hist_data["partner"]["partner_id"] == test_patient_user.id
    assert any(m["id"] == msg_id for m in hist_data["messages"])


def test_messaging_caregiver_replies_and_patient_receives_translation(
    client, db_session, test_patient_user, test_caregiver_user, patient_token, caregiver_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    caregiver_headers = {"Authorization": f"Bearer {caregiver_token}"}

    # Patient sends first message
    p_send = client.post("/api/v1/voice/messages", json={
        "recipient_id": test_caregiver_user.id,
        "text": "ನನಗೆ ಆಯಾಸವಾಗುತ್ತಿದೆ",
        "source_language": "kn",
        "target_language": "en",
        "consent_confirmed": True
    }, headers=patient_headers)
    assert p_send.status_code == 201
    parent_id = p_send.json()["id"]

    # Caregiver replies in English
    reply_payload = {
        "text": "Please rest and drink water. I am monitoring your telemetry.",
        "source_language": "en",
        "target_language": "kn",
        "auto_translate": True,
        "consent_confirmed": True
    }
    reply_res = client.post(f"/api/v1/voice/messages/{parent_id}/reply", json=reply_payload, headers=caregiver_headers)
    assert reply_res.status_code == 201
    reply_data = reply_res.json()

    assert reply_data["sender_id"] == test_caregiver_user.id
    assert reply_data["recipient_id"] == test_patient_user.id
    assert reply_data["reply_to_id"] == parent_id
    assert reply_data["source_language"] == "en"
    assert reply_data["target_language"] == "kn"
    assert reply_data["original_text"] == reply_payload["text"]
    assert reply_data["translated_text"] is not None


def test_messaging_unauthorized_caregiver_rejected_403(
    client, db_session, test_patient_user, patient_token
):
    from app.core.security import get_password_hash, create_access_token
    from app.models.user import User, CaregiverProfile, UserRole

    # Create unassociated caregiver
    unauth_user = User(
        email="unauth_caregiver@pulseguardian.ai",
        hashed_password=get_password_hash("pass123"),
        full_name="Dr. Unrelated",
        role=UserRole.CAREGIVER.value,
        phone_number="+919876543299",
        preferred_language="en",
        is_active=True
    )
    db_session.add(unauth_user)
    db_session.flush()

    c_prof = CaregiverProfile(user_id=unauth_user.id, relationship_type="Nurse")
    db_session.add(c_prof)
    db_session.commit()

    unauth_token = create_access_token(subject=unauth_user.id, role=unauth_user.role, extra_claims={"email": unauth_user.email})
    unauth_headers = {"Authorization": f"Bearer {unauth_token}"}

    # Unassociated caregiver tries to view patient's conversation -> 403
    res = client.get(f"/api/v1/voice/conversations/{test_patient_user.id}", headers=unauth_headers)
    assert res.status_code == 403
    assert "Access forbidden" in res.json()["detail"]

    # Unassociated caregiver tries to send message to patient -> 403
    send_res = client.post("/api/v1/voice/messages", json={
        "recipient_id": test_patient_user.id,
        "text": "Hello patient",
        "consent_confirmed": True
    }, headers=unauth_headers)
    assert send_res.status_code == 403
    assert "Access forbidden" in send_res.json()["detail"]


def test_messaging_unrelated_patient_access_rejected_403(
    client, db_session, test_caregiver_user, caregiver_token
):
    from app.core.security import get_password_hash, create_access_token
    from app.models.user import User, PatientProfile, UserRole

    # Create unassociated patient
    other_patient = User(
        email="other_patient@pulseguardian.ai",
        hashed_password=get_password_hash("pass123"),
        full_name="Other Patient",
        role=UserRole.PATIENT.value,
        preferred_language="hi",
        is_active=True
    )
    db_session.add(other_patient)
    db_session.flush()

    p_prof = PatientProfile(user_id=other_patient.id, blood_group="A+")
    db_session.add(p_prof)
    db_session.commit()

    other_token = create_access_token(subject=other_patient.id, role=other_patient.role, extra_claims={"email": other_patient.email})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Other patient tries to message caregiver -> 403
    res = client.post("/api/v1/voice/messages", json={
        "recipient_id": test_caregiver_user.id,
        "text": "Doctor I need help",
        "consent_confirmed": True
    }, headers=other_headers)
    assert res.status_code == 403
    assert "Access forbidden" in res.json()["detail"]


def test_messaging_mark_read_and_unread_counts(
    client, db_session, test_patient_user, test_caregiver_user, patient_token, caregiver_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    caregiver_headers = {"Authorization": f"Bearer {caregiver_token}"}

    # Send message from patient to caregiver
    p_send = client.post("/api/v1/voice/messages", json={
        "recipient_id": test_caregiver_user.id,
        "text": "Checking in with my doctor",
        "consent_confirmed": True
    }, headers=patient_headers)
    assert p_send.status_code == 201
    msg_id = p_send.json()["id"]

    # Caregiver checks unread count
    cnt_res = client.get("/api/v1/voice/messages/unread-count", headers=caregiver_headers)
    assert cnt_res.status_code == 200
    assert cnt_res.json()["total_unread"] >= 1
    assert cnt_res.json()["by_sender"].get(str(test_patient_user.id), 0) >= 1

    # Caregiver marks message as read
    read_res = client.patch(f"/api/v1/voice/messages/{msg_id}/read", headers=caregiver_headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True
    assert read_res.json()["read_at"] is not None
    assert read_res.json()["delivery_status"] == "read"

    # Sender cannot mark their own sent message as read
    inv_read = client.patch(f"/api/v1/voice/messages/{msg_id}/read", headers=patient_headers)
    assert inv_read.status_code == 400
    assert "Only the recipient" in inv_read.json()["detail"]


def test_messaging_mark_all_read_in_conversation(
    client, db_session, test_patient_user, test_caregiver_user, patient_token, caregiver_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    caregiver_headers = {"Authorization": f"Bearer {caregiver_token}"}

    # Send 2 messages
    client.post("/api/v1/voice/messages", json={"recipient_id": test_caregiver_user.id, "text": "Msg 1", "consent_confirmed": True}, headers=patient_headers)
    client.post("/api/v1/voice/messages", json={"recipient_id": test_caregiver_user.id, "text": "Msg 2", "consent_confirmed": True}, headers=patient_headers)

    # Caregiver marks all read
    read_all_res = client.post(f"/api/v1/voice/conversations/{test_patient_user.id}/read-all", headers=caregiver_headers)
    assert read_all_res.status_code == 200
    assert read_all_res.json()["marked_read_count"] >= 2


def test_messaging_translate_on_demand(
    client, db_session, test_patient_user, test_caregiver_user, patient_token, caregiver_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    caregiver_headers = {"Authorization": f"Bearer {caregiver_token}"}

    # Message sent without automatic translation
    msg_res = client.post("/api/v1/voice/messages", json={
        "recipient_id": test_caregiver_user.id,
        "text": "ನನ್ನ ನಾಡಿ ಸಾಮಾನ್ಯವಾಗಿದೆ",
        "source_language": "kn",
        "target_language": "kn",
        "auto_translate": False,
        "consent_confirmed": True
    }, headers=patient_headers)
    assert msg_res.status_code == 201
    msg_id = msg_res.json()["id"]

    # Caregiver requests translation to English on demand
    trans_res = client.post(f"/api/v1/voice/messages/{msg_id}/translate", json={
        "target_language": "en",
        "consent_confirmed": True
    }, headers=caregiver_headers)
    assert trans_res.status_code == 200
    data = trans_res.json()
    assert data["target_language"] == "en"
    assert data["translated_text"] is not None
    assert data["translation_status"] in ("completed", "uncertain")


def test_messaging_synthesize_on_demand(
    client, db_session, test_patient_user, test_caregiver_user, patient_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # Send message
    msg_res = client.post("/api/v1/voice/messages", json={
        "recipient_id": test_caregiver_user.id,
        "text": "Hello doctor",
        "consent_confirmed": True
    }, headers=patient_headers)
    msg_id = msg_res.json()["id"]

    # Synthesize audio on demand
    tts_res = client.post(f"/api/v1/voice/messages/{msg_id}/synthesize", json={
        "language_code": "en",
        "voice_gender": "female",
        "audio_format": "audio/mp3",
        "consent_confirmed": True
    }, headers=patient_headers)
    assert tts_res.status_code == 200
    assert len(tts_res.json()["audio_payload"]) > 0


def test_messaging_consent_revocation_blocks_future_ai_processing(
    client, db_session, test_patient_user, test_caregiver_user, patient_token, caregiver_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # Revoke consent
    client.post("/api/v1/voice/consent", json={"consent_granted": False, "audio_retention_permitted": False}, headers=patient_headers)

    # Message sent with consent_confirmed=False has translation_status="consent_required"
    res = client.post("/api/v1/voice/messages", json={
        "recipient_id": test_caregiver_user.id,
        "text": "Hello without consent",
        "source_language": "en",
        "target_language": "kn",
        "auto_translate": True,
        "consent_confirmed": False
    }, headers=patient_headers)
    assert res.status_code == 201
    assert res.json()["translation_status"] == "consent_required"
    assert res.json()["original_text"] == "Hello without consent"
    assert res.json()["translated_text"] is None

    # Translating message without consent returns 403
    msg_id = res.json()["id"]
    t_res = client.post(f"/api/v1/voice/messages/{msg_id}/translate", json={
        "target_language": "kn",
        "consent_confirmed": False
    }, headers=patient_headers)
    assert t_res.status_code == 403
    assert "Consent required" in t_res.json()["detail"]


def test_messaging_metadata_only_audit_log(
    client, db_session, test_patient_user, test_caregiver_user, patient_token
):
    from app.models.voice import VoiceAuditLog
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    secret_message = "Private clinical note 12345"
    client.post("/api/v1/voice/messages", json={
        "recipient_id": test_caregiver_user.id,
        "text": secret_message,
        "consent_confirmed": True
    }, headers=patient_headers)

    # Inspect audit log
    audit = db_session.query(VoiceAuditLog).filter(
        VoiceAuditLog.user_id == test_patient_user.id,
        VoiceAuditLog.operation_type == "message_sent"
    ).order_by(VoiceAuditLog.created_at.desc()).first()

    assert audit is not None
    assert audit.input_character_count == len(secret_message)
    # Check that secret_message is NOT in any column of VoiceAuditLog
    for col in ["operation_type", "detected_language", "provider"]:
        assert secret_message not in str(getattr(audit, col, ""))


def test_voice_workflow_kannada_speech_to_english_text(
    client, db_session, test_patient_user, test_caregiver_user, patient_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    wav_payload = make_synthetic_wav(2.0)
    b64_audio = base64.b64encode(wav_payload).decode("utf-8")

    payload = {
        "recipient_id": test_caregiver_user.id,
        "audio_base64": b64_audio,
        "audio_format": "audio/wav",
        "language_hint": "kn",
        "target_language": "en",
        "generate_tts": False,
        "consent_confirmed": True
    }

    res = client.post("/api/v1/voice/workflow/dispatch", json=payload, headers=patient_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["sender_id"] == test_patient_user.id
    assert data["recipient_id"] == test_caregiver_user.id
    assert data["stage_statuses"]["audio_validation"] == "completed"
    assert data["stage_statuses"]["stt_transcription"] == "completed"
    assert data["stage_statuses"]["language_detection"] == "completed"
    assert data["stage_statuses"]["translation"] in ("completed", "uncertain")
    assert data["stage_statuses"]["tts_synthesis"] == "skipped"
    assert data["message_id"] > 0
    assert len(data["original_text"]) > 0
    assert len(data["disclaimers"]) >= 1


def test_voice_workflow_with_tts_synthesis(
    client, db_session, test_patient_user, test_caregiver_user, patient_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    payload = {
        "recipient_id": test_caregiver_user.id,
        "text": "My temperature is normal today.",
        "source_language": "en",
        "target_language": "kn",
        "generate_tts": True,
        "voice_gender": "female",
        "tts_audio_format": "audio/mp3",
        "consent_confirmed": True
    }

    res = client.post("/api/v1/voice/workflow/dispatch", json=payload, headers=patient_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["stage_statuses"]["audio_validation"] == "skipped"
    assert data["stage_statuses"]["stt_transcription"] == "skipped"
    assert data["stage_statuses"]["translation"] in ("completed", "uncertain")
    assert data["stage_statuses"]["tts_synthesis"] == "completed"
    assert data["audio_payload"] is not None
    assert len(data["audio_payload"]) > 0


def test_voice_workflow_text_only_branch(
    client, db_session, test_patient_user, test_caregiver_user, patient_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    payload = {
        "recipient_id": test_caregiver_user.id,
        "text": "ನನ್ನ ರಕ್ತದೊತ್ತಡ ಸಾಮಾನ್ಯವಾಗಿದೆ",
        "source_language": "kn",
        "target_language": "en",
        "generate_tts": False,
        "consent_confirmed": True
    }

    res = client.post("/api/v1/voice/workflow/dispatch", json=payload, headers=patient_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["stage_statuses"]["audio_validation"] == "skipped"
    assert data["stage_statuses"]["stt_transcription"] == "skipped"
    assert data["stage_statuses"]["language_detection"] == "completed"
    assert data["stage_statuses"]["translation"] in ("completed", "uncertain")
    assert data["stage_statuses"]["tts_synthesis"] == "skipped"
    assert data["original_text"] == payload["text"]


def test_voice_workflow_invalid_audio_rejected(
    client, db_session, test_patient_user, test_caregiver_user, patient_token
):
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # Malformed audio payload -> 400
    res = client.post("/api/v1/voice/workflow/dispatch", json={
        "recipient_id": test_caregiver_user.id,
        "audio_base64": "NOT_BASE64_BYTES!!!",
        "audio_format": "audio/wav",
        "consent_confirmed": True
    }, headers=patient_headers)
    assert res.status_code == 400

    # Exceeding duration limit (> 60s) -> 413
    long_wav = make_synthetic_wav(65.0)
    res_413 = client.post("/api/v1/voice/workflow/dispatch", json={
        "recipient_id": test_caregiver_user.id,
        "audio_base64": base64.b64encode(long_wav).decode("utf-8"),
        "audio_format": "audio/wav",
        "consent_confirmed": True
    }, headers=patient_headers)
    assert res_413.status_code == 413

    # Unsupported target language -> 400
    res_lang = client.post("/api/v1/voice/workflow/dispatch", json={
        "recipient_id": test_caregiver_user.id,
        "text": "Hello",
        "target_language": "fr",
        "consent_confirmed": True
    }, headers=patient_headers)
    assert res_lang.status_code == 400


def test_voice_workflow_stage_failure_tracking(
    client, db_session, test_patient_user, test_caregiver_user, patient_token, monkeypatch
):
    from app.services.voice.adapters.mock_adapter import MockTranslationAdapter
    _setup_patient_caregiver_pair(db_session, test_patient_user, test_caregiver_user)
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # Simulate translation failure
    def mock_fail_translate(*args, **kwargs):
        raise ConnectionError("Translation provider unreachable")

    monkeypatch.setattr(MockTranslationAdapter, "translate", mock_fail_translate)

    res = client.post("/api/v1/voice/workflow/dispatch", json={
        "recipient_id": test_caregiver_user.id,
        "text": "Test message",
        "source_language": "en",
        "target_language": "kn",
        "consent_confirmed": True
    }, headers=patient_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["stage_statuses"]["translation"] == "failed"
    assert data["original_text"] == "Test message"
    assert data["message_id"] > 0


def test_voice_websocket_authenticated_connect_and_ping(client, patient_token):
    with client.websocket_connect(f"/api/v1/voice/ws?token={patient_token}") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert data == "pong"


def test_voice_websocket_invalid_or_missing_token_rejected(client):
    import pytest

    # Missing token
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/voice/ws") as ws:
            pass

    # Invalid token
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/voice/ws?token=invalid.jwt.token") as ws:
            pass





