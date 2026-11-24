from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import RoleChecker, get_current_active_user, get_db
from app.models.user import (
    CaregiverProfile,
    PatientCaregiverAssociation,
    PatientProfile,
    User,
    UserRole,
)
from app.schemas.user import (
    CaregiverProfileOut,
    CaregiverProfileUpdate,
    PatientCaregiverAssociationCreate,
    PatientCaregiverAssociationOut,
    PatientCaregiverAssociationUpdate,
    PatientProfileOut,
    PatientProfileUpdate,
    UserProfileOut,
)

router = APIRouter()

allow_caregiver_or_admin = RoleChecker([UserRole.CAREGIVER.value, UserRole.ADMIN.value])
allow_admin = RoleChecker([UserRole.ADMIN.value])


# -----------------------------------------------------------------------------
# Patient Endpoints
# -----------------------------------------------------------------------------
@router.get("/patients", response_model=List[PatientProfileOut])
def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    device_uuid: Optional[str] = None,
    current_user: User = Depends(allow_caregiver_or_admin),
    db: Session = Depends(get_db)
) -> Any:
    """
    List registered patients. Accessible by caregivers and admins.
    """
    query = db.query(PatientProfile)
    if device_uuid:
        query = query.filter(PatientProfile.device_uuid == device_uuid)
    return query.offset(skip).limit(limit).all()


@router.get("/patients/{patient_id}", response_model=PatientProfileOut)
def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve details of a specific patient profile.
    Patients can access their own; caregivers/admins can access associated profiles.
    """
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient profile with id {patient_id} not found"
        )

    # Permission check: patient can view self, caregiver can view assigned or admin can view all
    if current_user.role == UserRole.PATIENT.value and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only view your own patient profile"
        )

    return patient


@router.put("/patients/{patient_id}", response_model=PatientProfileOut)
def update_patient_profile(
    patient_id: int,
    profile_in: PatientProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update patient health information, device UUID, and emergency contacts.
    """
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient profile with id {patient_id} not found"
        )

    if current_user.role == UserRole.PATIENT.value and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only edit your own profile"
        )

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


# -----------------------------------------------------------------------------
# Caregiver Endpoints
# -----------------------------------------------------------------------------
@router.get("/caregivers", response_model=List[CaregiverProfileOut])
def list_caregivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List caregivers registered in the system.
    """
    return db.query(CaregiverProfile).offset(skip).limit(limit).all()


@router.get("/caregivers/{caregiver_id}", response_model=CaregiverProfileOut)
def get_caregiver(
    caregiver_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve details of a specific caregiver profile.
    """
    caregiver = db.query(CaregiverProfile).filter(CaregiverProfile.id == caregiver_id).first()
    if not caregiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caregiver profile with id {caregiver_id} not found"
        )
    return caregiver


@router.put("/caregivers/{caregiver_id}", response_model=CaregiverProfileOut)
def update_caregiver_profile(
    caregiver_id: int,
    profile_in: CaregiverProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update caregiver relationship type, organization, and notification preferences.
    """
    caregiver = db.query(CaregiverProfile).filter(CaregiverProfile.id == caregiver_id).first()
    if not caregiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caregiver profile with id {caregiver_id} not found"
        )

    if current_user.role == UserRole.CAREGIVER.value and caregiver.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only edit your own profile"
        )

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(caregiver, field, value)

    db.commit()
    db.refresh(caregiver)
    return caregiver


# -----------------------------------------------------------------------------
# Patient-Caregiver Association Endpoints
# -----------------------------------------------------------------------------
@router.post("/associations", response_model=PatientCaregiverAssociationOut, status_code=status.HTTP_201_CREATED)
def link_patient_and_caregiver(
    association_in: PatientCaregiverAssociationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Establish an association between a patient and a caregiver with designated
    escalation tier and access privileges.
    """
    # 1. Verify patient exists
    patient = db.query(PatientProfile).filter(PatientProfile.id == association_in.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with id {association_in.patient_id} not found"
        )

    # 2. Verify caregiver exists
    caregiver = db.query(CaregiverProfile).filter(CaregiverProfile.id == association_in.caregiver_id).first()
    if not caregiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caregiver with id {association_in.caregiver_id} not found"
        )

    # 3. Check for existing link
    existing = db.query(PatientCaregiverAssociation).filter(
        PatientCaregiverAssociation.patient_id == association_in.patient_id,
        PatientCaregiverAssociation.caregiver_id == association_in.caregiver_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This patient and caregiver are already linked"
        )

    # If new association is primary, reset any previous primary caregiver for this patient
    if association_in.is_primary:
        db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.patient_id == association_in.patient_id,
            PatientCaregiverAssociation.is_primary == True  # noqa: E712
        ).update({"is_primary": False})

    association = PatientCaregiverAssociation(
        patient_id=association_in.patient_id,
        caregiver_id=association_in.caregiver_id,
        is_primary=association_in.is_primary,
        access_level=association_in.access_level,
        escalation_tier=association_in.escalation_tier
    )
    db.add(association)
    db.commit()
    db.refresh(association)
    return association


@router.get("/patients/{patient_id}/caregivers", response_model=List[PatientCaregiverAssociationOut])
def get_patient_caregivers(
    patient_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all caregivers linked to a patient, ordered by escalation tier (1 -> 2 -> 3).
    """
    associations = db.query(PatientCaregiverAssociation).filter(
        PatientCaregiverAssociation.patient_id == patient_id
    ).order_by(PatientCaregiverAssociation.escalation_tier.asc()).all()

    return associations


@router.get("/caregivers/{caregiver_id}/patients", response_model=List[PatientCaregiverAssociationOut])
def get_caregiver_patients(
    caregiver_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all patients assigned to a specific caregiver.
    """
    associations = db.query(PatientCaregiverAssociation).filter(
        PatientCaregiverAssociation.caregiver_id == caregiver_id
    ).all()

    return associations


@router.delete("/associations/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_association(
    association_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Dissolve a patient-caregiver association.
    """
    association = db.query(PatientCaregiverAssociation).filter(
        PatientCaregiverAssociation.id == association_id
    ).first()
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association with id {association_id} not found"
        )

    db.delete(association)
    db.commit()
