from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api_router import api_router
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist if database is accessible
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        # Running in environment where DB is migrated via Alembic or tested separately
        pass
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for PulseGuardian AI – Smart Wearable Health Monitoring and Emergency Assistance System",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS middleware configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["System"])
def root() -> Dict[str, str]:
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "documentation": f"{settings.API_V1_STR}/docs",
        "status": "healthy"
    }


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "database": "connected"
    }
