from fastapi import APIRouter

from app.api.v1 import ai, auth, emergency, health, health_drift, location, users, voice

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Profile"])
api_router.include_router(users.router, prefix="/users", tags=["Patients, Caregivers & Associations"])
api_router.include_router(health.router, prefix="/health", tags=["Wearable Health Ingestion & Telemetry"])
api_router.include_router(location.router, prefix="/location", tags=["GPS Tracking & Geolocation"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["Emergency SOS & Caregiver Escalation"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Engine & Digital Twin"])
api_router.include_router(health_drift.router, prefix="/ai/health-drift", tags=["Health Drift Intelligence"])
api_router.include_router(voice.router, prefix="/voice", tags=["Multilingual Voice Assistance"])

