import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileOut(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    note_ref: Optional[str] = None
    original_name: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    bucket: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FileMetaOut(FileOut):
    object_key: str


class PresignedUrlOut(BaseModel):
    url: str
    expires_in: int  # seconds, always 3600
