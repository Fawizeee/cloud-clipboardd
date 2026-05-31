from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from schemas.device import DeviceStatusResponse
from schemas.clipboard import ClipboardItemResponse


class SyncTriggerRequest(BaseModel):
    device_id: str
    last_sync_timestamp: datetime


class SyncItem(BaseModel):
    id: str
    action: str          # "create" | "update" | "delete"
    content_type: str
    content: Optional[str] = None
    created_at: datetime


class SyncTriggerResponse(BaseModel):
    sync_id: str
    items_to_sync: List[SyncItem]
    sync_timestamp: datetime


class SyncStatusResponse(BaseModel):
    last_sync: Optional[datetime] = None
    pending_items: int
    conflict_items: int
    devices: List[DeviceStatusResponse]
