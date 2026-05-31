from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DeviceRegisterRequest(BaseModel):
    device_name: str
    device_type: str        # mobile, desktop, web
    platform: str           # ios, android, windows, linux, macos, web
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    device_token: Optional[str] = None   # push notification token
    public_key: Optional[str] = None     # E2E encryption public key


class DeviceResponse(BaseModel):
    id: str
    device_name: str
    device_type: str
    platform: str
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    last_seen: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceStatusResponse(BaseModel):
    id: str
    name: str
    last_seen: Optional[datetime] = None
    status: str  # "online" | "offline"
