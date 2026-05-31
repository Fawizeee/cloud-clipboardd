"""
Clipboard Routes
================
All clipboard endpoints — personal CRUD, team sharing, search, and file upload.

Every route is JWT-protected via get_current_user. User identity is never
taken from the request body — only from the bearer token.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from db.session import get_db
from db.models.user import User
from api.v1.auth.dependencies import get_current_user
from schemas.clipboard import (
    SaveClipboardRequest,
    UpdateClipboardRequest,
    ShareClipboardRequest,
    SaveClipboardResponse,
    ClipboardItemResponse,
    PaginatedClipboardResponse,
    FileUploadResponse,
)
from services import clipboard_service
from datetime import datetime
import uuid

router = APIRouter(prefix="/clipboard", tags=["clipboard"])


# ── Personal clipboard ────────────────────────────────────────────────────────

@router.post("/personal", response_model=SaveClipboardResponse, status_code=status.HTTP_201_CREATED)
async def save_clipboard(
    req: SaveClipboardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a new clipboard item for the authenticated user."""
    return await clipboard_service.create_clipboard_item(db, current_user, req)


@router.get("/personal", response_model=PaginatedClipboardResponse)
async def get_clipboard(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    sort_order: str = Query("desc", description="Sort by creation date: 'asc' or 'desc'"),
    content_type: str | None = Query(None, description="Filter by content type"),
    folder_id: str | None = Query(None, description="Filter by folder UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the authenticated user's personal clipboard items with pagination."""
    return await clipboard_service.get_personal_items(
        db, current_user, page=page, limit=limit,
        sort_order=sort_order, content_type=content_type, folder_id=folder_id,
    )


@router.get("/personal/search", response_model=PaginatedClipboardResponse)
async def search_clipboard(
    q: str = Query(..., min_length=1, description="Search query string"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full-text search across the authenticated user's clipboard items."""
    return await clipboard_service.search_clipboard_items(db, current_user, q, page=page, limit=limit)


@router.get("/personal/{item_id}", response_model=ClipboardItemResponse)
async def get_clipboard_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single clipboard item by ID (increments access count)."""
    return await clipboard_service.get_single_item(db, current_user, item_id)


@router.patch("/personal/{item_id}", response_model=ClipboardItemResponse)
async def update_clipboard_item(
    item_id: str,
    req: UpdateClipboardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update a clipboard item (content, favorite, pinned, folder)."""
    return await clipboard_service.update_clipboard_item(db, current_user, item_id, req)


@router.delete("/personal/{item_id}")
async def delete_clipboard_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a clipboard item owned by the authenticated user."""
    return await clipboard_service.delete_clipboard_item(db, current_user, item_id)


# ── Team (shared) clipboard ───────────────────────────────────────────────────

@router.get("/team", response_model=PaginatedClipboardResponse)
async def get_team_clipboard(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve clipboard items that other users have shared with the authenticated user."""
    return await clipboard_service.get_team_items(db, current_user, page=page, limit=limit)


@router.post("/team/share")
async def share_clipboard_item(
    req: ShareClipboardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Share one of your clipboard items with another user by their email address."""
    return await clipboard_service.share_clipboard_item(db, current_user, req)


# ── File upload (stub — no storage backend configured) ───────────────────────

@router.post("/files", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file clipboard item.

    NOTE: File storage (S3/MinIO) is not configured in this environment.
    This endpoint accepts the multipart upload, reads the file size, and returns
    a stub URL. Wire in your storage provider here when ready.
    """
    content = await file.read()
    file_size = len(content)

    stub_id = str(uuid.uuid4())
    return FileUploadResponse(
        id=stub_id,
        file_url=f"https://storage.example.com/files/{stub_id}/{file.filename}",
        content_type=file.content_type or "application/octet-stream",
        filename=file.filename or "upload",
        file_size=file_size,
        created_at=datetime.utcnow(),
    )
