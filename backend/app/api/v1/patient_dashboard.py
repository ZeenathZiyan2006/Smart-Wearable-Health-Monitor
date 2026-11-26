"""
Patient Dashboard API Routes:
Live Metrics, Medicines, Reminders, Appointments, Medical History, Allergies, Hydration
"""
from datetime import datetime, timezone, timedelta
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.api.v1.health import _check_patient_read_permission
from app.models.user import User, UserRole, PatientProfile, PatientCaregiverAssociation, FamilyAccount, FamilyPatientRelationship
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
)
from app.schemas.dashboard import (
    PatientMedicineCreate,
    PatientMedicineUpdate,
    PatientMedicineOut,
    MedicineActionRequest,
    MedicineIntakeLogOut,
    PatientReminderCreate,
    PatientReminderUpdate,
    PatientReminderOut,
    DoctorAppointmentCreate,
    DoctorAppointmentUpdate,
    DoctorAppointmentOut,
    MedicalConditionCreate,
    MedicalConditionOut,
    AllergyCreate,
    AllergyOut,
    HydrationLogCreate,
    HydrationSummaryOut,
)

router = APIRouter()


def resolve_patient_profile(current_user: User, patient_id: Optional[int], db: Session) -> PatientProfile:
    """
    Enforces strict patient data isolation.
    - An authenticated patient can ONLY access their own health records.
    - If a patient specifies a different patient_id in URLs/queries/payloads, access is denied (403 Forbidden).
    - Caregivers and family accounts must be verified and authorized for the target patient.
    """
    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role_str == "patient":
        if not current_user.patient_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found.")
        if patient_id is not None and patient_id != current_user.patient_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to access another patient's health records."
            )
        return current_user.patient_profile

    if user_role_str == "admin":
        if patient_id:
            profile = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
            if not profile:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target patient not found.")
            return profile
        first_p = db.query(PatientProfile).first()
        if not first_p:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No patient profiles exist.")
        return first_p

    # Caregivers / Guardians / Family members
    if patient_id:
        target_profile = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        if not target_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target patient not found.")
        _check_patient_read_permission(db, target_profile.id, current_user)
        return target_profile

    if user_role_str == "caregiver" and current_user.caregiver_profile and current_user.caregiver_profile.patient_associations:
        return current_user.caregiver_profile.patient_associations[0].patient

    fam_rel = db.query(FamilyPatientRelationship).join(
        FamilyAccount, FamilyPatientRelationship.family_account_id == FamilyAccount.id
    ).filter(
        FamilyAccount.family_email == current_user.email,
        FamilyPatientRelationship.is_authorized == True
    ).first()
    if fam_rel and fam_rel.patient_profile:
        return fam_rel.patient_profile

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient identification required.")


# ==========================================
# MODULE 4: Medicine Management
# ==========================================
@router.get("/medicines", response_model=List[PatientMedicineOut])
def get_medicines(
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    meds = db.query(PatientMedicine).filter(PatientMedicine.patient_id == patient.id).order_by(desc(PatientMedicine.created_at)).all()
    
    now = datetime.now(timezone.utc)
    results = []
    for m in meds:
        consumed = m.total_quantity - m.remaining_quantity
        is_low = m.remaining_quantity <= 5
        is_exp = bool(m.expiry_date and (m.expiry_date.replace(tzinfo=timezone.utc) if m.expiry_date.tzinfo is None else m.expiry_date) < now)
        results.append(
            PatientMedicineOut(
                id=m.id,
                patient_id=m.patient_id,
                medicine_name=m.medicine_name,
                dosage=m.dosage,
                frequency=m.frequency,
                scheduled_times=m.scheduled_times,
                start_date=m.start_date,
                end_date=m.end_date,
                expiry_date=m.expiry_date,
                total_quantity=m.total_quantity,
                remaining_quantity=m.remaining_quantity,
                medicine_status=m.medicine_status,
                consumed_quantity=max(0, consumed),
                is_low_stock=is_low,
                is_expired=is_exp,
                notes=m.notes,
                created_at=m.created_at
            )
        )
    return results


@router.post("/medicines", response_model=PatientMedicineOut, status_code=status.HTTP_201_CREATED)
def add_medicine(
    payload: PatientMedicineCreate,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    med = PatientMedicine(
        patient_id=patient.id,
        medicine_name=payload.medicine_name.strip(),
        dosage=payload.dosage.strip(),
        frequency=payload.frequency.strip(),
        scheduled_times=payload.scheduled_times.strip(),
        start_date=payload.start_date or datetime.now(timezone.utc),
        end_date=payload.end_date,
        expiry_date=payload.expiry_date,
        total_quantity=payload.total_quantity,
        remaining_quantity=payload.remaining_quantity,
        medicine_status=payload.medicine_status,
        notes=payload.notes
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


@router.put("/medicines/{medicine_id}", response_model=PatientMedicineOut)
def update_medicine(
    medicine_id: int,
    payload: PatientMedicineUpdate,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    med = db.query(PatientMedicine).filter(PatientMedicine.id == medicine_id, PatientMedicine.patient_id == patient.id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(med, field, val)

    db.commit()
    db.refresh(med)
    return med


@router.post("/medicines/{medicine_id}/action", response_model=MedicineIntakeLogOut)
def record_medicine_action(
    medicine_id: int,
    action: MedicineActionRequest,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    med = db.query(PatientMedicine).filter(PatientMedicine.id == medicine_id, PatientMedicine.patient_id == patient.id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")

    sched_time = action.scheduled_time or datetime.now(timezone.utc)
    log = MedicineIntakeLog(
        medicine_id=med.id,
        patient_id=patient.id,
        scheduled_time=sched_time,
        status=action.status,
        notes=action.notes
    )
    db.add(log)

    if action.status == "taken" and med.remaining_quantity > 0:
        med.remaining_quantity -= 1

    db.commit()
    db.refresh(log)
    return log


@router.delete("/medicines/{medicine_id}", status_code=status.HTTP_200_OK)
def delete_medicine(
    medicine_id: int,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    med = db.query(PatientMedicine).filter(PatientMedicine.id == medicine_id, PatientMedicine.patient_id == patient.id).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found.")
    db.delete(med)
    db.commit()
    return {"status": "success", "message": f"Medicine '{med.medicine_name}' removed."}


# ==========================================
# MODULE 5: Smart Reminders & Alarms
# ==========================================
@router.get("/reminders", response_model=List[PatientReminderOut])
def get_reminders(
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    return db.query(PatientReminder).filter(PatientReminder.patient_id == patient.id).all()


@router.post("/reminders", response_model=PatientReminderOut, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: PatientReminderCreate,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    rem = PatientReminder(
        patient_id=patient.id,
        title=payload.title.strip(),
        reminder_type=payload.reminder_type,
        reminder_time=payload.reminder_time.strip(),
        is_enabled=payload.is_enabled,
        recurring_days=payload.recurring_days,
        alarm_tone=payload.alarm_tone,
        volume=payload.volume,
        vibration_enabled=payload.vibration_enabled,
        snooze_interval_minutes=payload.snooze_interval_minutes
    )
    db.add(rem)
    db.commit()
    db.refresh(rem)
    return rem


@router.put("/reminders/{reminder_id}", response_model=PatientReminderOut)
def update_reminder(
    reminder_id: int,
    payload: PatientReminderUpdate,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    rem = db.query(PatientReminder).filter(PatientReminder.id == reminder_id, PatientReminder.patient_id == patient.id).first()
    if not rem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(rem, field, val)

    db.commit()
    db.refresh(rem)
    return rem


@router.delete("/reminders/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    rem = db.query(PatientReminder).filter(PatientReminder.id == reminder_id, PatientReminder.patient_id == patient.id).first()
    if not rem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found.")
    db.delete(rem)
    db.commit()
    return {"status": "success", "message": "Reminder deleted."}


# ==========================================
# MODULE 7: Doctor Appointments
# ==========================================
@router.get("/appointments", response_model=List[DoctorAppointmentOut])
def get_appointments(
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    return db.query(DoctorAppointment).filter(DoctorAppointment.patient_id == patient.id).order_by(DoctorAppointment.appointment_date).all()


@router.post("/appointments", response_model=DoctorAppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: DoctorAppointmentCreate,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    app = DoctorAppointment(
        patient_id=patient.id,
        doctor_name=payload.doctor_name.strip(),
        specialization=payload.specialization.strip(),
        hospital_name=payload.hospital_name.strip(),
        phone_number=payload.phone_number,
        appointment_date=payload.appointment_date,
        reason=payload.reason,
        notes=payload.notes,
        status="confirmed"
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.put("/appointments/{appointment_id}", response_model=DoctorAppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: DoctorAppointmentUpdate,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    app = db.query(DoctorAppointment).filter(DoctorAppointment.id == appointment_id, DoctorAppointment.patient_id == patient.id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(app, field, val)

    db.commit()
    db.refresh(app)
    return app


# ==========================================
# MODULE 2: Conditions & Allergies
# ==========================================
@router.get("/conditions", response_model=List[MedicalConditionOut])
def get_conditions(
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    return db.query(PatientMedicalCondition).filter(PatientMedicalCondition.patient_id == patient.id).all()


@router.post("/conditions", response_model=MedicalConditionOut, status_code=status.HTTP_201_CREATED)
def add_condition(
    payload: MedicalConditionCreate,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    cond = PatientMedicalCondition(
        patient_id=patient.id,
        condition_name=payload.condition_name.strip(),
        diagnosed_date=payload.diagnosed_date,
        severity=payload.severity,
        status=payload.status,
        notes=payload.notes
    )
    db.add(cond)
    db.commit()
    db.refresh(cond)
    return cond


@router.get("/allergies", response_model=List[AllergyOut])
def get_allergies(
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    return db.query(PatientAllergy).filter(PatientAllergy.patient_id == patient.id).all()


@router.post("/allergies", response_model=AllergyOut, status_code=status.HTTP_201_CREATED)
def add_allergy(
    payload: AllergyCreate,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    allergy = PatientAllergy(
        patient_id=patient.id,
        allergen=payload.allergen.strip(),
        reaction=payload.reaction,
        severity=payload.severity
    )
    db.add(allergy)
    db.commit()
    db.refresh(allergy)
    return allergy


# ==========================================
# Hydration Tracking
# ==========================================
@router.get("/hydration", response_model=HydrationSummaryOut)
def get_hydration(
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    logs = db.query(PatientHydrationLog).filter(
        PatientHydrationLog.patient_id == patient.id,
        PatientHydrationLog.logged_at >= today_start
    ).all()
    
    total = sum(l.intake_ml for l in logs)
    target = 2500
    pct = round((total / target) * 100, 1)
    return {
        "total_intake_ml": total,
        "target_intake_ml": target,
        "percentage": pct,
        "logs_count": len(logs)
    }


@router.post("/hydration", response_model=HydrationSummaryOut)
def log_hydration(
    payload: HydrationLogCreate,
    patient_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    patient = resolve_patient_profile(current_user, patient_id, db)
    log = PatientHydrationLog(
        patient_id=patient.id,
        intake_ml=payload.intake_ml
    )
    db.add(log)
    db.commit()
    return get_hydration(patient_id=patient.id, current_user=current_user, db=db)
