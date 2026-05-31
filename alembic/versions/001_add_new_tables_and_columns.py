"""Add new columns to clipboard/devices and create folders, shared_items, sync_events tables

Revision ID: 001_add_new_tables_and_columns
Revises: 
Create Date: 2026-05-31

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_new_tables_and_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Create new ENUMs (safe: create if not exists) ────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clipboard_content_type_enum AS ENUM ('text','image','file','url','code','email');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clipboard_owner_type_enum AS ENUM ('user','team');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE device_platform_enum AS ENUM ('ios','android','windows','linux','macos','web');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE shared_item_permission_enum AS ENUM ('read','write');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sync_event_type_enum AS ENUM ('create','update','delete','sync');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sync_event_status_enum AS ENUM ('pending','completed','failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── folders table ────────────────────────────────────────────────────────
    op.create_table(
        'folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id'), nullable=True),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_folders_user_id', 'folders', ['user_id'])

    # ── New columns on clipboard table ───────────────────────────────────────
    # Add only if they don't already exist
    with op.batch_alter_table('clipboard') as batch_op:
        batch_op.add_column(sa.Column('content_preview', sa.String(200), nullable=True))
        batch_op.add_column(sa.Column('content_hash', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('content_size', sa.BigInteger, nullable=True))
        batch_op.add_column(sa.Column('source_device_name', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('folder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id'), nullable=True))
        batch_op.add_column(sa.Column('metadata', postgresql.JSONB, nullable=True))
        batch_op.add_column(sa.Column('is_favorite', sa.Boolean, server_default='false'))
        batch_op.add_column(sa.Column('is_pinned', sa.Boolean, server_default='false'))
        batch_op.add_column(sa.Column('access_count', sa.Integer, server_default='0'))
        batch_op.add_column(sa.Column('last_accessed', sa.DateTime, nullable=True))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime, nullable=True))

    op.create_index('idx_clipboard_content_hash', 'clipboard', ['content_hash'])

    # ── New columns on devices table ─────────────────────────────────────────
    with op.batch_alter_table('devices') as batch_op:
        batch_op.add_column(sa.Column('os_version', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('app_version', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('device_token', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('public_key', sa.Text, nullable=True))
        batch_op.add_column(sa.Column('last_seen', sa.DateTime, nullable=True))
        batch_op.add_column(sa.Column('is_active', sa.Boolean, server_default='true'))

    # ── shared_items table ───────────────────────────────────────────────────
    op.create_table(
        'shared_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clipboard_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clipboard.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shared_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shared_with_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission', sa.Enum('read', 'write', name='shared_item_permission_enum'), nullable=False, server_default='read'),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_shared_items_clipboard_id', 'shared_items', ['clipboard_item_id'])
    op.create_index('idx_shared_items_shared_by', 'shared_items', ['shared_by_user_id'])
    op.create_index('idx_shared_items_shared_with', 'shared_items', ['shared_with_user_id'])

    # ── sync_events table ────────────────────────────────────────────────────
    op.create_table(
        'sync_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('clipboard_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clipboard.id', ondelete='CASCADE'), nullable=True),
        sa.Column('source_device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('target_device_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('event_type', sa.Enum('create', 'update', 'delete', 'sync', name='sync_event_type_enum'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', name='sync_event_status_enum'), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_sync_events_user_id', 'sync_events', ['user_id'])
    op.create_index('idx_sync_events_status', 'sync_events', ['status'])
    op.create_index('idx_sync_events_created_at', 'sync_events', ['created_at'])


def downgrade() -> None:
    op.drop_table('sync_events')
    op.drop_table('shared_items')

    with op.batch_alter_table('devices') as batch_op:
        for col in ['os_version', 'app_version', 'device_token', 'public_key', 'last_seen', 'is_active']:
            batch_op.drop_column(col)

    with op.batch_alter_table('clipboard') as batch_op:
        for col in ['content_preview', 'content_hash', 'content_size', 'source_device_name',
                    'folder_id', 'metadata', 'is_favorite', 'is_pinned',
                    'access_count', 'last_accessed', 'deleted_at']:
            batch_op.drop_column(col)

    op.drop_table('folders')

    for enum_name in [
        'sync_event_status_enum', 'sync_event_type_enum',
        'shared_item_permission_enum', 'device_platform_enum',
        'clipboard_owner_type_enum', 'clipboard_content_type_enum',
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
