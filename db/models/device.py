from db.models.base import Base
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
#7GyInUPmUqqCFmJ0
class Device(Base):
    __tablename__ = "devices"
    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True),ForeignKey("users.id"),nullable=False)
    device_name = Column(String,nullable=False)
    device_type = Column(String,nullable=False)
    platform = Column(Enum("ios", "android", "windows", "linux", "macos", name="device_platform_enum"), nullable=False)
    last_login = Column(DateTime,nullable=True)
    created_at = Column(DateTime,default=datetime.utcnow)
    updated_at = Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
    is_deleted = Column(Boolean,default=False)
    