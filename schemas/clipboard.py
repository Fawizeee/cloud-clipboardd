from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class saveClipboardRequest(BaseModel):
    content: str
    user_id: str
    content_type: str
    expires_at: Optional[datetime] = None
    is_private: bool = False
    source_device_id: Optional[str] = None

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v):
        if v not in ["text","image","file","url"]:
            raise ValueError("Invalid content type")
        return v

class saveClipboardResponse(BaseModel):
    content: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
class getClipboardResponse(BaseModel):
    content: str
    user_id: str
    created_at: datetime
    updated_at: datetime

