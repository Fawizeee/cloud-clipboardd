"""
Device Routes
=============
POST   /api/v1/device          — register a device
GET    /api/v1/device          — list user's registered devices
DELETE /api/v1/device/{id}    — remove a device
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from db.models.user import User
from api.v1.auth.dependencies import get_current_user
from schemas.device import DeviceRegisterRequest, DeviceResponse
from services import device_service

router = APIRouter(prefix="/device", tags=["device"])


@router.post("", response_model=DeviceResponse, status_code=201)
async def register_device(
    req: DeviceRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Register a new device for the authenticated user.
    If a device with the same name + platform already exists it is updated
    (last_seen, device_token, app_version) and returned instead.
    """
    return await device_service.register_device(db, current_user, req)


@router.get("", response_model=List[DeviceResponse])
async def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active devices registered under the authenticated user's account."""
    return await device_service.list_devices(db, current_user)


@router.delete("/{device_id}")
async def remove_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete (de-register) a device belonging to the authenticated user."""
    return await device_service.remove_device(db, current_user, device_id)
