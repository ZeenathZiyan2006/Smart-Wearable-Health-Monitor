"""Add sleep, accelerometer, units and gps status

Revision ID: 6e6dd0d70332
Revises: e0cb4f8a22d6
Create Date: 2026-11-23 15:45:33.369492+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e6dd0d70332'
down_revision: Union[str, None] = 'e0cb4f8a22d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('health_telemetry') as batch_op:
        batch_op.add_column(sa.Column('device_uuid', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('temperature_unit', sa.String(length=10), nullable=False, server_default='C'))
        batch_op.add_column(sa.Column('sleep_duration_minutes', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('accelerometer_x', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('accelerometer_y', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('accelerometer_z', sa.Float(), nullable=True))
        batch_op.create_index(batch_op.f('ix_health_telemetry_device_uuid'), ['device_uuid'], unique=False)
        batch_op.create_unique_constraint('uq_health_telemetry_patient_timestamp', ['patient_id', 'recorded_at'])

    with op.batch_alter_table('location_logs') as batch_op:
        batch_op.add_column(sa.Column('device_uuid', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('is_gps_available', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column('device_battery', sa.Float(), nullable=True))
        batch_op.alter_column('latitude', existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column('longitude', existing_type=sa.FLOAT(), nullable=True)
        batch_op.create_index(batch_op.f('ix_location_logs_device_uuid'), ['device_uuid'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('location_logs') as batch_op:
        batch_op.drop_index(batch_op.f('ix_location_logs_device_uuid'))
        batch_op.alter_column('longitude', existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column('latitude', existing_type=sa.FLOAT(), nullable=False)
        batch_op.drop_column('device_battery')
        batch_op.drop_column('is_gps_available')
        batch_op.drop_column('device_uuid')

    with op.batch_alter_table('health_telemetry') as batch_op:
        batch_op.drop_constraint('uq_health_telemetry_patient_timestamp', type_='unique')
        batch_op.drop_index(batch_op.f('ix_health_telemetry_device_uuid'))
        batch_op.drop_column('accelerometer_z')
        batch_op.drop_column('accelerometer_y')
        batch_op.drop_column('accelerometer_x')
        batch_op.drop_column('sleep_duration_minutes')
        batch_op.drop_column('temperature_unit')
        batch_op.drop_column('device_uuid')
