"""
Device Service
==============
Business logic for registering, listing, and removing user devices.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from db.models.device import Device
from db.models.user import User
from schemas.device import DeviceRegisterRequest, DeviceResponse

VALID_PLATFORMS = {"ios", "android", "windows", "linux", "macos", "web"}


async def register_device(
    db: Session,
    current_user: User,
    req: DeviceRegisterRequest,
) -> DeviceResponse:
    if req.platform not in VALID_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid platform. Must be one of: {', '.join(sorted(VALID_PLATFORMS))}",
        )

    # Upsert by device_name + platform for the same user to avoid duplicates
    existing = (
        db.query(Device)
        .filter(
            Device.user_id == current_user.id,
            Device.device_name == req.device_name,
            Device.platform == req.platform,
            Device.is_deleted == False,  # noqa: E712
        )
        .first()
    )

    if existing:
        # Update last-seen and token
        existing.last_seen = datetime.utcnow()
        if req.device_token:
            existing.device_token = req.device_token
        if req.app_version:
            existing.app_version = req.app_version
        db.commit()
        db.refresh(existing)
        return DeviceResponse(
            id=str(existing.id),
            device_name=existing.device_name,
            device_type=existing.device_type,
            platform=existing.platform,
            os_version=existing.os_version,
            app_version=existing.app_version,
            last_seen=existing.last_seen,
            is_active=existing.is_active,
            created_at=existing.created_at,
        )

    device = Device(
        user_id=current_user.id,
        device_name=req.device_name,
        device_type=req.device_type,
        platform=req.platform,
        os_version=req.os_version,
        app_version=req.app_version,
        device_token=req.device_token,
        public_key=req.public_key,
        last_seen=datetime.utcnow(),
        is_active=True,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    return DeviceResponse(
        id=str(device.id),
        device_name=device.device_name,
        device_type=device.device_type,
        platform=device.platform,
        os_version=device.os_version,
        app_version=device.app_version,
        last_seen=device.last_seen,
        is_active=device.is_active,
        created_at=device.created_at,
    )


async def list_devices(db: Session, current_user: User) -> List[DeviceResponse]:
    devices = (
        db.query(Device)
        .filter(
            Device.user_id == current_user.id,
            Device.is_deleted == False,  # noqa: E712
        )
        .order_by(Device.last_seen.desc())
        .all()
    )
    return [
        DeviceResponse(
            id=str(d.id),
            device_name=d.device_name,
            device_type=d.device_type,
            platform=d.platform,
            os_version=d.os_version,
            app_version=d.app_version,
            last_seen=d.last_seen,
            is_active=d.is_active,
            created_at=d.created_at,
        )
        for d in devices
    ]


async def remove_device(db: Session, current_user: User, device_id: str) -> dict:
    device = (
        db.query(Device)
        .filter(
            Device.id == device_id,
            Device.user_id == current_user.id,
            Device.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device.is_deleted = True
    device.is_active = False
    db.commit()
    return {"message": "Device removed successfully"}
