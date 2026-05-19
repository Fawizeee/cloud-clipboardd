from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.clipboard import saveClipboardRequest, saveClipboardResponse, getClipboardResponse
from db.models.clipboard import ClipboardItem
from db.models.user import User
from api.v1.auth.dependencies import get_current_user

router = APIRouter(prefix="/clipboard", tags=["clipboard"])


@router.post("/personal", response_model=saveClipboardResponse)
async def save_clipboard(
    req: saveClipboardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Save a new clipboard item for the authenticated user.

    The user identity is taken from the JWT bearer token — not the request body.
    """
    new_item = ClipboardItem(
        content=req.content,
        content_type=req.content_type,
        user_id=current_user.id,
        owner_id=current_user.id,   # Default owner to the user themselves
        expires_at=req.expires_at,
        is_private=req.is_private,
        source_device_id=req.source_device_id,
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return saveClipboardResponse(
        content=new_item.content,
        created_at=new_item.created_at,
        updated_at=new_item.updated_at,
    )


@router.get("/personal", response_model=list[getClipboardResponse])
async def get_clipboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all clipboard items belonging to the authenticated user.

    The user identity is taken from the JWT bearer token — no query parameter required.
    """
    clipboard_items = await ClipboardItem.get_by_user_id(db, current_user.id)

    return [
        getClipboardResponse(
            content=item.content,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in clipboard_items
    ]
