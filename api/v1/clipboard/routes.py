from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.clipboard import saveClipboardRequest, saveClipboardResponse, getClipboardResponse
from db.models.clipboard import ClipboardItem
import uuid

router = APIRouter(prefix="/clipboard", tags=["clipboard"])

@router.post("/save", response_model=saveClipboardResponse)
async def save_clipboard(req: Request, db: Session = Depends(get_db)):
    clipboard_save_request = saveClipboardRequest.model_validate(await req.json())
    
    # Create the model instance
    new_item = ClipboardItem(
        content=clipboard_save_request.content,
        content_type=clipboard_save_request.content_type,
        user_id=clipboard_save_request.user_id,
        owner_id=clipboard_save_request.user_id, # Default owner to user
        expires_at=clipboard_save_request.expires_at,
        is_private=clipboard_save_request.is_private,
        source_device_id=clipboard_save_request.source_device_id
    )
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return saveClipboardResponse(
        content=new_item.content,
        user_id=str(new_item.user_id),
        created_at=new_item.created_at,
        updated_at=new_item.updated_at
    )

@router.get('/get', response_model=list[getClipboardResponse])
async def get_clipboard(user_id: str, db: Session = Depends(get_db)):
    # Assuming user_id is passed as a query parameter for testing
    # generate user id
    user_id = uuid.uuid4()
    print("user_id", user_id)
    clipboard_items = await ClipboardItem.get_by_user_id(db, user_id)
    
    response_items = []
    for item in clipboard_items:
        response_items.append(getClipboardResponse(
            content=item.content,
            user_id=str(item.user_id),
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
        
    return response_items
