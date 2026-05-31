"""
Sync Service
============
Provides sync-status queries and delta computation for device synchronisation.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session

from db.models.clipboard import ClipboardItem
from db.models.device import Device
from db.models.sync_event import SyncEvent
from db.models.user import User
from schemas.sync import (
    SyncStatusResponse,
    SyncTriggerRequest,
    SyncTriggerResponse,
    SyncItem,
)
from schemas.device import DeviceStatusResponse


# A device is considered "online" if seen within the last 5 minutes
ONLINE_THRESHOLD_MINUTES = 5


async def get_sync_status(db: Session, current_user: User) -> SyncStatusResponse:
    # Pending sync events (not yet delivered to all targets)
    pending_count = (
        db.query(SyncEvent)
        .filter(
            SyncEvent.user_id == current_user.id,
            SyncEvent.status == "pending",
        )
        .count()
    )

    # Conflict detection is left as future work — report 0 for now
    conflict_count = 0

    # Last processed sync event timestamp
    last_event = (
        db.query(SyncEvent)
        .filter(
            SyncEvent.user_id == current_user.id,
            SyncEvent.status == "completed",
        )
        .order_by(SyncEvent.processed_at.desc())
        .first()
    )
    last_sync = last_event.processed_at if last_event else None

    # Device list with online/offline status
    devices = (
        db.query(Device)
        .filter(
            Device.user_id == current_user.id,
            Device.is_deleted == False,  # noqa: E712
        )
        .order_by(Device.last_seen.desc())
        .all()
    )

    threshold = datetime.utcnow() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    device_statuses = [
        DeviceStatusResponse(
            id=str(d.id),
            name=d.device_name,
            last_seen=d.last_seen,
            status="online" if (d.last_seen and d.last_seen >= threshold) else "offline",
        )
        for d in devices
    ]

    return SyncStatusResponse(
        last_sync=last_sync,
        pending_items=pending_count,
        conflict_items=conflict_count,
        devices=device_statuses,
    )


async def trigger_sync(
    db: Session,
    current_user: User,
    req: SyncTriggerRequest,
) -> SyncTriggerResponse:
    """
    Return all clipboard items created or modified after the last_sync_timestamp
    for this user, so the requesting device can catch up.
    """
    items = (
        db.query(ClipboardItem)
        .filter(
            ClipboardItem.user_id == current_user.id,
            ClipboardItem.updated_at > req.last_sync_timestamp,
        )
        .order_by(ClipboardItem.updated_at.asc())
        .limit(200)  # hard cap per sync batch
        .all()
    )

    sync_items: list[SyncItem] = []
    for item in items:
        action = "delete" if item.is_deleted else "create"
        sync_items.append(
            SyncItem(
                id=str(item.id),
                action=action,
                content_type=item.content_type,
                content=None if item.is_deleted else item.content,
                created_at=item.created_at,
            )
        )

    # Mark a new sync event as completed
    sync_event = SyncEvent(
        user_id=current_user.id,
        source_device_id=req.device_id if _is_valid_uuid(req.device_id) else None,
        event_type="sync",
        status="completed",
        processed_at=datetime.utcnow(),
    )
    db.add(sync_event)
    db.commit()

    return SyncTriggerResponse(
        sync_id=str(uuid.uuid4()),
        items_to_sync=sync_items,
        sync_timestamp=datetime.utcnow(),
    )


def _is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
