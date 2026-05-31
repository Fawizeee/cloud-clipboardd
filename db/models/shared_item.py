from db.models.base import Base
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime


class SharedItem(Base):
    """
    Represents a clipboard item that has been shared from one user to another.
    Supports read/write permission levels.
    """
    __tablename__ = "shared_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clipboard_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clipboard.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shared_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shared_with_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission = Column(
        Enum("read", "write", name="shared_item_permission_enum"),
        default="read",
        nullable=False,
    )
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
