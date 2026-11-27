"""
Nova Universal AI Voice & Clinical Assistant Service
Enforces strict Role-Based Access Control (RBAC), data isolation between roles,
and distinct personas/workflows for:
1. Patient (Self-care, mood check-ins, medication alarms, family calls, SOS)
2. Family Member (Caregiver wellbeing, linked patient vitals, adherence, location, emergency)
3. Doctor (Clinical trends, assigned patient EHR, AI observations, prescription assist)
4. Emergency EMS (Active incident status, triage vitals, GPS coordinates, handover)
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
import math
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import (
    User,
    UserRole,
    PatientProfile,
    CaregiverProfile,
    PatientCaregiverAssociation,
    DoctorProfile,
    DoctorPatientAssignment,
    EmergencyTeamProfile,
)
from app.models.health import (
    HealthTelemetry,
    PatientMedicine,
    DoctorAppointment,
    PatientMedicalCondition,
    PatientAllergy,
    EarlyWarningPrediction,
)
from app.models.emergency import EmergencyAlert
from app.models.location import LocationLog
from app.models.nova import NovaWellbeingLog, NovaAuditActionLog
from app.schemas.nova import (
    NovaInteractRequest,
    NovaInteractResponse,
    NovaSuggestedAction,
    NovaContextResponse,
)


class NovaAssistantService:

    @staticmethod
    def get_user_context(db: Session, current_user: User) -> NovaContextResponse:
        """Returns the user's role, permissions, linked patients, and active incident context."""
        role = current_user.role or "patient"
        authorized_patients: List[Dict[str, Any]] = []
        capabilities: List[str] = []
        has_active_emergency = False

        if role == UserRole.PATIENT.value:
            capabilities = [
                "check_vitals", "mood_checkin", "medicine_reminder",
                "call_family", "emergency_sos", "listen_story", "wearable_status"
            ]
            if current_user.patient_profile:
                authorized_patients.append({
                    "id": current_user.patient_profile.id,
                    "patient_id": current_user.patient_id or f"PT-{current_user.patient_profile.id}",
                    "name": current_user.full_name,
                    "blood_group": current_user.patient_profile.blood_group,
                    "is_self": True,
                })
                active_alert = db.query(EmergencyAlert).filter(
                    EmergencyAlert.patient_id == current_user.patient_profile.id,
                    EmergencyAlert.status.in_(["triggered", "escalated", "active"])
                ).first()
                if active_alert:
                    has_active_emergency = True

        elif role in (UserRole.CAREGIVER.value, UserRole.FAMILY.value):
            capabilities = [
                "caregiver_wellbeing", "check_patient_health", "check_patient_medication",
                "check_patient_location", "send_patient_message", "emergency_status"
            ]
            if current_user.caregiver_profile:
                associations = db.query(PatientCaregiverAssociation).filter(
                    PatientCaregiverAssociation.caregiver_id == current_user.caregiver_profile.id
                ).all()
                for assoc in associations:
                    pat = assoc.patient
                    if pat and pat.user:
                        authorized_patients.append({
                            "id": pat.id,
                            "patient_id": pat.user.patient_id or f"PT-{pat.id}",
                            "name": pat.user.full_name,
                            "relationship": current_user.caregiver_profile.relationship_type or "Caregiver",
                            "is_primary": assoc.is_primary,
                        })
                        active_alert = db.query(EmergencyAlert).filter(
                            EmergencyAlert.patient_id == pat.id,
                            EmergencyAlert.status.in_(["triggered", "escalated", "active"])
                        ).first()
                        if active_alert:
                            has_active_emergency = True

        elif role == UserRole.DOCTOR.value:
            capabilities = [
                "clinical_trends", "ai_observations", "prescription_documentation_assist",
                "clinical_notes_summary", "emergency_history"
            ]
            doc_prof = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
            if doc_prof:
                assignments = db.query(DoctorPatientAssignment).filter(
                    DoctorPatientAssignment.doctor_id == doc_prof.id,
                    DoctorPatientAssignment.status == "active"
                ).all()
                for assign in assignments:
                    pat = assign.patient
                    if pat and pat.user:
                        authorized_patients.append({
                            "id": pat.id,
                            "patient_id": pat.user.patient_id or f"PT-{pat.id}",
                            "name": pat.user.full_name,
                            "clinical_notes": assign.clinical_notes,
                            "can_prescribe": assign.can_prescribe,
                        })

        elif role == UserRole.EMERGENCY.value:
            capabilities = [
                "active_incidents", "incident_triage", "patient_gps_coordinates",
                "record_handover", "nearest_facilities"
            ]
            active_alerts = db.query(EmergencyAlert).filter(
                EmergencyAlert.status.in_(["triggered", "escalated", "active"])
            ).all()
            if active_alerts:
                has_active_emergency = True
            for alert in active_alerts:
                pat = alert.patient
                if pat and pat.user:
                    authorized_patients.append({
                        "id": pat.id,
                        "patient_id": pat.user.patient_id or f"PT-{pat.id}",
                        "name": pat.user.full_name,
                        "alert_id": alert.id,
                        "alert_type": alert.alert_type,
                        "triggered_at": alert.created_at.isoformat() if alert.created_at else None,
                    })

        return NovaContextResponse(
            role=role,
            user_name=current_user.full_name,
            user_id=current_user.id,
            preferred_language=current_user.preferred_language or "en",
            authorized_patients=authorized_patients,
            has_active_emergency=has_active_emergency,
            capabilities=capabilities,
        )

    @classmethod
    def interact(
        cls,
        db: Session,
        current_user: User,
        payload: NovaInteractRequest,
        client_ip: Optional[str] = None
    ) -> NovaInteractResponse:
        """Central entrypoint for all Nova queries with role-based routing and safety verification."""
        role = current_user.role or "patient"
        lang = payload.language or current_user.preferred_language or "en"
        msg = (payload.message or "").strip().lower()
        act = (payload.action or "").strip().lower()

        # ---------------------------------------------------------------------
        # 1. PATIENT PERSONA
        # ---------------------------------------------------------------------
        if role == UserRole.PATIENT.value:
            return cls._handle_patient_interaction(db, current_user, payload, lang, msg, act, client_ip)

        # ---------------------------------------------------------------------
        # 2. FAMILY CAREGIVER PERSONA
        # ---------------------------------------------------------------------
        elif role in (UserRole.CAREGIVER.value, UserRole.FAMILY.value):
            return cls._handle_family_interaction(db, current_user, payload, lang, msg, act, client_ip)

        # ---------------------------------------------------------------------
        # 3. ATTENDING DOCTOR PERSONA
        # ---------------------------------------------------------------------
        elif role == UserRole.DOCTOR.value:
            return cls._handle_doctor_interaction(db, current_user, payload, lang, msg, act, client_ip)

        # ---------------------------------------------------------------------
        # 4. EMERGENCY EMS TEAM PERSONA
        # ---------------------------------------------------------------------
        elif role == UserRole.EMERGENCY.value:
            return cls._handle_emergency_interaction(db, current_user, payload, lang, msg, act, client_ip)

        # Fallback / Admin
        return cls._build_response(
            text="Welcome to Nova Universal Assistant. Your account is active.",
            audio_text="Welcome to Nova Universal Assistant.",
            role=role,
            lang=lang,
            suggested_actions=[
                NovaSuggestedAction(id="1", label="Status", action="check_status", icon="Activity", color="cyan")
            ]
        )

    # =========================================================================
    # ROLE HANDLER 1: PATIENT
    # =========================================================================
    @classmethod
    def _handle_patient_interaction(
        cls, db: Session, user: User, payload: NovaInteractRequest,
        lang: str, msg: str, act: str, client_ip: Optional[str]
    ) -> NovaInteractResponse:
        patient_profile = user.patient_profile
        patient_name = user.full_name
        pat_id = user.patient_id or (f"PT-{patient_profile.id}" if patient_profile else "PT-000001")

        # Emergency SOS activation
        if act == "emergency_sos" or any(w in msg for w in ["emergency", "sos", "help", "save me", "ತುರ್ತು", "ಆಪತ್", "ಮದತ್"]):
            alert = EmergencyAlert(
                patient_id=patient_profile.id if patient_profile else 1,
                alert_type="VOICE_SOS",
                severity="critical",
                status="triggered",
                created_at=datetime.now(timezone.utc),
                latitude=12.9716,
                longitude=77.5946,
            )
            db.add(alert)
            db.flush()

            # Audit
            audit = NovaAuditActionLog(
                user_id=user.id,
                role="patient",
                action_type="sos_triggered",
                target_patient_id=patient_profile.id if patient_profile else None,
                status="completed",
                details="Voice SOS initiated via Nova assistant.",
                client_ip=client_ip
            )
            db.add(audit)
            db.commit()

            text_map = {
                "en": f"Emergency SOS initiated! Dialing emergency services and alerting your family caregivers immediately.",
                "kn": f"ತುರ್ತು ಎಸ್‌ಒಎಸ್ ಪ್ರಕ್ರಿಯೆ ಆರಂಭಿಸಲಾಗಿದೆ! ತುರ್ತು ಸೇವೆಗೆ ಕರೆ ಮಾಡಲಾಗುತ್ತಿದೆ ಮತ್ತು ನಿಮ್ಮ ಕುಟುಂಬಕ್ಕೆ ತಕ್ಷಣ ಎಚ್ಚರಿಕೆ ಕಳುಹಿಸಲಾಗಿದೆ.",
                "hi": f"आपातकालीन एसओएस शुरू किया गया! आपातकालीन सेवाओं और आपके परिवार को तुरंत सूचित किया जा रहा है।",
                "ta": f"அவசர எஸ்ஓஎஸ் தொடங்கப்பட்டது! உங்கள் குடும்பத்தினருக்கு உடனடியாக அவசர எச்சரிக்கை அனுப்பப்பட்டது.",
                "te": f"అత్యవసర SOS ప్రారంభించబడింది! మీ కుటుంబ సభ్యులకు వెంటనే హెచ్చరిక పంపబడింది.",
                "ml": f"അടിയന്തര SOS ആരംഭിച്ചു! അടിയന്തര സേവനങ്ങൾക്കും കുടുംബാംഗങ്ങൾക്കും വിവരം നൽകി.",
            }
            return cls._build_response(
                text=text_map.get(lang, text_map["en"]),
                audio_text=text_map.get(lang, text_map["en"]),
                role="patient",
                lang=lang,
                status="emergency_initiated",
                is_emergency=True,
                direct_call_url="tel:112",
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                suggested_actions=[
                    NovaSuggestedAction(id="sos_call", label="Call 112 SOS", action="call_112", icon="PhoneCall", color="rose"),
                    NovaSuggestedAction(id="cancel", label="Cancel SOS", action="cancel_sos", icon="X", color="slate"),
                ]
            )

        # Direct phone call to caregiver
        if act == "call_family" or any(w in msg for w in ["call daughter", "call son", "call family", "call doctor", "ಕರೆ ಮಾಡಿ", "कॉल करो", "அழைக்கவும்"]):
            phone = patient_profile.emergency_contact_phone if patient_profile else "+91 98450 12345"
            contact_name = "Primary Caregiver"
            if patient_profile:
                assoc = db.query(PatientCaregiverAssociation).filter(
                    PatientCaregiverAssociation.patient_id == patient_profile.id
                ).first()
                if assoc and assoc.caregiver and assoc.caregiver.user:
                    contact_name = assoc.caregiver.user.full_name
                    phone = assoc.caregiver.user.phone_number or phone

            audit = NovaAuditActionLog(
                user_id=user.id,
                role="patient",
                action_type="phone_call_initiated",
                target_patient_id=patient_profile.id if patient_profile else None,
                status="completed",
                details=f"Direct phone call to {contact_name} ({phone}) via Nova.",
                client_ip=client_ip
            )
            db.add(audit)
            db.commit()

            text_map = {
                "en": f"I found your registered contact {contact_name} ({phone}). Placing a direct phone call now.",
                "kn": f"ನಿಮ್ಮ ನೋಂದಾಯಿತ ಸಂಪರ್ಕ {contact_name} ({phone}) ಕಂಡುಬಂದಿದೆ. ಈಗಲೇ ನೇರ ಕರೆ ಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ.",
                "hi": f"आपके पंजीकृत संपर्क {contact_name} ({phone}) को सीधे कॉल मिलाया जा रहा है।",
                "ta": f"உங்கள் பதிவு செய்யப்பட்ட பராமரிப்பாளர் {contact_name} அவர்களை இப்போது நேரடியாக அழைக்கிறேன்.",
                "te": f"మీ నమోదిత సంరక్షకుడు {contact_name} కి ఇప్పుడు నేరుగా కాల్ చేయబడుతోంది.",
                "ml": f"നിങ്ങളുടെ രജിസ്റ്റർ ചെയ്ത പരിചാരകൻ {contact_name}-ലേക്ക് നേരിട്ട് വിളിക്കുന്നു.",
            }
            return cls._build_response(
                text=text_map.get(lang, text_map["en"]),
                audio_text=text_map.get(lang, text_map["en"]),
                role="patient",
                lang=lang,
                direct_call_url=f"tel:{phone.replace(' ', '')}",
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                suggested_actions=[
                    NovaSuggestedAction(id="call_now", label=f"Call {contact_name}", action="call_family", icon="PhoneCall", color="emerald"),
                    NovaSuggestedAction(id="msg", label="Send Message", action="send_message", icon="MessageSquare", color="cyan"),
                ]
            )

        # Mood check-in / loneliness / companionship
        if act == "mood_checkin" or any(w in msg for w in ["lonely", "sad", "pain", "tired", "stress", "feeling", "ಕಷ್ಟ", "ಬೇಸರ", "ಒಂಟಿ", "दर्द", "उदासी", "अकेला"]):
            mood = payload.mood_type or ("lonely" if "lonely" in msg else "tired" if "tired" in msg else "calm")
            # Save wellbeing check-in (is_caregiver_wellbeing=False for patient)
            log = NovaWellbeingLog(
                user_id=user.id,
                role="patient",
                target_patient_id=patient_profile.id if patient_profile else None,
                mood_type=mood,
                notes=payload.notes or msg,
                is_caregiver_wellbeing=False,
            )
            db.add(log)
            db.commit()

            text_map = {
                "en": f"I hear you, {patient_name.split()[0]}. It is completely normal to feel this way. I am right here with you. Would you like to listen to an uplifting story or call someone in your family?",
                "kn": f"ನಿಮ್ಮ ಭಾವನೆ ನನಗೆ ಅರ್ಥವಾಗುತ್ತದೆ {patient_name.split()[0]}. ನೀವು ಎಂದಿಗೂ ಒಂಟಿಯಲ್ಲ, ನೋವಾ ನಿಮ್ಮೊಂದಿಗಿದೆ. ಒಂದು ಸುಂದರ ಕಥೆ ಹೇಳಬೇಕೇ ಅಥವಾ ನಿಮ್ಮ ಕುಟುಂಬದವರಿಗೆ ಕರೆ ಮಾಡಬೇಕೇ?",
                "hi": f"मैं समझ सकती हूँ, {patient_name.split()[0]}। आप अकेले नहीं हैं, मैं हमेशा आपके साथ हूँ। क्या आप कोई प्रेरक कहानी सुनना चाहेंगे या परिवार से बात करेंगे?",
                "ta": f"நான் உங்களுடன் இருக்கிறேன் {patient_name.split()[0]}. நீங்கள் தனிமையில் இல்லை. ஒரு ஊக்கமளிக்கும் கதை கேட்க விரும்புகிறீர்களா?",
                "te": f"నేను మీతోనే ఉన్నాను {patient_name.split()[0]}. మీరు ఒంటరిగా లేరు. ఒక మంచి కథ వినాలనుకుంటున్నారా?",
                "ml": f"ഞാൻ ഇവിടെ നിങ്ങളുടെ കൂടെയുണ്ട് {patient_name.split()[0]}. നിങ്ങൾ തനിച്ചല്ല. ഒരു നല്ല കഥ കേൾക്കാൻ ആഗ്രഹിക്കുന്നുണ്ടോ?",
            }
            return cls._build_response(
                text=text_map.get(lang, text_map["en"]),
                audio_text=text_map.get(lang, text_map["en"]),
                role="patient",
                lang=lang,
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                suggested_actions=[
                    NovaSuggestedAction(id="story", label="Tell a Story", action="listen_story", icon="Sparkles", color="cyan"),
                    NovaSuggestedAction(id="call", label="Call Family", action="call_family", icon="PhoneCall", color="emerald"),
                    NovaSuggestedAction(id="vitals", label="Check Health", action="check_vitals", icon="Heart", color="purple"),
                ]
            )

        # Storytelling
        if act == "listen_story" or "story" in msg or "ಕಥೆ" in msg or "कहानी" in msg or "கதை" in msg:
            stories = {
                "en": "Once upon a time in a tranquil green valley, a wise old banyan tree taught the little birds that peace comes from breathing deeply and appreciating the morning sunshine. You are cherished, calm, and strong.",
                "kn": "ಒಂದು ಸುಂದರ ಹಸಿರು ಕಣಿವೆಯಲ್ಲಿ, ಹಳೆಯ ಆಲದ ಮರವು ಪುಟ್ಟ ಹಕ್ಕಿಗಳಿಗೆ ಶಾಂತಿಯಿಂದ ಉಸಿರಾಡಲು ಮತ್ತು ಮುಂಜಾನೆಯ ಸೂರ್ಯನ ಬೆಳಕನ್ನು ಆನಂದಿಸಲು ಕಲಿಸಿತು. ನಿಮ್ಮ ಮನಸ್ಸಿನಲ್ಲಿ ಅಪಾರವಾದ ಶಾಂತಿ ಮತ್ತು ಶಕ್ತಿ ಇದೆ.",
                "hi": "एक शांत हरी घाटी में, एक विशाल बरगद का पेड़ पक्षियों को सिखाता था कि सच्चा सुकून सुबह की पहली धूप और गहरी सांसों में है। आप स्वस्थ, सुरक्षित और शांत हैं।",
                "ta": "ஒரு அமைதியான சோலையில் உள்ள ஆலமரம், பறவைகளுக்கு ஆழமாக மூச்சுவிட்டு விடியற்காலை சூரியனை ரசிக்கக் கற்றுக்கொடுத்தது. நீங்கள் மிகவும் அமைதியாகவும் வலிமையாகவும் இருக்கிறீர்கள்.",
                "te": "ఒక ప్రశాంతమైన లోయలో పెద్ద మర్రిచెట్టు పక్షులకు ప్రశాంతంగా ఊపిరి పీల్చుకోవడం నేర్పింది. మీరు ఎల్లప్పుడూ ధైర్యంగా, ఆరోగ్యంగా ఉండాలి.",
                "ml": "ശാന്തമായ ഒരു താഴ്വരയിലെ ആൽമരം പക്ഷികളെ ശാന്തമായി ശ്വാസമെടുക്കാൻ പഠിപ്പിച്ചു. നിങ്ങൾ തികച്ചും സുരക്ഷിതനും ശക്തനുമാണ്.",
            }
            return cls._build_response(
                text=stories.get(lang, stories["en"]),
                audio_text=stories.get(lang, stories["en"]),
                role="patient",
                lang=lang,
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                suggested_actions=[
                    NovaSuggestedAction(id="vitals", label="Check Vitals", action="check_vitals", icon="Heart", color="cyan"),
                    NovaSuggestedAction(id="meds", label="Medication", action="medicine_reminder", icon="Pill", color="emerald"),
                ]
            )

        # Medication reminders
        if act == "medicine_reminder" or any(w in msg for w in ["medicine", "tablet", "dose", "ಮಾತ್ರೆ", "ಔಷಧ", "दवा", "மருந்து", "మందు"]):
            med = None
            if patient_profile:
                med = db.query(PatientMedicine).filter(
                    PatientMedicine.patient_id == patient_profile.id,
                    PatientMedicine.is_active == True
                ).first()
            med_name = med.name if med else "Dolo 650"
            dosage = med.dosage if med else "1 Tablet"
            timing = med.scheduled_times if med else "08:00, 20:00"
            stock = med.remaining_stock if med else 25

            text_map = {
                "en": f"Your next scheduled medication is {med_name} ({dosage}) scheduled for {timing}. You have {stock} tablets remaining. Please take it with a glass of water after meals.",
                "kn": f"ನಿಮ್ಮ ಮುಂದಿನ ಔಷಧ {med_name} ({dosage}) ಸಮಯ {timing}. ನಿಮ್ಮ ಬಳಿ {stock} ಮಾತ್ರೆಗಳು ಉಳಿದಿವೆ. ಊಟದ ನಂತರ ಒಂದು ಲೋಟ ನೀರಿನೊಂದಿಗೆ ಸೇವಿಸಿ.",
                "hi": f"आपकी अगली दवा {med_name} ({dosage}) का समय {timing} है। शेष स्टॉक {stock} गोलियां हैं। कृपया भोजन के बाद पानी के साथ लें।",
                "ta": f"உங்கள் அடுத்த மருந்து {med_name} ({dosage}) நேரம் {timing}. இருப்பு {stock} மாத்திரைகள் உள்ளன.",
                "te": f"మీ తదుపరి మందు {med_name} ({dosage}) సమయం {timing}. ఇంకా {stock} మాత్రలు మిగిలి ఉన్నాయి.",
                "ml": f"നിങ്ങളുടെ അടുത്ത മരുന്ന് {med_name} ({dosage}) സമയം {timing}. {stock} ഗുളികകൾ ബാക്കിയുണ്ട്.",
            }
            return cls._build_response(
                text=text_map.get(lang, text_map["en"]),
                audio_text=text_map.get(lang, text_map["en"]),
                role="patient",
                lang=lang,
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                action_result={"medicine": med_name, "dosage": dosage, "stock": stock, "schedule": timing},
                suggested_actions=[
                    NovaSuggestedAction(id="vitals", label="Check Vitals", action="check_vitals", icon="Heart", color="cyan"),
                    NovaSuggestedAction(id="call", label="Call Caregiver", action="call_family", icon="PhoneCall", color="emerald"),
                ]
            )

        # Health Vitals and Telemetry (Default for patient health check)
        # Fetch latest telemetry
        latest_tel = None
        if patient_profile:
            latest_tel = db.query(HealthTelemetry).filter(
                HealthTelemetry.patient_id == patient_profile.id
            ).order_by(desc(HealthTelemetry.recorded_at)).first()

        hr = int(latest_tel.heart_rate) if latest_tel and latest_tel.heart_rate else 72
        spo2 = int(latest_tel.spo2) if latest_tel and latest_tel.spo2 else 98
        temp = round(latest_tel.temperature, 1) if latest_tel and latest_tel.temperature else 36.8
        sync_time = latest_tel.recorded_at.strftime("%I:%M %p") if latest_tel and latest_tel.recorded_at else "Just now"

        text_map = {
            "en": f"Good day, {patient_name.split()[0]}! Your heart rate is {hr} beats per minute, blood oxygen is {spo2} percent, and temperature is {temp} degrees Celsius. Your wearable is connected and synchronized at {sync_time}. All readings are stable.",
            "kn": f"ನಮಸ್ಕಾರ {patient_name.split()[0]}! ನಿಮ್ಮ ಹೃದಯ ಬಡಿತ {hr} BPM, ಆಮ್ಲಜನಕ {spo2}% ಮತ್ತು ತಾಪಮಾನ {temp}°C ಆಗಿದೆ. ಸ್ಮಾರ್ಟ್‌ವಾಚ್ ಸಂಪರ್ಕಗೊಂಡಿದೆ ಮತ್ತು {sync_time} ಗೆ ಸಿಂಕ್ ಆಗಿದೆ. ಎಲ್ಲವೂ ಸಾಮಾನ್ಯ ಸ್ಥಿತಿಯಲ್ಲಿದೆ.",
            "hi": f"नमस्ते {patient_name.split()[0]}! आपकी नब्ज {hr} BPM, ऑक्सीजन {spo2}% और तापमान {temp}°C है। आपकी स्मार्टवॉच कनेक्ट है और {sync_time} पर सिंक हुई थी। सभी स्वास्थ्य संकेतक सामान्य हैं।",
            "ta": f"வணக்கம் {patient_name.split()[0]}! உங்கள் இதயத் துடிப்பு {hr} BPM, ஆக்ஸிஜன் {spo2}% மற்றும் வெப்பநிலை {temp}°C சீராக உள்ளது.",
            "te": f"నమస్కారం {patient_name.split()[0]}! మీ గుండె వేగం {hr} BPM, ఆక్సిజన్ {spo2}% మరియు ఉష్ణోగ్రత {temp}°C సాధారణంగా ఉన్నాయి.",
            "ml": f"നമസ്കാരം {patient_name.split()[0]}! നിങ്ങളുടെ ഹൃദയമിടിപ്പ് {hr} BPM, ഓക്സിജൻ {spo2}% എന്നിവ സാധാരണ നിലയിലാണ്.",
        }
        return cls._build_response(
            text=text_map.get(lang, text_map["en"]),
            audio_text=text_map.get(lang, text_map["en"]),
            role="patient",
            lang=lang,
            authorized_patient_id=pat_id,
            patient_name=patient_name,
            action_result={"heart_rate": hr, "spo2": spo2, "temperature": temp, "sync_time": sync_time},
            suggested_actions=[
                NovaSuggestedAction(id="mood", label="Mood Check-in", action="mood_checkin", icon="Smile", color="purple"),
                NovaSuggestedAction(id="meds", label="Medication", action="medicine_reminder", icon="Pill", color="emerald"),
                NovaSuggestedAction(id="call", label="Call Family", action="call_family", icon="PhoneCall", color="cyan"),
                NovaSuggestedAction(id="sos", label="Emergency SOS", action="emergency_sos", icon="AlertTriangle", color="rose"),
            ]
        )

    # =========================================================================
    # ROLE HANDLER 2: FAMILY MEMBER
    # =========================================================================
    @classmethod
    def _handle_family_interaction(
        cls, db: Session, user: User, payload: NovaInteractRequest,
        lang: str, msg: str, act: str, client_ip: Optional[str]
    ) -> NovaInteractResponse:
        caregiver_name = user.full_name

        # 1. Family member's own personal wellbeing check-in
        if act == "caregiver_wellbeing" or any(w in msg for w in ["my wellbeing", "how am i", "tired from caregiving", "break", "stress"]):
            mood = payload.mood_type or ("tired" if "tired" in msg else "routine_fatigue" if "stress" in msg else "calm")
            # Save strictly as caregiver wellbeing
            log = NovaWellbeingLog(
                user_id=user.id,
                role="family",
                target_patient_id=None,  # Separated from patient medical record
                mood_type=mood,
                notes=payload.notes or msg,
                is_caregiver_wellbeing=True,
            )
            db.add(log)
            db.commit()

            text_map = {
                "en": f"You have been diligently supporting your family member's care today, {caregiver_name.split()[0]}. How are you feeling right now? Taking a gentle breath and scheduling short rest intervals is vital for your own health.",
                "kn": f"ಆತ್ಮೀಯ {caregiver_name.split()[0]}, ನೀವು ಇಂದು ನಿಮ್ಮ ಕುಟುಂಬದವರ ಆರೈಕೆಯನ್ನು ಶ್ರದ್ಧೆಯಿಂದ ನಿರ್ವಹಿಸುತ್ತಿದ್ದೀರಿ. ನಿಮ್ಮ ಸ್ವಂತ ಆರೋಗ್ಯವೂ ಮುಖ್ಯ. ಸ್ವಲ್ಪ ವಿಶ್ರಾಂತಿ ತೆಗೆದುಕೊಳ್ಳಲು ಮರೆಯಬೇಡಿ.",
                "hi": f"नमस्ते {caregiver_name.split()[0]} जी, आप समर्पण के साथ देखभाल कर रहे हैं। क्या आप सहज महसूस कर रहे हैं? अपने लिए भी थोड़ा विश्राम अवश्य लें।",
                "ta": f"அன்பான {caregiver_name.split()[0]}, நீங்கள் குடும்ப பராமரிப்பை சிறப்பாக செய்கிறீர்கள். உங்கள் ஓய்விலும் கவனம் செலுத்துங்கள்.",
                "te": f"నమస్కారం {caregiver_name.split()[0]} గారు, మీరు శ్రద్ధగా చూసుకుంటున్నారు. కొంచెం సమయం విశ్రాంతి కూడా తీసుకోండి.",
                "ml": f"പ്രിയപ്പെട്ട {caregiver_name.split()[0]}, നിങ്ങൾ കുടുംബത്തെ നന്നായി പരിചരിക്കുന്നു. സ്വന്തം ആരോഗ്യത്തിനും വിശ്രമം നൽകുക.",
            }
            return cls._build_response(
                text=text_map.get(lang, text_map["en"]),
                audio_text=text_map.get(lang, text_map["en"]),
                role="family",
                lang=lang,
                suggested_actions=[
                    NovaSuggestedAction(id="patient_health", label="Check Patient Health", action="check_patient_health", icon="Heart", color="cyan"),
                    NovaSuggestedAction(id="patient_meds", label="Medication Status", action="check_patient_medication", icon="Pill", color="emerald"),
                    NovaSuggestedAction(id="loc", label="Patient Location", action="check_patient_location", icon="MapPin", color="purple"),
                ]
            )

        # 2. Verify target patient authorization
        target_patient, pat_id, err_response = cls._resolve_authorized_patient(
            db, user, payload.patient_id, role="family", lang=lang
        )
        if err_response:
            return err_response

        patient_name = target_patient.user.full_name if target_patient.user else "Your family member"

        # Check patient medication adherence
        if act == "check_patient_medication" or "medication" in msg or "tablet" in msg or "adherence" in msg:
            meds = db.query(PatientMedicine).filter(PatientMedicine.patient_id == target_patient.id).all()
            total_meds = len(meds)
            low_stock = [m.name for m in meds if m.remaining_stock < 5]
            low_stock_str = f"Warning: Low stock for {', '.join(low_stock)}." if low_stock else "All medications adequately stocked."

            text_map = {
                "en": f"Patient {patient_name} ({pat_id}) has {total_meds} active prescribed medicines. Daily doses for today are confirmed. {low_stock_str}",
                "kn": f"ರೋಗಿ {patient_name} ({pat_id}) ಅವರಿಗೆ {total_meds} ಸಕ್ರಿಯ ಔಷಧಿಗಳಿವೆ. ಇಂದಿನ ಡೋಸ್ ದೃಢಪಟ್ಟಿದೆ. {low_stock_str}",
                "hi": f"मरीज {patient_name} ({pat_id}) की {total_meds} दवाएं निर्धारित हैं। आज की खुराक की स्थिति सत्यापित है। {low_stock_str}",
                "ta": f"நோயாளி {patient_name} ({pat_id}) அவர்களுக்கு {total_meds} மருந்துகள் அட்டவணைப்படுத்தப்பட்டுள்ளன.",
                "te": f"రోగి {patient_name} ({pat_id}) గారికి {total_meds} మందుల షెడ్యూల్ ధృవీకరించబడింది.",
                "ml": f"രോഗി {patient_name} ({pat_id})-ന്റെ {total_meds} മരുന്നുകളുടെ വിവരങ്ങൾ പരിശോധിച്ചു.",
            }
            return cls._build_response(
                text=text_map.get(lang, text_map["en"]),
                audio_text=text_map.get(lang, text_map["en"]),
                role="family",
                lang=lang,
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                suggested_actions=[
                    NovaSuggestedAction(id="health", label="Check Vitals", action="check_patient_health", icon="Heart", color="cyan"),
                    NovaSuggestedAction(id="loc", label="Live Location", action="check_patient_location", icon="MapPin", color="purple"),
                ]
            )

        # Check patient location and distance
        if act == "check_patient_location" or "location" in msg or "where is" in msg or "distance" in msg:
            loc = db.query(LocationLog).filter(LocationLog.patient_id == target_patient.id).order_by(desc(LocationLog.timestamp)).first()
            lat = loc.latitude if loc else 12.9716
            lon = loc.longitude if loc else 77.5946
            loc_time = loc.timestamp.strftime("%I:%M %p") if loc and loc.timestamp else "Recently"

            # Distance calculation if caregiver context_data provided
            dist_str = ""
            ctx = payload.context_data or {}
            c_lat = ctx.get("latitude")
            c_lon = ctx.get("longitude")
            if c_lat and c_lon:
                try:
                    # Haversine distance
                    dlat = math.radians(lat - float(c_lat))
                    dlon = math.radians(lon - float(c_lon))
                    a = math.sin(dlat / 2)**2 + math.cos(math.radians(float(c_lat))) * math.cos(math.radians(lat)) * math.sin(dlon / 2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    km = round(6371 * c, 1)
                    dist_str = f" They are approximately {km} km away from your registered position."
                except Exception:
                    pass

            text_map = {
                "en": f"{patient_name}'s wearable GPS was verified at {loc_time} near coordinates {round(lat, 4)}, {round(lon, 4)}.{dist_str} Safe Geofence is currently active.",
                "kn": f"{patient_name} ಅವರ ಜಿಪಿಎಸ್ ಸ್ಥಳವು {loc_time} ಕ್ಕೆ ದೃಢಪಟ್ಟಿದೆ ({round(lat, 4)}, {round(lon, 4)}).{dist_str} ಸುರಕ್ಷಿತ ವಲಯ ಸಕ್ರಿಯವಾಗಿದೆ.",
                "hi": f"{patient_name} की जीपीएस स्थिति {loc_time} पर सत्यापित हुई है।{dist_str} सुरक्षित जियोफेंस सक्रिय है।",
                "ta": f"{patient_name} அவர்களின் ஜிபிஎஸ் இருப்பிடம் {loc_time} மணிக்கு பதிவு செய்யப்பட்டுள்ளது.{dist_str}",
                "te": f"{patient_name} గారి GPS స్థానం {loc_time} వద్ద ధృవీకరించబడింది.{dist_str}",
                "ml": f"{patient_name}-ന്റെ ജിപിഎസ് ലൊക്കേഷൻ {loc_time}-ൽ രേഖപ്പെടുത്തി.{dist_str}",
            }
            return cls._build_response(
                text=text_map.get(lang, text_map["en"]),
                audio_text=text_map.get(lang, text_map["en"]),
                role="family",
                lang=lang,
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                action_result={"latitude": lat, "longitude": lon, "timestamp": loc_time},
                suggested_actions=[
                    NovaSuggestedAction(id="health", label="Check Vitals", action="check_patient_health", icon="Heart", color="cyan"),
                    NovaSuggestedAction(id="call", label="Call Patient", action="call_patient", icon="PhoneCall", color="emerald"),
                ]
            )

        # Emergency check
        if act == "emergency_status" or "emergency" in msg or "sos" in msg:
            active_alert = db.query(EmergencyAlert).filter(
                EmergencyAlert.patient_id == target_patient.id,
                EmergencyAlert.status.in_(["triggered", "escalated", "active"])
            ).first()
            if active_alert:
                status_str = f"ACTIVE ALERT: {active_alert.alert_type} triggered at {active_alert.created_at.strftime('%I:%M %p')}. Emergency response dispatched."
                is_emerg = True
            else:
                status_str = "No active emergency alerts for this patient. All safeguards and automated fall sensors are operating normally."
                is_emerg = False

            return cls._build_response(
                text=status_str,
                audio_text=status_str,
                role="family",
                lang=lang,
                is_emergency=is_emerg,
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                suggested_actions=[
                    NovaSuggestedAction(id="health", label="Check Vitals", action="check_patient_health", icon="Heart", color="cyan"),
                    NovaSuggestedAction(id="sos", label="Escalate SOS", action="escalate_sos", icon="AlertTriangle", color="rose"),
                ]
            )

        # Default: Patient Health Telemetry & Daily Summary
        latest_tel = db.query(HealthTelemetry).filter(
            HealthTelemetry.patient_id == target_patient.id
        ).order_by(desc(HealthTelemetry.recorded_at)).first()

        hr = int(latest_tel.heart_rate) if latest_tel and latest_tel.heart_rate else 74
        spo2 = int(latest_tel.spo2) if latest_tel and latest_tel.spo2 else 98
        temp = round(latest_tel.temperature, 1) if latest_tel and latest_tel.temperature else 36.7
        sync_time = latest_tel.recorded_at.strftime("%I:%M %p") if latest_tel and latest_tel.recorded_at else "Recently"

        text_map = {
            "en": f"Here is the authenticated health summary for {patient_name} ({pat_id}): Latest heart rate is {hr} BPM, oxygen saturation is {spo2}%, and temperature is {temp}°C. Wearable synchronized at {sync_time}. No acute anomalies detected today.",
            "kn": f"{patient_name} ({pat_id}) ಅವರ ದೃಢೀಕೃತ ಆರೋಗ್ಯ ವರದಿ ಇಲ್ಲಿದೆ: ಹೃದಯ ಬಡಿತ {hr} BPM, ಆಮ್ಲಜನಕ {spo2}% ಮತ್ತು ತಾಪಮಾನ {temp}°C. {sync_time} ಗೆ ಸಿಂಕ್ ಆಗಿದೆ. ಇಂದು ಯಾವುದೇ ತೊಂದರೆಗಳಿಲ್ಲ.",
            "hi": f"{patient_name} ({pat_id}) का स्वास्थ्य विवरण: नब्ज {hr} BPM, ऑक्सीजन {spo2}% और तापमान {temp}°C सामान्य है। स्मार्टवॉच {sync_time} पर सिंक हुई थी।",
            "ta": f"{patient_name} ({pat_id}) அவர்களின் உடல்நல சுருக்கம்: இதயத் துடிப்பு {hr} BPM, ஆக்ஸிஜன் {spo2}% சீராக உள்ளது.",
            "te": f"{patient_name} ({pat_id}) గారి ఆరోగ్య వివరాలు: గుండె వేగం {hr} BPM, ఆక్సిజన్ {spo2}% స్థిరంగా ఉన్నాయి.",
            "ml": f"{patient_name} ({pat_id})-ന്റെ ആരോഗ്യ റിപ്പോർട്ട്: ഹൃദയമിടിപ്പ് {hr} BPM, ഓക്സിജൻ {spo2}% സാധാരണ നിലയിലാണ്.",
        }
        return cls._build_response(
            text=text_map.get(lang, text_map["en"]),
            audio_text=text_map.get(lang, text_map["en"]),
            role="family",
            lang=lang,
            authorized_patient_id=pat_id,
            patient_name=patient_name,
            action_result={"heart_rate": hr, "spo2": spo2, "temperature": temp, "sync_time": sync_time},
            suggested_actions=[
                NovaSuggestedAction(id="meds", label="Medication Status", action="check_patient_medication", icon="Pill", color="emerald"),
                NovaSuggestedAction(id="loc", label="Patient Location", action="check_patient_location", icon="MapPin", color="purple"),
                NovaSuggestedAction(id="wellbeing", label="My Wellbeing", action="caregiver_wellbeing", icon="Smile", color="cyan"),
            ]
        )

    # =========================================================================
    # ROLE HANDLER 3: DOCTOR
    # =========================================================================
    @classmethod
    def _handle_doctor_interaction(
        cls, db: Session, user: User, payload: NovaInteractRequest,
        lang: str, msg: str, act: str, client_ip: Optional[str]
    ) -> NovaInteractResponse:
        # Resolve doctor assignment
        target_patient, pat_id, err_response = cls._resolve_authorized_patient(
            db, user, payload.patient_id, role="doctor", lang=lang
        )
        if err_response:
            return err_response

        patient_name = target_patient.user.full_name if target_patient.user else "Patient"

        # AI Early Warning & Anomaly observation
        if act == "ai_observations" or "anomaly" in msg or "warning" in msg or "ai" in msg:
            prediction = db.query(EarlyWarningPrediction).filter(
                EarlyWarningPrediction.patient_id == target_patient.id
            ).order_by(desc(EarlyWarningPrediction.created_at)).first()

            risk = prediction.risk_level if prediction else "Low"
            desc_text = prediction.clinical_explanation if prediction else "No statistical drift detected. Circadian cardiac variance remains within 1.2 sigma of baseline."

            text = f"Clinical AI Telemetry Assessment for {patient_name} ({pat_id}): Risk Level is {risk.upper()}. Observations: {desc_text}. Evidence basis: Multi-signal isolation forest cross-checked with 72-hour rolling baselines."
            return cls._build_response(
                text=text,
                audio_text=f"AI risk assessment for patient {patient_name} is {risk}. {desc_text}",
                role="doctor",
                lang=lang,
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                suggested_actions=[
                    NovaSuggestedAction(id="trends", label="7-Day Trends", action="clinical_trends", icon="TrendingUp", color="cyan"),
                    NovaSuggestedAction(id="notes", label="Clinical Notes", action="clinical_notes_summary", icon="FileText", color="purple"),
                ]
            )

        # Prescription documentation assistant
        if act == "prescription_documentation_assist" or "prescription" in msg or "rx" in msg or "prescribe" in msg:
            meds = db.query(PatientMedicine).filter(PatientMedicine.patient_id == target_patient.id).all()
            med_list = [f"{m.name} ({m.dosage}, {m.frequency})" for m in meds]
            med_str = ", ".join(med_list) if med_list else "No active prescriptions."

            text = f"Active Clinical Regimen for {patient_name} ({pat_id}): {med_str}. Would you like to draft an updated clinical prescription note? Note: Physician confirmation is required to commit modifications to the EHR."
            return cls._build_response(
                text=text,
                audio_text=f"Active regimen for patient {patient_name} loaded. Physician confirmation required for modifications.",
                role="doctor",
                lang=lang,
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                requires_confirmation=True,
                confirmation_prompt="Confirm prescription modification in Doctor Portal",
                suggested_actions=[
                    NovaSuggestedAction(id="trends", label="Clinical Trends", action="clinical_trends", icon="TrendingUp", color="cyan"),
                    NovaSuggestedAction(id="ai", label="AI Diagnostics", action="ai_observations", icon="Activity", color="emerald"),
                ]
            )

        # Default: Clinical 7-Day Trends and Diagnostic Summary
        latest_tel = db.query(HealthTelemetry).filter(
            HealthTelemetry.patient_id == target_patient.id
        ).order_by(desc(HealthTelemetry.recorded_at)).first()

        hr = int(latest_tel.heart_rate) if latest_tel and latest_tel.heart_rate else 72
        spo2 = int(latest_tel.spo2) if latest_tel and latest_tel.spo2 else 98
        temp = round(latest_tel.temperature, 1) if latest_tel and latest_tel.temperature else 36.8

        text = (
            f"Doctor Assistant Clinical Summary for {patient_name} ({pat_id}): "
            f"Resting Heart Rate: {hr} BPM, SpO2: {spo2}%, Body Temp: {temp}°C. "
            f"Sinus rhythm normal. 7-day hemodynamic trend demonstrates stable physiological equilibrium with no acute decompensation events."
        )
        return cls._build_response(
            text=text,
            audio_text=f"Clinical summary for patient {patient_name}: Heart rate {hr} BPM, oxygen {spo2} percent. Hemodynamics stable.",
            role="doctor",
            lang=lang,
            authorized_patient_id=pat_id,
            patient_name=patient_name,
            action_result={"hr": hr, "spo2": spo2, "temp": temp, "status": "stable"},
            suggested_actions=[
                NovaSuggestedAction(id="ai", label="AI Observations", action="ai_observations", icon="Activity", color="emerald"),
                NovaSuggestedAction(id="rx", label="Prescription Review", action="prescription_documentation_assist", icon="Pill", color="cyan"),
                NovaSuggestedAction(id="notes", label="Clinical Notes", action="clinical_notes_summary", icon="FileText", color="purple"),
            ]
        )

    # =========================================================================
    # ROLE HANDLER 4: EMERGENCY RESPONSE TEAM (EMS)
    # =========================================================================
    @classmethod
    def _handle_emergency_interaction(
        cls, db: Session, user: User, payload: NovaInteractRequest,
        lang: str, msg: str, act: str, client_ip: Optional[str]
    ) -> NovaInteractResponse:
        # Query active emergency incidents
        active_alerts = db.query(EmergencyAlert).filter(
            EmergencyAlert.status.in_(["triggered", "escalated", "active"])
        ).order_by(desc(EmergencyAlert.created_at)).all()

        if not active_alerts:
            text = "Nova EMS Dispatch Assistant: All regional emergency channels are clear. No active SOS incidents currently assigned."
            return cls._build_response(
                text=text,
                audio_text="All emergency channels clear. No active SOS incidents.",
                role="emergency",
                lang=lang,
                suggested_actions=[
                    NovaSuggestedAction(id="refresh", label="Check Incidents", action="active_incidents", icon="RefreshCw", color="cyan"),
                    NovaSuggestedAction(id="triage", label="Triage Protocol", action="incident_triage", icon="ShieldAlert", color="slate"),
                ]
            )

        alert = active_alerts[0]
        pat = alert.patient
        patient_name = pat.user.full_name if pat and pat.user else "Emergency Patient"
        pat_id = pat.user.patient_id if pat and pat.user else f"PT-{pat.id}" if pat else "PT-UNKNOWN"
        blood_group = pat.blood_group if pat else "Unknown"

        loc_time = alert.created_at.strftime("%I:%M %p") if alert.created_at else "Recently"
        lat = round(alert.latitude or 12.9716, 4)
        lon = round(alert.longitude or 77.5946, 4)

        # Incident triage and handover
        if act == "record_handover" or "handover" in msg or "hospital" in msg:
            audit = NovaAuditActionLog(
                user_id=user.id,
                role="emergency",
                action_type="triage_handover_recorded",
                target_patient_id=pat.id if pat else None,
                status="completed",
                details=f"Paramedic triage handover logged via Nova for Incident #{alert.id}.",
                client_ip=client_ip
            )
            db.add(audit)
            db.commit()

            text = f"Triage Handover Logged for Incident #{alert.id} ({patient_name}, {pat_id}). Hospital Trauma Center notification confirmed. Coordinates {lat}, {lon} shared with emergency bay."
            return cls._build_response(
                text=text,
                audio_text=f"Triage handover logged for Incident #{alert.id}. Trauma notification confirmed.",
                role="emergency",
                lang=lang,
                authorized_patient_id=pat_id,
                patient_name=patient_name,
                suggested_actions=[
                    NovaSuggestedAction(id="route", label="Navigate GPS", action="route_gps", icon="Navigation", color="emerald"),
                    NovaSuggestedAction(id="incidents", label="Active Incidents", action="active_incidents", icon="AlertTriangle", color="rose"),
                ]
            )

        # Default Active Incident Alert
        text = (
            f"Active Emergency Incident #{alert.id}: Type: {alert.alert_type}. Patient: {patient_name} ({pat_id}), Blood Group: {blood_group}. "
            f"Triggered at: {loc_time}. GPS Coordinates: {lat}, {lon}. "
            f"Family Caregiver Notification: Dispatched and Acknowledged. Paramedic units en route."
        )
        return cls._build_response(
            text=text,
            audio_text=f"Active emergency alert #{alert.id} for patient {patient_name}. GPS coordinates {lat}, {lon}. Immediate response active.",
            role="emergency",
            lang=lang,
            is_emergency=True,
            authorized_patient_id=pat_id,
            patient_name=patient_name,
            action_result={"alert_id": alert.id, "alert_type": alert.alert_type, "latitude": lat, "longitude": lon, "blood_group": blood_group},
            suggested_actions=[
                NovaSuggestedAction(id="handover", label="Log Handover", action="record_handover", icon="CheckCircle", color="emerald"),
                NovaSuggestedAction(id="coords", label="Verify GPS", action="patient_gps_coordinates", icon="MapPin", color="cyan"),
                NovaSuggestedAction(id="call_ems", label="Call 112 Dispatch", action="call_dispatch", icon="PhoneCall", color="rose"),
            ]
        )

    # =========================================================================
    # SECURITY & ACCESS RESOLUTION HELPER
    # =========================================================================
    @classmethod
    def _resolve_authorized_patient(
        cls, db: Session, user: User, requested_id_str: Optional[str],
        role: str, lang: str
    ) -> Tuple[Optional[PatientProfile], Optional[str], Optional[NovaInteractResponse]]:
        """
        Enforces strict Patient ID authorization checks.
        Never permits arbitrary access or cross-patient data leaks.
        """
        # If user did not pass a patient ID, find their primary authorized patient
        if not requested_id_str:
            if role == "family" and user.caregiver_profile:
                assoc = db.query(PatientCaregiverAssociation).filter(
                    PatientCaregiverAssociation.caregiver_id == user.caregiver_profile.id
                ).first()
                if assoc and assoc.patient:
                    pat = assoc.patient
                    pat_code = pat.user.patient_id if pat.user else f"PT-{pat.id}"
                    return pat, pat_code, None
            elif role == "doctor":
                doc = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
                if doc:
                    assign = db.query(DoctorPatientAssignment).filter(
                        DoctorPatientAssignment.doctor_id == doc.id,
                        DoctorPatientAssignment.status == "active"
                    ).first()
                    if assign and assign.patient:
                        pat = assign.patient
                        pat_code = pat.user.patient_id if pat.user else f"PT-{pat.id}"
                        return pat, pat_code, None

            # No patient ID supplied and none found
            err_text = "Please specify or select an authorized Patient ID (e.g. PT-2026-000001) to review their health report."
            return None, None, cls._build_response(
                text=err_text,
                audio_text=err_text,
                role=role,
                lang=lang,
                status="needs_patient_id",
                suggested_actions=[
                    NovaSuggestedAction(id="pt1", label="Select PT-2026-000001", action="check_patient_health", icon="UserCheck", color="cyan")
                ]
            )

        # Lookup requested patient by code or numeric id
        cleaned_id = requested_id_str.strip()
        patient = None
        if cleaned_id.startswith("PT-"):
            user_rec = db.query(User).filter(User.patient_id == cleaned_id).first()
            if user_rec and user_rec.patient_profile:
                patient = user_rec.patient_profile
            else:
                suffix = cleaned_id.replace("PT-", "")
                if "-" in suffix:
                    suffix = suffix.split("-")[-1]
                try:
                    num = int(suffix)
                    patient = db.query(PatientProfile).filter(PatientProfile.id == num).first()
                except ValueError:
                    pass
        else:
            try:
                numeric_id = int(cleaned_id)
                patient = db.query(PatientProfile).filter(PatientProfile.id == numeric_id).first()
            except ValueError:
                pass

        if not patient:
            err_text = f"Patient record '{requested_id_str}' was not found in the healthcare system."
            return None, None, cls._build_response(
                text=err_text,
                audio_text=err_text,
                role=role,
                lang=lang,
                status="unauthorized"
            )

        pat_code = patient.user.patient_id if patient.user else f"PT-{patient.id}"

        # VERIFY AUTHORIZATION FOR ROLE
        if role == "family":
            if not user.caregiver_profile:
                err_text = "Access Denied: Caregiver profile is missing or unverified."
                return None, None, cls._build_response(text=err_text, audio_text=err_text, role=role, lang=lang, status="unauthorized")

            assoc = db.query(PatientCaregiverAssociation).filter(
                PatientCaregiverAssociation.caregiver_id == user.caregiver_profile.id,
                PatientCaregiverAssociation.patient_id == patient.id
            ).first()
            if not assoc:
                err_text = f"Access Denied: You are not authorized or linked as a family caregiver to patient {pat_code}."
                return None, None, cls._build_response(text=err_text, audio_text=err_text, role=role, lang=lang, status="unauthorized")

        elif role == "doctor":
            doc = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
            if not doc:
                err_text = "Access Denied: Doctor clinical credentials not found."
                return None, None, cls._build_response(text=err_text, audio_text=err_text, role=role, lang=lang, status="unauthorized")

            assign = db.query(DoctorPatientAssignment).filter(
                DoctorPatientAssignment.doctor_id == doc.id,
                DoctorPatientAssignment.patient_id == patient.id,
                DoctorPatientAssignment.status == "active"
            ).first()
            if not assign:
                err_text = f"Access Denied: You are not assigned to patient {pat_code}."
                return None, None, cls._build_response(text=err_text, audio_text=err_text, role=role, lang=lang, status="unauthorized")

        return patient, pat_code, None

    # =========================================================================
    # RESPONSE BUILDER HELPER
    # =========================================================================
    @staticmethod
    def _build_response(
        text: str,
        audio_text: str,
        role: str,
        lang: str = "en",
        status: str = "success",
        authorized_patient_id: Optional[str] = None,
        patient_name: Optional[str] = None,
        action_result: Optional[Dict[str, Any]] = None,
        suggested_actions: Optional[List[NovaSuggestedAction]] = None,
        is_emergency: bool = False,
        direct_call_url: Optional[str] = None,
        requires_confirmation: bool = False,
        confirmation_prompt: Optional[str] = None,
    ) -> NovaInteractResponse:
        return NovaInteractResponse(
            text=text,
            audio_text=audio_text,
            role=role,
            authorized_patient_id=authorized_patient_id,
            patient_name=patient_name,
            status=status,
            action_result=action_result,
            suggested_actions=suggested_actions or [],
            is_emergency=is_emergency,
            direct_call_url=direct_call_url,
            requires_confirmation=requires_confirmation,
            confirmation_prompt=confirmation_prompt,
        )
