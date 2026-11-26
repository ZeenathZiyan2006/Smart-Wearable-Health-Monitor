"""Add multilingual messaging lifecycle fields to voice_message_logs

Revision ID: c7e84128f102
Revises: 9a12c448d1b7
Create Date: 2026-11-24 16:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7e84128f102'
down_revision: Union[str, None] = '9a12c448d1b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch_alter_table for robust SQLite & PostgreSQL compatibility
    with op.batch_alter_table('voice_message_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('delivery_status', sa.String(length=50), nullable=False, server_default='delivered'))
        batch_op.add_column(sa.Column('translation_status', sa.String(length=50), nullable=False, server_default='none'))
        batch_op.add_column(sa.Column('is_uncertain', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('reply_to_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('audio_payload', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('audio_format', sa.String(length=50), nullable=True))

        batch_op.create_foreign_key(
            'fk_voice_message_logs_reply_to_id',
            'voice_message_logs',
            ['reply_to_id'],
            ['id'],
            ondelete='SET NULL'
        )
        batch_op.create_index(batch_op.f('ix_voice_message_logs_is_read'), ['is_read'], unique=False)
        batch_op.create_index(batch_op.f('ix_voice_message_logs_reply_to_id'), ['reply_to_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('voice_message_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_voice_message_logs_reply_to_id'))
        batch_op.drop_index(batch_op.f('ix_voice_message_logs_is_read'))
        batch_op.drop_constraint('fk_voice_message_logs_reply_to_id', type_='foreignkey')
        batch_op.drop_column('audio_format')
        batch_op.drop_column('audio_payload')
        batch_op.drop_column('reply_to_id')
        batch_op.drop_column('is_uncertain')
        batch_op.drop_column('translation_status')
        batch_op.drop_column('delivery_status')
        batch_op.drop_column('read_at')
        batch_op.drop_column('is_read')
