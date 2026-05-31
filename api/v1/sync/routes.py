"""
Sync Routes
===========
GET  /api/v1/sync/status   — sync status with device list and pending count
POST /api/v1/sync/trigger  — return clipboard delta since last sync timestamp
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from db.models.user import User
from api.v1.auth.dependencies import get_current_user
from schemas.sync import SyncStatusResponse, SyncTriggerRequest, SyncTriggerResponse
from services import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return current sync status for the authenticated user:
    - Last successful sync timestamp
    - Count of pending sync events
    - List of registered devices with online/offline status
    """
    return await sync_service.get_sync_status(db, current_user)


@router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(
    req: SyncTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute and return all clipboard items that changed after last_sync_timestamp.
    The calling device uses this delta to bring itself up to date.
    """
    return await sync_service.trigger_sync(db, current_user, req)
