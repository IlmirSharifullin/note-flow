from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AttachmentOut(BaseModel):
    file_id: str
    filename: str
    url: str


class NoteCreate(BaseModel):
    title: str
    body: str = ""
    tags: list[str] = []


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[list[str]] = None


class NoteOut(BaseModel):
    id: str
    user_id: str
    title: str
    body: str
    tags: list[str]
    attachments: list[AttachmentOut]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class NoteListOut(BaseModel):
    items: list[NoteOut]
    total: int
    page: int
    size: int


class NoteHistoryOut(BaseModel):
    id: str
    note_id: str
    title: str
    body: str
    saved_at: datetime
