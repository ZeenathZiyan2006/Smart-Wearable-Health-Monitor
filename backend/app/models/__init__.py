from app.core.database import Base
from app.models.user import User, UserRole, PatientProfile, CaregiverProfile, PatientCaregiverAssociation, PatientRecoveryRequest, FamilyAccount, FamilyPatientRelationship, PatientRecoveryAuditLog
from app.models.health import (
    HealthTelemetry,
    MedicalReport,
    PatientMedicine,
    MedicineIntakeLog,
    PatientReminder,
    DoctorAppointment,
    PatientMedicalCondition,
    PatientAllergy,
    PatientHydrationLog,
    EarlyWarningPrediction,
    FallEvent,
    InactivityEvent,
    VoiceAssistantSetting,
    HospitalEmergencySetting,
    EmergencyQRProfile,
    QRAccessAuditLog,
    DigitalMedicalDocument,
)
from app.models.emergency import EmergencyAlert, EscalationAuditLog
from app.models.digital_twin import DigitalTwinBaseline, HealthDriftRecord
from app.models.location import LocationLog
from app.models.voice import VoiceConsent, VoiceMessageLog, VoiceAuditLog
from app.models.device import Device, DeviceConnectionHistory
from app.models.notification import InAppNotification
from app.models.audit import SystemAuditLog

__all__ = [
    "Base",
    "User",
    "UserRole",
    "PatientProfile",
    "CaregiverProfile",
    "PatientCaregiverAssociation",
    "HealthTelemetry",
    "MedicalReport",
    "PatientMedicine",
    "MedicineIntakeLog",
    "PatientReminder",
    "DoctorAppointment",
    "PatientMedicalCondition",
    "PatientAllergy",
    "PatientHydrationLog",
    "EarlyWarningPrediction",
    "FallEvent",
    "InactivityEvent",
    "VoiceAssistantSetting",
    "HospitalEmergencySetting",
    "EmergencyQRProfile",
    "QRAccessAuditLog",
    "DigitalMedicalDocument",
    "EmergencyAlert",
    "EscalationAuditLog",
    "DigitalTwinBaseline",
    "HealthDriftRecord",
    "LocationLog",
    "VoiceConsent",
    "VoiceMessageLog",
    "VoiceAuditLog",
    "Device",
    "DeviceConnectionHistory",
    "InAppNotification",
    "SystemAuditLog",
    "PatientRecoveryRequest",
    "FamilyAccount",
    "FamilyPatientRelationship",
    "PatientRecoveryAuditLog",
]
