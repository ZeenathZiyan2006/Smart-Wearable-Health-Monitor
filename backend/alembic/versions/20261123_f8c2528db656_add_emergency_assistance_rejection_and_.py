"""Add emergency assistance, rejection and escalation audit fields

Revision ID: f8c2528db656
Revises: 6e6dd0d70332
Create Date: 2026-11-23 15:58:33.458223+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8c2528db656'
down_revision: Union[str, None] = '6e6dd0d70332'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('emergency_alerts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('device_uuid', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('location_accuracy', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('assistance_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('rejected_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('rejection_reason', sa.Text(), nullable=True))
        batch_op.create_index(batch_op.f('ix_emergency_alerts_device_uuid'), ['device_uuid'], unique=False)
        batch_op.create_foreign_key('fk_emergency_alerts_rejected_by_id', 'users', ['rejected_by_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('escalation_audit_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('provider', sa.String(length=50), nullable=False, server_default='development_mock'))
        batch_op.add_column(sa.Column('recipient_address', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    with op.batch_alter_table('escalation_audit_logs', schema=None) as batch_op:
        batch_op.drop_column('retry_count')
        batch_op.drop_column('error_message')
        batch_op.drop_column('recipient_address')
        batch_op.drop_column('provider')

    with op.batch_alter_table('emergency_alerts', schema=None) as batch_op:
        batch_op.drop_constraint('fk_emergency_alerts_rejected_by_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_emergency_alerts_device_uuid'))
        batch_op.drop_column('rejection_reason')
        batch_op.drop_column('rejected_at')
        batch_op.drop_column('rejected_by_id')
        batch_op.drop_column('assistance_message')
        batch_op.drop_column('location_accuracy')
        batch_op.drop_column('device_uuid')
