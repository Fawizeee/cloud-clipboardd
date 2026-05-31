from db.models.base import Base
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    device_name = Column(String(255), nullable=False)
    device_type = Column(String(50), nullable=False)  # mobile, desktop, web
    platform = Column(
        Enum("ios", "android", "windows", "linux", "macos", "web", name="device_platform_enum"),
        nullable=False,
    )
    os_version = Column(String(100), nullable=True)
    app_version = Column(String(50), nullable=True)
    device_token = Column(String(500), nullable=True)  # for push notifications
    public_key = Column(String, nullable=True)          # for end-to-end encryption

    last_login = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)

    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)