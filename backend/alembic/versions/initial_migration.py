# backend/alembic/versions/initial_migration.py
"""
Initial database migration.
Creates all tables for InfoSense application.
"""

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('is_authenticated', sa.Boolean(), nullable=False),
        sa.Column('session_string', sa.Text(), nullable=True),
        sa.Column('last_auth_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message_count_today', sa.BigInteger(), nullable=False),
        sa.Column('last_message_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_number'),
        sa.UniqueConstraint('telegram_id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)

    # Create channels table
    op.create_table(
        'channels',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_monitoring', sa.Boolean(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_message_id', sa.BigInteger(), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('total_messages_processed', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_channels_id'), 'channels', ['id'], unique=False)
    op.create_index(op.f('ix_channels_username'), 'channels', ['username'], unique=False)

    # Create keywords table
    op.create_table(
        'keywords',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('word', sa.String(length=100), nullable=False),
        sa.Column('is_inclusion', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keywords_channel_id'), 'keywords', ['channel_id'], unique=False)
    op.create_index(op.f('ix_keywords_id'), 'keywords', ['id'], unique=False)
    op.create_index(op.f('ix_keywords_word'), 'keywords', ['word'], unique=False)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('telegram_message_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('sender_id', sa.BigInteger(), nullable=True),
        sa.Column('sender_username', sa.String(length=100), nullable=True),
        sa.Column('sender_first_name', sa.String(length=100), nullable=True),
        sa.Column('sender_last_name', sa.String(length=100), nullable=True),
        sa.Column('media_type', sa.String(length=50), nullable=True),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('message_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('edit_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('views', sa.BigInteger(), nullable=False),
        sa.Column('forwards', sa.BigInteger(), nullable=False),
        sa.Column('is_forwarded', sa.Boolean(), nullable=False),
        sa.Column('forwarded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('forward_destination', sa.String(length=100), nullable=True),
        sa.Column('matched_keywords', sa.JSON(), nullable=True),
        sa.Column('channel_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_channel_id'), 'messages', ['channel_id'], unique=False)
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_telegram_message_id'), 'messages', ['telegram_message_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order to respect foreign key constraints
    op.drop_index(op.f('ix_messages_telegram_message_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_channel_id'), table_name='messages')
    op.drop_table('messages')
    
    op.drop_index(op.f('ix_keywords_word'), table_name='keywords')
    op.drop_index(op.f('ix_keywords_id'), table_name='keywords')
    op.drop_index(op.f('ix_keywords_channel_id'), table_name='keywords')
    op.drop_table('keywords')
    
    op.drop_index(op.f('ix_channels_username'), table_name='channels')
    op.drop_index(op.f('ix_channels_id'), table_name='channels')
    op.drop_table('channels')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_index(op.f('ix_users_phone_number'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
