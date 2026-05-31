"""
Clipboard Service
=================
Business logic for clipboard CRUD, deduplication, team sharing, and search.
All DB mutations go through this service so routes stay thin.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from db.models.clipboard import ClipboardItem
from db.models.shared_item import SharedItem
from db.models.user import User
from schemas.clipboard import (
    SaveClipboardRequest,
    UpdateClipboardRequest,
    ClipboardItemResponse,
    PaginatedClipboardResponse,
    PaginationMeta,
    SaveClipboardResponse,
    ShareClipboardRequest,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _to_response(item: ClipboardItem, shared_by: Optional[str] = None) -> ClipboardItemResponse:
    return ClipboardItemResponse(
        id=str(item.id),
        content=item.content,
        content_type=item.content_type,
        content_preview=item.content_preview,
        content_size=item.content_size,
        source_device_name=item.source_device_name,
        source_device_id=str(item.source_device_id) if item.source_device_id else None,
        folder_id=str(item.folder_id) if item.folder_id else None,
        is_favorite=item.is_favorite,
        is_pinned=item.is_pinned,
        is_private=item.is_private,
        access_count=item.access_count,
        shared_by=shared_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
        expires_at=item.expires_at,
    )


# ── create ────────────────────────────────────────────────────────────────────

async def create_clipboard_item(
    db: Session,
    current_user: User,
    req: SaveClipboardRequest,
) -> SaveClipboardResponse:
    content_hash = ClipboardItem.compute_hash(req.content)
    content_preview = ClipboardItem.make_preview(req.content)
    content_size = len(req.content.encode("utf-8"))

    new_item = ClipboardItem(
        content=req.content,
        content_type=req.content_type,
        content_hash=content_hash,
        content_preview=content_preview,
        content_size=content_size,
        user_id=current_user.id,
        owner_type="user",
        owner_id=current_user.id,
        expires_at=req.expires_at,
        is_private=req.is_private,
        source_device_id=req.source_device_id,
        source_device_name=req.source_device_name,
        folder_id=req.folder_id,
        metadata_=req.metadata,
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return SaveClipboardResponse(
        id=str(new_item.id),
        content=new_item.content,
        content_type=new_item.content_type,
        content_size=new_item.content_size,
        sync_status="pending",
        created_at=new_item.created_at,
        updated_at=new_item.updated_at,
    )


# ── read ──────────────────────────────────────────────────────────────────────

async def get_personal_items(
    db: Session,
    current_user: User,
    page: int = 1,
    limit: int = 20,
    sort_order: str = "desc",
    content_type: Optional[str] = None,
    folder_id: Optional[str] = None,
) -> PaginatedClipboardResponse:
    items = await ClipboardItem.get_by_user_id(
        db,
        current_user.id,
        page=page,
        limit=limit,
        sort_order=sort_order,
        content_type=content_type,
        folder_id=folder_id,
    )
    total = await ClipboardItem.count_by_user_id(
        db,
        current_user.id,
        content_type=content_type,
        folder_id=folder_id,
    )
    return PaginatedClipboardResponse(
        items=[_to_response(i) for i in items],
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=math.ceil(total / limit) if limit else 1,
        ),
    )


async def get_single_item(db: Session, current_user: User, item_id: str) -> ClipboardItemResponse:
    item = (
        db.query(ClipboardItem)
        .filter(
            ClipboardItem.id == item_id,
            ClipboardItem.user_id == current_user.id,
            ClipboardItem.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clipboard item not found")

    # Bump access count
    item.access_count += 1
    item.last_accessed = datetime.utcnow()
    db.commit()
    db.refresh(item)

    return _to_response(item)


async def get_team_items(
    db: Session,
    current_user: User,
    page: int = 1,
    limit: int = 20,
) -> PaginatedClipboardResponse:
    """Return clipboard items shared with the current user by others."""
    offset = (page - 1) * limit
    shared_rows = (
        db.query(SharedItem, ClipboardItem, User)
        .join(ClipboardItem, SharedItem.clipboard_item_id == ClipboardItem.id)
        .join(User, SharedItem.shared_by_user_id == User.id)
        .filter(
            SharedItem.shared_with_user_id == current_user.id,
            ClipboardItem.is_deleted == False,  # noqa: E712
        )
        .order_by(SharedItem.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total = (
        db.query(SharedItem)
        .join(ClipboardItem, SharedItem.clipboard_item_id == ClipboardItem.id)
        .filter(
            SharedItem.shared_with_user_id == current_user.id,
            ClipboardItem.is_deleted == False,  # noqa: E712
        )
        .count()
    )

    responses = []
    for shared, clip_item, sharer in shared_rows:
        shared_by_name = f"{sharer.first_name} {sharer.last_name}".strip() or sharer.email
        responses.append(_to_response(clip_item, shared_by=shared_by_name))

    return PaginatedClipboardResponse(
        items=responses,
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=math.ceil(total / limit) if limit else 1,
        ),
    )


# ── update ────────────────────────────────────────────────────────────────────

async def update_clipboard_item(
    db: Session,
    current_user: User,
    item_id: str,
    req: UpdateClipboardRequest,
) -> ClipboardItemResponse:
    item = (
        db.query(ClipboardItem)
        .filter(
            ClipboardItem.id == item_id,
            ClipboardItem.user_id == current_user.id,
            ClipboardItem.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clipboard item not found")

    if req.content is not None:
        item.content = req.content
        item.content_hash = ClipboardItem.compute_hash(req.content)
        item.content_preview = ClipboardItem.make_preview(req.content)
        item.content_size = len(req.content.encode("utf-8"))
    if req.is_favorite is not None:
        item.is_favorite = req.is_favorite
    if req.is_pinned is not None:
        item.is_pinned = req.is_pinned
    if req.folder_id is not None:
        item.folder_id = req.folder_id

    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return _to_response(item)


# ── delete ────────────────────────────────────────────────────────────────────

async def delete_clipboard_item(db: Session, current_user: User, item_id: str) -> dict:
    item = (
        db.query(ClipboardItem)
        .filter(
            ClipboardItem.id == item_id,
            ClipboardItem.user_id == current_user.id,
            ClipboardItem.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clipboard item not found")

    item.is_deleted = True
    item.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Clipboard item deleted successfully"}


# ── share ─────────────────────────────────────────────────────────────────────

async def share_clipboard_item(
    db: Session,
    current_user: User,
    req: ShareClipboardRequest,
) -> dict:
    # Verify the item belongs to the sharing user
    item = (
        db.query(ClipboardItem)
        .filter(
            ClipboardItem.id == req.clipboard_item_id,
            ClipboardItem.user_id == current_user.id,
            ClipboardItem.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clipboard item not found")

    # Find the recipient
    recipient = db.query(User).filter(User.email == req.share_with_email).first()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient user not found")

    if str(recipient.id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot share with yourself")

    # Avoid duplicate shares
    existing = (
        db.query(SharedItem)
        .filter(
            SharedItem.clipboard_item_id == item.id,
            SharedItem.shared_with_user_id == recipient.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item already shared with this user")

    shared = SharedItem(
        clipboard_item_id=item.id,
        shared_by_user_id=current_user.id,
        shared_with_user_id=recipient.id,
        permission=req.permission,
    )
    db.add(shared)
    db.commit()
    return {"message": f"Item shared with {req.share_with_email} successfully"}


# ── search ────────────────────────────────────────────────────────────────────

async def search_clipboard_items(
    db: Session,
    current_user: User,
    query: str,
    page: int = 1,
    limit: int = 20,
) -> PaginatedClipboardResponse:
    offset = (page - 1) * limit
    base_query = db.query(ClipboardItem).filter(
        ClipboardItem.user_id == current_user.id,
        ClipboardItem.is_deleted == False,  # noqa: E712
        ClipboardItem.content.ilike(f"%{query}%"),
    )
    items = base_query.order_by(ClipboardItem.created_at.desc()).offset(offset).limit(limit).all()
    total = base_query.count()

    return PaginatedClipboardResponse(
        items=[_to_response(i) for i in items],
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=math.ceil(total / limit) if limit else 1,
        ),
    )
