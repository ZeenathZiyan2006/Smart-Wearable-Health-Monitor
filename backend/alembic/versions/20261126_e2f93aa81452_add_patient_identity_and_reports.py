"""Add patient identity, family email, medical reports, and recovery requests

Revision ID: e2f93aa81452
Revises: d1e84cc9a123
Create Date: 2026-11-26 19:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2f93aa81452'
down_revision: Union[str, None] = 'd1e84cc9a123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('patient_id', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('uuid', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_users_patient_id', ['patient_id'], unique=True)
        batch_op.create_index('ix_users_uuid', ['uuid'], unique=True)

    # 2. Update patient_profiles table
    with op.batch_alter_table('patient_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('patient_id', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('uuid', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('family_email', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('contact_number', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('address', sa.Text(), nullable=True))
        batch_op.create_index('ix_patient_profiles_patient_id', ['patient_id'], unique=True)
        batch_op.create_index('ix_patient_profiles_uuid', ['uuid'], unique=True)
        batch_op.create_index('ix_patient_profiles_family_email', ['family_email'], unique=False)

    # 3. Create medical_reports table
    op.create_table(
        'medical_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_name', sa.String(length=100), nullable=False),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('report_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patient_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('medical_reports', schema=None) as batch_op:
        batch_op.create_index('ix_medical_reports_patient_id', ['patient_id'], unique=False)

    # 4. Create patient_recovery_requests table
    op.create_table(
        'patient_recovery_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email_or_phone', sa.String(length=255), nullable=False),
        sa.Column('otp_code', sa.String(length=10), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('patient_recovery_requests', schema=None) as batch_op:
        batch_op.create_index('ix_patient_recovery_requests_email_or_phone', ['email_or_phone'], unique=False)


def downgrade() -> None:
    op.drop_table('patient_recovery_requests')
    op.drop_table('medical_reports')
    with op.batch_alter_table('patient_profiles', schema=None) as batch_op:
        batch_op.drop_column('address')
        batch_op.drop_column('contact_number')
        batch_op.drop_column('family_email')
        batch_op.drop_column('uuid')
        batch_op.drop_column('patient_id')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('uuid')
        batch_op.drop_column('patient_id')
