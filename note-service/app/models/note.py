from datetime import datetime
from typing import Annotated, Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class Attachment(BaseModel):
    file_id: str
    filename: str
    url: str


class Note(Document):
    user_id: Annotated[str, Indexed()]
    title: str
    body: str = ""
    tags: list[str] = []
    attachments: list[Attachment] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "notes"
        indexes = [
            [("user_id", 1), ("created_at", -1)],
            [("user_id", 1), ("tags", 1)],
            [("user_id", 1), ("deleted_at", 1)],
            [("title", "text"), ("body", "text")],
        ]


class NoteHistory(Document):
    note_id: str
    title: str
    body: str
    saved_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "note_history"
        indexes = [
            [("note_id", 1), ("saved_at", -1)],
            # TTL 30 days for history records
            [("saved_at", 1), {"expireAfterSeconds": 2592000}],
        ]
