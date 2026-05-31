from db.models.base import Base
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime


class Folder(Base):
    """
    A named collection/folder that groups clipboard items for a user.
    Folders can be nested via the parent_id self-reference.
    """
    __tablename__ = "folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)   # hex color, e.g. "#6C63FF"
    icon = Column(String(50), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
