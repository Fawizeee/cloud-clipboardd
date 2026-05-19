from db.models.base import Base
from sqlalchemy import Column,String,Boolean,DateTime,ForeignKey,Enum
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
class ClipboardItem(Base):
    __tablename__ = "clipboard"
    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    content = Column(String,nullable=False)
    content_type = Column(Enum("text","image","file","url", name="clipboard_content_type_enum"),nullable=False,default="text")
    user_id = Column(UUID(as_uuid=True),ForeignKey("users.id"),nullable=False)
    owner_type = Column(Enum("user","team",name="clipboard_owner_type_enum"),nullable=False,default="user")
    owner_id = Column(UUID(as_uuid=True),nullable=False)
    created_at = Column(DateTime,default=datetime.utcnow)
    updated_at = Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
    is_deleted = Column(Boolean,default=False)
    expires_at = Column(DateTime,nullable=True)
    is_private = Column(Boolean,default=False)
    source_device_id = Column(UUID(as_uuid=True),nullable=True)
    
    
     
    @staticmethod
    async def get_by_user_id(db:Session,user_id:str):
        return db.query(ClipboardItem).filter(ClipboardItem.user_id == user_id).all() 

    @staticmethod
    def validate_content_type(content_type:str)->bool:
        return content_type in ["text","image","file","url"]