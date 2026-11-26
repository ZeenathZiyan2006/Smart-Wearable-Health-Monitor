# Re-export DigitalTwin models for app.models.ai compatibility
from app.models.digital_twin import DigitalTwinBaseline, HealthDriftRecord

__all__ = ["DigitalTwinBaseline", "HealthDriftRecord"]
