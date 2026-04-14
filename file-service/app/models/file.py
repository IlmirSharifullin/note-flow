import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    note_ref: Mapped[str | None] = mapped_column(String(24), nullable=True)
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    bucket: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    # active | deleted | archived
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
