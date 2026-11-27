import json
import os
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "PulseGuardian AI Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & JWT
    SECRET_KEY: str = "pulseguardian-development-super-secret-key-change-in-production-min32bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "pulseguardian"
    POSTGRES_PASSWORD: str = "pulseguardian_password"
    POSTGRES_DB: str = "pulseguardian_db"
    DATABASE_URL: str | None = None
    TEST_DATABASE_URL: str = "sqlite:///./test_pulseguardian.db"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    EMERGENCY_ACK_TIMEOUT_SECONDS: int = 120  # 2 minutes acknowledgement window per tier

    # Multilingual Voice Assistance & Audio Processing Settings
    VOICE_STT_PROVIDER: str = "mock_development"  # "mock_development", "local_whisper", "hosted_whisper"
    VOICE_TRANSLATION_PROVIDER: str = "mock_development"  # "mock_development", "hosted_translation", "local_indictrans"
    VOICE_TTS_PROVIDER: str = "mock_development"  # "mock_development", "hosted_tts"
    VOICE_ENABLE_CONSENT_ENFORCEMENT: bool = True
    VOICE_AUDIO_RETENTION_HOURS: int = 0  # 0 indicates ephemeral memory processing, no raw audio saved to disk
    VOICE_CONFIDENCE_THRESHOLD: float = 0.60
    VOICE_LANGUAGE_CONFIDENCE_THRESHOLD: float = 0.50
    VOICE_MAX_AUDIO_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB maximum audio payload
    VOICE_MAX_AUDIO_DURATION_SECONDS: float = 60.0  # 60 seconds maximum audio duration
    VOICE_MAX_TRANSLATION_CHARS: int = 5000  # 5,000 characters maximum text translation payload
    VOICE_MAX_TTS_CHARS: int = 2000  # 2,000 characters maximum speech synthesis payload
    DEFAULT_SYSTEM_LANGUAGE: str = "en"

    # Hosted OpenAI Whisper STT Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # Local Faster-Whisper STT Settings
    FASTER_WHISPER_MODEL_SIZE: str = "base"
    FASTER_WHISPER_DEVICE: str = "cpu"
    FASTER_WHISPER_COMPUTE_TYPE: str = "int8"

    # Multilingual Translation Settings (Hosted & IndicTrans2)
    TRANSLATION_API_KEY: Optional[str] = None
    TRANSLATION_API_BASE: str = "https://api.openai.com/v1"
    TRANSLATION_MODEL_NAME: str = "gpt-4o-mini"
    INDICTRANS_MODEL_DIR: Optional[str] = None

    # Text-to-Speech (TTS) Settings (Hosted & Mock)
    TTS_API_KEY: Optional[str] = None
    TTS_API_BASE: str = "https://api.openai.com/v1"
    TTS_MODEL_NAME: str = "tts-1"
    TTS_DEFAULT_VOICE_GENDER: str = "neutral"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:4173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # If explicitly opted into PostgreSQL or running in Docker container network
        if os.getenv("USE_POSTGRES", "false").lower() in ("true", "1", "yes") or (
            os.getenv("POSTGRES_SERVER") and os.getenv("POSTGRES_SERVER") not in ("localhost", "127.0.0.1")
        ):
            return (
                f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        # Default zero-configuration portable SQLite database
        return "sqlite:///./pulseguardian.db"


settings = Settings()
