from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


# ── Request schemas ───────────────────────────────────────────────────────────

VALID_CONTENT_TYPES = {"text", "image", "file", "url", "code", "email"}


class SaveClipboardRequest(BaseModel):
    content: str
    content_type: str
    expires_at: Optional[datetime] = None
    is_private: bool = False
    source_device_id: Optional[str] = None
    source_device_name: Optional[str] = None
    folder_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        if v not in VALID_CONTENT_TYPES:
            raise ValueError(f"Invalid content type. Must be one of: {', '.join(VALID_CONTENT_TYPES)}")
        return v


class UpdateClipboardRequest(BaseModel):
    content: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None
    folder_id: Optional[str] = None


class ShareClipboardRequest(BaseModel):
    """Share a clipboard item with another user by email."""
    clipboard_item_id: str
    share_with_email: str
    permission: str = "read"

    @field_validator("permission")
    @classmethod
    def validate_permission(cls, v: str) -> str:
        if v not in {"read", "write"}:
            raise ValueError("Permission must be 'read' or 'write'")
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class ClipboardItemResponse(BaseModel):
    id: str
    content: str
    content_type: str
    content_preview: Optional[str] = None
    content_size: Optional[int] = None
    source_device_name: Optional[str] = None
    source_device_id: Optional[str] = None
    folder_id: Optional[str] = None
    is_favorite: bool = False
    is_pinned: bool = False
    is_private: bool = False
    access_count: int = 0
    shared_by: Optional[str] = None  # populated for team items
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class PaginatedClipboardResponse(BaseModel):
    items: List[ClipboardItemResponse]
    pagination: PaginationMeta


class SaveClipboardResponse(BaseModel):
    id: str
    content: str
    content_type: str
    content_size: Optional[int] = None
    sync_status: str = "pending"
    created_at: datetime
    updated_at: datetime


class FileUploadResponse(BaseModel):
    id: str
    file_url: str
    content_type: str
    filename: str
    file_size: int
    created_at: datetime


# ── Keep old names as aliases for backward compatibility ──────────────────────
saveClipboardRequest = SaveClipboardRequest
saveClipboardResponse = SaveClipboardResponse
getClipboardResponse = ClipboardItemResponse
