import os
import sys

# Prepend backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

TEST_DB_PATH = os.path.abspath(os.path.join(backend_dir, "test_pulseguardian.db"))
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["ENVIRONMENT"] = "testing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.user import CaregiverProfile, PatientProfile, User, UserRole
from app.workers.celery_app import celery_app

celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in test database file at start of test session, drop at end."""
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except OSError:
            pass


@pytest.fixture(autouse=True)
def clean_database_tables():
    """Clean all records from tables before each test to guarantee complete test isolation."""
    session = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()


@pytest.fixture
def db_session():
    """Yield a database session attached to the test database."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Test client with get_db overridden to use TestingSessionLocal."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_patient_user(db_session):
    user = User(
        email="patient@pulseguardian.ai",
        hashed_password=get_password_hash("patient123"),
        full_name="Ramesh Kumar",
        role=UserRole.PATIENT.value,
        phone_number="+919876543210",
        preferred_language="kn",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    patient_profile = PatientProfile(
        user_id=user.id,
        blood_group="O+",
        medical_history="Hypertension",
        emergency_contact_phone="+919876543211",
        device_uuid="PG-ESP32-001",
        device_status="online"
    )
    db_session.add(patient_profile)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_caregiver_user(db_session):
    user = User(
        email="caregiver@pulseguardian.ai",
        hashed_password=get_password_hash("caregiver123"),
        full_name="Dr. Sunita Rao",
        role=UserRole.CAREGIVER.value,
        phone_number="+919876543220",
        preferred_language="en",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    caregiver_profile = CaregiverProfile(
        user_id=user.id,
        relationship_type="Doctor",
        organization="PulseHealth Clinic",
        notification_preference="all"
    )
    db_session.add(caregiver_profile)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def patient_token(test_patient_user):
    return create_access_token(
        subject=test_patient_user.id,
        role=test_patient_user.role,
        extra_claims={"email": test_patient_user.email}
    )


@pytest.fixture
def caregiver_token(test_caregiver_user):
    return create_access_token(
        subject=test_caregiver_user.id,
        role=test_caregiver_user.role,
        extra_claims={"email": test_caregiver_user.email}
    )
