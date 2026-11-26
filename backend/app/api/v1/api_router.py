from fastapi import APIRouter

from app.api.v1 import (
    ai,
    audit,
    auth,
    devices,
    emergency,
    health,
    health_drift,
    location,
    notifications,
    users,
    voice,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Profile"])
api_router.include_router(users.router, prefix="/users", tags=["Patients, Caregivers & Associations"])
api_router.include_router(devices.router, prefix="/devices", tags=["Wearable Device Management"])
api_router.include_router(health.router, prefix="/health", tags=["Wearable Health Ingestion & Telemetry"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["In-App Notifications"])
api_router.include_router(location.router, prefix="/location", tags=["GPS Tracking & Geolocation"])
api_router.include_router(emergency.router, prefix="/emergency", tags=["Emergency SOS & Caregiver Escalation"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Engine & Digital Twin"])
api_router.include_router(health_drift.router, prefix="/ai/health-drift", tags=["Health Drift Intelligence"])
api_router.include_router(voice.router, prefix="/voice", tags=["Multilingual Voice Assistance"])
api_router.include_router(audit.router, prefix="/audit", tags=["System Audit Logs"])
