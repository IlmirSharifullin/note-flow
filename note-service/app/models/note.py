from datetime import datetime
from typing import Annotated, Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel


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
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("user_id", ASCENDING), ("tags", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("deleted_at", ASCENDING)]),
            IndexModel([("title", TEXT), ("body", TEXT)]),
        ]


class NoteHistory(Document):
    note_id: str
    title: str
    body: str
    saved_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "note_history"
        indexes = [
            IndexModel([("note_id", ASCENDING), ("saved_at", DESCENDING)]),
            IndexModel([("saved_at", ASCENDING)], expireAfterSeconds=2592000),
        ]
