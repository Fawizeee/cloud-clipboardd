from db.models.base import Base
from sqlalchemy import Column,String,Boolean,DateTime,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    email = Column(String,unique=True,nullable=False)
    password = Column(String,nullable=True)
    first_name = Column(String,nullable=False)
    last_name = Column(String,nullable=False)
    created_at = Column(DateTime,default=datetime.utcnow)
    updated_at = Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
    is_active = Column(Boolean,default=False)
    is_verified = Column(Boolean,default=False)
    verification_token = Column(String,nullable=True)
    refresh_token = Column(String,nullable=True)
    token = Column(String,nullable=True)
    is_deleted = Column(Boolean,default=False)
    
    last_login = Column(DateTime, nullable=True)
    login_attempts = Column(String(10), default="0", nullable=False)
    locked_until = Column(DateTime, nullable=True)
    needs_onboarding = Column(Boolean, default=True, nullable=False)
    last_active_at = Column(DateTime, nullable=True)
    last_password_change_at = Column(DateTime, nullable=True)

    