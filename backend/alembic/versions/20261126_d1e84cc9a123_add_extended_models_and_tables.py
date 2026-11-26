"""Add extended health measurements, devices, notifications, and system audit logs

Revision ID: d1e84cc9a123
Revises: c7e84128f102
Create Date: 2026-11-26 09:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e84cc9a123'
down_revision: Union[str, None] = 'c7e84128f102'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add extended vital signs and metrics to health_telemetry
    with op.batch_alter_table('health_telemetry', schema=None) as batch_op:
        batch_op.add_column(sa.Column('blood_pressure_sys', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('blood_pressure_dia', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('respiratory_rate', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('calories_burned', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('sleep_stage', sa.String(length=50), nullable=True))

    # 2. Create devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('device_uuid', sa.String(length=100), nullable=False),
        sa.Column('device_name', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('firmware_version', sa.String(length=50), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('battery_level', sa.Float(), nullable=True),
        sa.Column('is_simulator', sa.Boolean(), nullable=False),
        sa.Column('config_json', sa.Text(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paired_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patient_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_devices_device_uuid'), ['device_uuid'], unique=True)
        batch_op.create_index(batch_op.f('ix_devices_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_devices_patient_id'), ['patient_id'], unique=False)

    # 3. Create device_connection_history table
    op.create_table(
        'device_connection_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('device_connection_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_device_connection_history_device_id'), ['device_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_device_connection_history_id'), ['id'], unique=False)

    # 4. Create in_app_notifications table
    op.create_table(
        'in_app_notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=30), nullable=False),
        sa.Column('data_json', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('in_app_notifications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_in_app_notifications_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_in_app_notifications_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_in_app_notifications_is_read'), ['is_read'], unique=False)
        batch_op.create_index(batch_op.f('ix_in_app_notifications_user_id'), ['user_id'], unique=False)

    # 5. Create system_audit_logs table
    op.create_table(
        'system_audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=80), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('system_audit_logs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_system_audit_logs_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_system_audit_logs_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_system_audit_logs_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_system_audit_logs_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('system_audit_logs')
    op.drop_table('in_app_notifications')
    op.drop_table('device_connection_history')
    op.drop_table('devices')
    with op.batch_alter_table('health_telemetry', schema=None) as batch_op:
        batch_op.drop_column('sleep_stage')
        batch_op.drop_column('calories_burned')
        batch_op.drop_column('respiratory_rate')
        batch_op.drop_column('blood_pressure_dia')
        batch_op.drop_column('blood_pressure_sys')
