"""Add voice assistance consent, message logs and audit tables

Revision ID: 9a12c448d1b7
Revises: f8c2528db656
Create Date: 2026-11-24 08:50:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a12c448d1b7'
down_revision: Union[str, None] = 'f8c2528db656'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Voice Consents table
    op.create_table(
        'voice_consents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('consent_granted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('audio_retention_permitted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('privacy_policy_accepted', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_voice_consents_id'), 'voice_consents', ['id'], unique=False)

    # 2. Voice Message Logs table
    op.create_table(
        'voice_message_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('source_language', sa.String(length=20), nullable=False),
        sa.Column('target_language', sa.String(length=20), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=True),
        sa.Column('consent_confirmed', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('stt_provider', sa.String(length=50), nullable=False, server_default='mock_development'),
        sa.Column('translation_provider', sa.String(length=50), nullable=False, server_default='mock_development'),
        sa.Column('tts_provider', sa.String(length=50), nullable=False, server_default='mock_development'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voice_message_logs_id'), 'voice_message_logs', ['id'], unique=False)
    op.create_index(op.f('ix_voice_message_logs_recipient_id'), 'voice_message_logs', ['recipient_id'], unique=False)
    op.create_index(op.f('ix_voice_message_logs_sender_id'), 'voice_message_logs', ['sender_id'], unique=False)

    # 3. Voice Audit Logs table
    op.create_table(
        'voice_audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('detected_language', sa.String(length=20), nullable=True),
        sa.Column('input_character_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_character_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_mock', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='mock_development'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voice_audit_logs_id'), 'voice_audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_voice_audit_logs_user_id'), 'voice_audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_voice_audit_logs_user_id'), table_name='voice_audit_logs')
    op.drop_index(op.f('ix_voice_audit_logs_id'), table_name='voice_audit_logs')
    op.drop_table('voice_audit_logs')

    op.drop_index(op.f('ix_voice_message_logs_sender_id'), table_name='voice_message_logs')
    op.drop_index(op.f('ix_voice_message_logs_recipient_id'), table_name='voice_message_logs')
    op.drop_index(op.f('ix_voice_message_logs_id'), table_name='voice_message_logs')
    op.drop_table('voice_message_logs')

    op.drop_index(op.f('ix_voice_consents_id'), table_name='voice_consents')
    op.drop_table('voice_consents')
