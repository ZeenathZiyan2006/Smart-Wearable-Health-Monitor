"""
PulseGuardian AI – Demo Data Seeding Script
=============================================
Populates the local database with realistic demo data for frontend development and hackathon demonstrations:
1. Demo Patient (Ramesh Kumar, patient@pulseguardian.ai / Patient@123, preferred_language="kn")
2. Demo Primary Caregiver (Dr. Sunita Rao, caregiver@pulseguardian.ai / Caregiver@123, preferred_language="en")
3. Demo Secondary Caregiver (Nurse Anita Sharma, caregiver2@pulseguardian.ai / Caregiver@123, preferred_language="hi")
4. Patient-Caregiver Tier 1 & Tier 2 Associations
5. Affirmative Voice Consent record
6. Recent Wearable Telemetry (Heart rate, SpO2, Temperature, Steps, Sleep)
7. Recent GPS Location Log
8. Digital Twin Baseline & Health Drift Summary
9. Bilingual Kannada-English Conversation Thread (with 1 unread message for Caregiver dashboard)
10. Resolved Historical SOS Alert with Escalation Logs

Usage:
  python -m app.scripts.seed_demo_data
  python -m app.scripts.seed_demo_data --clean
"""

import argparse
from datetime import datetime, timedelta, timezone
import logging
import sys

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.digital_twin import DigitalTwinBaseline, HealthDriftRecord
from app.models.emergency import EmergencyAlert, EscalationAuditLog
from app.models.health import HealthTelemetry
from app.services.digital_twin_service import DigitalTwinService
from app.services.health_drift_service import HealthDriftService
from app.models.location import LocationLog
from app.models.user import CaregiverProfile, PatientCaregiverAssociation, PatientProfile, User, UserRole
from app.models.voice import VoiceConsent, VoiceMessageLog

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("pulseguardian.seed")


def seed_database(clean: bool = False):
    """Populates idempotent demo records."""
    db = SessionLocal()
    try:
        if clean:
            logger.info("Cleaning existing database tables...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            logger.info("Tables recreated cleanly.")
        else:
            Base.metadata.create_all(bind=engine)

        now = datetime.now(timezone.utc)

        # -------------------------------------------------------------------------
        # 1. Demo Patient User
        # -------------------------------------------------------------------------
        patient_user = db.query(User).filter(User.email == "patient@pulseguardian.ai").first()
        if not patient_user:
            patient_user = User(
                email="patient@pulseguardian.ai",
                hashed_password=get_password_hash("Patient@123"),
                full_name="Ramesh Kumar",
                role=UserRole.PATIENT.value,
                phone_number="+919876543210",
                preferred_language="kn",
                is_active=True,
                created_at=now - timedelta(days=30),
            )
            db.add(patient_user)
            db.flush()

            patient_profile = PatientProfile(
                user_id=patient_user.id,
                date_of_birth=datetime(1968, 5, 14).date(),
                gender="Male",
                blood_group="O+",
                medical_history="Mild hypertension managed with medication. No prior cardiac events.",
                emergency_contact_phone="+919876543211",
                device_uuid="PG-ESP32-001",
                device_status="online",
                last_sync_at=now - timedelta(minutes=2),
                created_at=now - timedelta(days=30),
            )
            db.add(patient_profile)
            db.flush()
            logger.info("Created Demo Patient: patient@pulseguardian.ai (Pass: Patient@123)")
        else:
            patient_profile = patient_user.patient_profile
            logger.info("Demo Patient already exists.")

        # -------------------------------------------------------------------------
        # 2. Demo Primary Caregiver (Doctor)
        # -------------------------------------------------------------------------
        caregiver_user = db.query(User).filter(User.email == "caregiver@pulseguardian.ai").first()
        if not caregiver_user:
            caregiver_user = User(
                email="caregiver@pulseguardian.ai",
                hashed_password=get_password_hash("Caregiver@123"),
                full_name="Dr. Sunita Rao",
                role=UserRole.CAREGIVER.value,
                phone_number="+919876543220",
                preferred_language="en",
                is_active=True,
                created_at=now - timedelta(days=30),
            )
            db.add(caregiver_user)
            db.flush()

            caregiver_profile = CaregiverProfile(
                user_id=caregiver_user.id,
                relationship_type="Doctor",
                organization="PulseHealth Heart & Vascular Clinic",
                notification_preference="all",
                created_at=now - timedelta(days=30),
            )
            db.add(caregiver_profile)
            db.flush()
            logger.info("Created Demo Primary Caregiver: caregiver@pulseguardian.ai (Pass: Caregiver@123)")
        else:
            caregiver_profile = caregiver_user.caregiver_profile
            logger.info("Demo Primary Caregiver already exists.")

        # -------------------------------------------------------------------------
        # 3. Demo Secondary Caregiver (Tier 2 Escalation Nurse)
        # -------------------------------------------------------------------------
        caregiver2_user = db.query(User).filter(User.email == "caregiver2@pulseguardian.ai").first()
        if not caregiver2_user:
            caregiver2_user = User(
                email="caregiver2@pulseguardian.ai",
                hashed_password=get_password_hash("Caregiver@123"),
                full_name="Nurse Anita Sharma",
                role=UserRole.CAREGIVER.value,
                phone_number="+919876543230",
                preferred_language="hi",
                is_active=True,
                created_at=now - timedelta(days=30),
            )
            db.add(caregiver2_user)
            db.flush()

            caregiver2_profile = CaregiverProfile(
                user_id=caregiver2_user.id,
                relationship_type="Nurse",
                organization="PulseHealth Emergency Rapid Response Unit",
                notification_preference="all",
                created_at=now - timedelta(days=30),
            )
            db.add(caregiver2_profile)
            db.flush()
            logger.info("Created Demo Secondary Caregiver: caregiver2@pulseguardian.ai (Pass: Caregiver@123)")
        else:
            caregiver2_profile = caregiver2_user.caregiver_profile

        # -------------------------------------------------------------------------
        # 4. Patient-Caregiver Associations
        # -------------------------------------------------------------------------
        assoc1 = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.patient_id == patient_profile.id,
            PatientCaregiverAssociation.caregiver_id == caregiver_profile.id
        ).first()
        if not assoc1:
            assoc1 = PatientCaregiverAssociation(
                patient_id=patient_profile.id,
                caregiver_id=caregiver_profile.id,
                is_primary=True,
                access_level="full",
                escalation_tier=1,
                created_at=now - timedelta(days=30),
            )
            db.add(assoc1)
            logger.info("Created Tier 1 Association: Ramesh Kumar <-> Dr. Sunita Rao")

        assoc2 = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.patient_id == patient_profile.id,
            PatientCaregiverAssociation.caregiver_id == caregiver2_profile.id
        ).first()
        if not assoc2:
            assoc2 = PatientCaregiverAssociation(
                patient_id=patient_profile.id,
                caregiver_id=caregiver2_profile.id,
                is_primary=False,
                access_level="full",
                escalation_tier=2,
                created_at=now - timedelta(days=30),
            )
            db.add(assoc2)
            logger.info("Created Tier 2 Association: Ramesh Kumar <-> Nurse Anita Sharma")

        # -------------------------------------------------------------------------
        # 5. Voice Consent
        # -------------------------------------------------------------------------
        consent = db.query(VoiceConsent).filter(VoiceConsent.user_id == patient_user.id).first()
        if not consent:
            consent = VoiceConsent(
                user_id=patient_user.id,
                consent_granted=True,
                audio_retention_permitted=False,
                privacy_policy_accepted=True,
                created_at=now - timedelta(days=15),
            )
            db.add(consent)
            logger.info("Created Affirmative Voice Consent for Ramesh Kumar")

        # -------------------------------------------------------------------------
        # 6. Wearable Telemetry Series (Last 24 hours of readings)
        # -------------------------------------------------------------------------
        existing_telemetry = db.query(HealthTelemetry).filter(HealthTelemetry.patient_id == patient_profile.id).first()
        if not existing_telemetry:
            telemetry_records = []
            base_time = now - timedelta(hours=24)
            # Create hourly reading points
            for h in range(25):
                t_point = base_time + timedelta(hours=h)
                # Realistic circadian variation (lower HR at night, higher during daytime)
                is_night = (t_point.hour < 6 or t_point.hour >= 23)
                hr = 62.0 if is_night else (72.0 + (h % 5) * 2.0)
                spo2 = 98.5 if is_night else 98.0
                temp = 36.4 if is_night else 36.6
                activity = "resting" if is_night else ("walking" if h in (8, 17) else "sedentary")
                steps = 0 if is_night else 350 + (h * 40)

                rec = HealthTelemetry(
                    patient_id=patient_profile.id,
                    heart_rate=hr,
                    spo2=spo2,
                    temperature=temp,
                    blood_pressure_sys=122.0,
                    blood_pressure_dia=78.0,
                    respiratory_rate=16.0,
                    accelerometer_x=0.02,
                    accelerometer_y=0.98,
                    accelerometer_z=0.15,
                    activity_type=activity,
                    step_count=steps,
                    calories_burned=float(steps * 0.04),
                    sleep_stage="deep" if (is_night and h == 3) else ("light" if is_night else None),
                    recorded_at=t_point,
                    created_at=t_point,
                )
                telemetry_records.append(rec)
            db.bulk_save_objects(telemetry_records)
            logger.info(f"Seeded {len(telemetry_records)} wearable health telemetry records.")

        # -------------------------------------------------------------------------
        # 7. GPS Location Log
        # -------------------------------------------------------------------------
        existing_loc = db.query(LocationLog).filter(LocationLog.patient_id == patient_profile.id).first()
        if not existing_loc:
            loc = LocationLog(
                patient_id=patient_profile.id,
                latitude=12.9716,
                longitude=77.5946,
                altitude=920.0,
                accuracy=4.5,
                speed=0.0,
                is_gps_available=True,
                recorded_at=now - timedelta(minutes=5),
                created_at=now - timedelta(minutes=5),
            )
            db.add(loc)
            logger.info("Seeded GPS Location Log: Bangalore (Lat: 12.9716, Lon: 77.5946).")

        # -------------------------------------------------------------------------
        # 8. Digital Twin Baseline & Health Drift
        # -------------------------------------------------------------------------
        dt, is_cold = DigitalTwinService.get_or_calculate_baseline(db, patient_profile.id, force_recalculate=True)
        drift_summary = HealthDriftService.analyze_drift(db, patient_profile.id, window_days=7, persist=True)
        logger.info(f"Seeded Digital Twin Baseline (samples: {dt.samples_count}) & Health Drift records.")

        # -------------------------------------------------------------------------
        # 9. Bilingual Patient-Caregiver Conversation Thread
        # -------------------------------------------------------------------------
        existing_msgs = db.query(VoiceMessageLog).filter(VoiceMessageLog.sender_id == patient_user.id).first()
        if not existing_msgs:
            m1 = VoiceMessageLog(
                sender_id=patient_user.id,
                recipient_id=caregiver_user.id,
                source_language="kn",
                target_language="en",
                original_text="ನನ್ನ ರಕ್ತದೊತ್ತಡ ಮತ್ತು ನಾಡಿಮಿಡಿತ ಇಂದು ಸ್ಥಿರವಾಗಿದೆಯೇ?",
                translated_text="Are my blood pressure and pulse steady today?",
                is_read=True,
                read_at=now - timedelta(hours=5),
                delivery_status="read",
                translation_status="completed",
                is_uncertain=False,
                consent_confirmed=True,
                stt_provider="none",
                translation_provider="hosted_translation",
                tts_provider="none",
                created_at=now - timedelta(hours=6),
            )
            db.add(m1)
            db.flush()

            m2 = VoiceMessageLog(
                sender_id=caregiver_user.id,
                recipient_id=patient_user.id,
                source_language="en",
                target_language="kn",
                original_text="Yes, Ramesh. Your vitals are completely stable within your Digital Twin baseline.",
                translated_text="ಹೌದು, ರಮೇಶ್. ನಿಮ್ಮ ಆರೋಗ್ಯ ಸೂಚಕಗಳು ನಿಮ್ಮ ಡಿಜಿಟಲ್ ಟ್ವಿನ್ ಆಧಾರದೊಳಗೆ ಸಂಪೂರ್ಣವಾಗಿ ಸ್ಥಿರವಾಗಿವೆ.",
                is_read=True,
                read_at=now - timedelta(hours=4),
                delivery_status="read",
                translation_status="completed",
                is_uncertain=False,
                reply_to_id=m1.id,
                consent_confirmed=True,
                stt_provider="none",
                translation_provider="hosted_translation",
                tts_provider="none",
                created_at=now - timedelta(hours=4, minutes=50),
            )
            db.add(m2)
            db.flush()

            # Unread message for Caregiver dashboard display
            m3 = VoiceMessageLog(
                sender_id=patient_user.id,
                recipient_id=caregiver_user.id,
                source_language="kn",
                target_language="en",
                original_text="ಧನ್ಯವಾದಗಳು ಡಾಕ್ಟರ್, ನಾನು ನಿಗದಿತ ನಡಿಗೆಯನ್ನು ಮುಂದುವರಿಸುತ್ತೇನೆ.",
                translated_text="Thank you doctor, I will continue my scheduled walk.",
                is_read=False,
                read_at=None,
                delivery_status="delivered",
                translation_status="completed",
                is_uncertain=False,
                reply_to_id=m2.id,
                consent_confirmed=True,
                stt_provider="none",
                translation_provider="hosted_translation",
                tts_provider="none",
                created_at=now - timedelta(minutes=45),
            )
            db.add(m3)
            logger.info("Seeded Bilingual Kannada-English Conversation thread with 1 unread message.")

        # -------------------------------------------------------------------------
        # 10. Historical Resolved SOS Alert
        # -------------------------------------------------------------------------
        existing_alert = db.query(EmergencyAlert).filter(EmergencyAlert.patient_id == patient_profile.id).first()
        if not existing_alert:
            alert = EmergencyAlert(
                patient_id=patient_profile.id,
                device_uuid="PG-ESP32-001",
                alert_type="manual_sos",
                severity="critical",
                status="resolved",
                current_escalation_tier=1,
                latitude=12.9716,
                longitude=77.5946,
                location_accuracy=4.5,
                assistance_message="I experienced a mild dizziness spell after taking medication.",
                acknowledged_by_id=caregiver_user.id,
                acknowledged_at=now - timedelta(days=2, hours=1),
                resolved_at=now - timedelta(days=2),
                resolution_notes="Patient rested; vitals recovered; no hospitalization required.",
                created_at=now - timedelta(days=2, hours=1, minutes=10),
            )
            db.add(alert)
            db.flush()

            audit_log = EscalationAuditLog(
                alert_id=alert.id,
                tier=1,
                notified_caregiver_id=caregiver_user.id,
                notification_channel="all",
                provider="mock_dispatch",
                recipient_address="+919876543220",
                status="delivered",
                message_payload="Alert: manual_sos | Severity: critical | Location: Lat: 12.9716, Lon: 77.5946",
                retry_count=0,
                sent_at=now - timedelta(days=2, hours=1, minutes=9),
            )
            db.add(audit_log)
            logger.info("Seeded Historical Emergency SOS Alert and Escalation Audit log.")

        db.commit()
        logger.info("=== Demo Data Seeding Completed Successfully! ===")
        logger.info("Demo Patient:   patient@pulseguardian.ai   / Patient@123   (Language: kn)")
        logger.info("Demo Caregiver: caregiver@pulseguardian.ai / Caregiver@123 (Language: en)")
        logger.info("Demo Caregiver2:caregiver2@pulseguardian.ai/ Caregiver@123 (Language: hi)")

    except Exception as exc:
        db.rollback()
        logger.error(f"Seeding failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed PulseGuardian AI demo data.")
    parser.add_argument("--clean", action="store_true", help="Drop and recreate all tables before seeding.")
    args = parser.parse_args()
    seed_database(clean=args.clean)
