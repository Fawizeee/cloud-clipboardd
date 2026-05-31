from db.models.base import Base
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Integer, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import hashlib


class ClipboardItem(Base):
    __tablename__ = "clipboard"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    content_type = Column(
        Enum("text", "image", "file", "url", "code", "email", name="clipboard_content_type_enum"),
        nullable=False,
        default="text",
    )
    content_preview = Column(String(200), nullable=True)  # first 200 chars or thumbnail
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for deduplication
    content_size = Column(BigInteger, nullable=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    owner_type = Column(
        Enum("user", "team", name="clipboard_owner_type_enum"),
        nullable=False,
        default="user",
    )
    owner_id = Column(UUID(as_uuid=True), nullable=False)

    # Optional device reference (soft reference — no FK constraint)
    source_device_id = Column(UUID(as_uuid=True), nullable=True)
    source_device_name = Column(String(255), nullable=True)

    # Folder organisation
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)

    # Extra metadata (source app, format, etc.)
    metadata_ = Column("metadata", JSONB, nullable=True)

    # Flags
    is_favorite = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, index=True)

    # Engagement
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def compute_hash(content: str) -> str:
        """Return the SHA-256 hex digest of the given content string."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def make_preview(content: str) -> str:
        """Return first 200 characters of content as a preview."""
        return content[:200]

    # ------------------------------------------------------------------ queries

    @staticmethod
    async def get_by_user_id(
        db: Session,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        sort_order: str = "desc",
        content_type: str | None = None,
        folder_id: str | None = None,
    ):
        offset = (page - 1) * limit
        query = db.query(ClipboardItem).filter(
            ClipboardItem.user_id == user_id,
            ClipboardItem.is_deleted == False,  # noqa: E712
        )
        if content_type:
            query = query.filter(ClipboardItem.content_type == content_type)
        if folder_id:
            query = query.filter(ClipboardItem.folder_id == folder_id)
        if sort_order.lower() == "asc":
            query = query.order_by(ClipboardItem.created_at.asc())
        else:
            query = query.order_by(ClipboardItem.created_at.desc())
        return query.offset(offset).limit(limit).all()

    @staticmethod
    async def count_by_user_id(
        db: Session,
        user_id: str,
        content_type: str | None = None,
        folder_id: str | None = None,
    ) -> int:
        query = db.query(ClipboardItem).filter(
            ClipboardItem.user_id == user_id,
            ClipboardItem.is_deleted == False,  # noqa: E712
        )
        if content_type:
            query = query.filter(ClipboardItem.content_type == content_type)
        if folder_id:
            query = query.filter(ClipboardItem.folder_id == folder_id)
        return query.count()

    @staticmethod
    def validate_content_type(content_type: str) -> bool:
        return content_type in ["text", "image", "file", "url", "code", "email"]