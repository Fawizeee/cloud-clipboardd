from db.models.base import Base
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
from datetime import datetime


class SyncEvent(Base):
    """
    Tracks synchronisation events between devices for a user.
    Each row records one clipboard operation that must be propagated.
    """
    __tablename__ = "sync_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    clipboard_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clipboard.id", ondelete="CASCADE"),
        nullable=True,
    )
    source_device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)

    # Target device IDs as a PostgreSQL UUID array
    target_device_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)

    event_type = Column(
        Enum("create", "update", "delete", "sync", name="sync_event_type_enum"),
        nullable=False,
    )
    status = Column(
        Enum("pending", "completed", "failed", name="sync_event_status_enum"),
        default="pending",
        nullable=False,
        index=True,
    )
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
