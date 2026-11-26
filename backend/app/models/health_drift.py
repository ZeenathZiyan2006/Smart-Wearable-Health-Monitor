# Re-export HealthDrift models for app.models.health_drift compatibility
from app.models.digital_twin import HealthDriftRecord

__all__ = ["HealthDriftRecord"]
