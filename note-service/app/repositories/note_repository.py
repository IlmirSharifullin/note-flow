from datetime import datetime, timedelta
from typing import Optional

from beanie import PydanticObjectId

from app.models.note import Note, NoteHistory

_HISTORY_LIMIT = 20
_TRASH_RETENTION_DAYS = 30


class NoteRepository:
    async def create(self, user_id: str, title: str, body: str, tags: list[str]) -> Note:
        note = Note(user_id=user_id, title=title, body=body, tags=tags)
        await note.insert()
        return note

    async def get_by_id(self, note_id: str, user_id: str) -> Optional[Note]:
        return await Note.find_one(
            Note.id == PydanticObjectId(note_id),
            Note.user_id == user_id,
            Note.deleted_at == None,
        )

    async def list_by_user(
        self,
        user_id: str,
        tag: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Note], int]:
        query = Note.find(Note.user_id == user_id, Note.deleted_at == None)
        if tag:
            query = query.find({"tags": tag})
        total = await query.count()
        items = (
            await query
            .skip((page - 1) * size)
            .limit(size)
            .sort(-Note.created_at)
            .to_list()
        )
        return items, total

    async def update(self, note: Note, **fields) -> Note:
        fields["updated_at"] = datetime.utcnow()
        await note.update({"$set": fields})
        await note.sync()
        return note

    async def soft_delete(self, note: Note) -> Note:
        note.deleted_at = datetime.utcnow()
        await note.save()
        return note

    async def restore(self, note: Note) -> Note:
        note.deleted_at = None
        await note.save()
        return note

    async def get_trash(self, user_id: str) -> list[Note]:
        cutoff = datetime.utcnow() - timedelta(days=_TRASH_RETENTION_DAYS)
        return await Note.find(
            Note.user_id == user_id,
            Note.deleted_at != None,
            {"deleted_at": {"$gte": cutoff}},
        ).to_list()

    async def full_text_search(self, user_id: str, query: str) -> list[Note]:
        return await Note.find(
            Note.user_id == user_id,
            Note.deleted_at == None,
            {"$text": {"$search": query}},
        ).to_list()

    async def get_tags(self, user_id: str) -> list[dict]:
        pipeline = [
            {"$match": {"user_id": user_id, "deleted_at": None}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$project": {"_id": 0, "tag": "$_id", "count": 1}},
        ]
        return await Note.aggregate(pipeline).to_list()

    async def save_history(self, note: Note) -> NoteHistory:
        history = NoteHistory(note_id=str(note.id), title=note.title, body=note.body)
        await history.insert()
        # Keep only last _HISTORY_LIMIT revisions
        all_revisions = (
            await NoteHistory.find(NoteHistory.note_id == str(note.id))
            .sort(-NoteHistory.saved_at)
            .to_list()
        )
        if len(all_revisions) > _HISTORY_LIMIT:
            for old in all_revisions[_HISTORY_LIMIT:]:
                await old.delete()
        return history

    async def get_history(self, note_id: str) -> list[NoteHistory]:
        return (
            await NoteHistory.find(NoteHistory.note_id == note_id)
            .sort(-NoteHistory.saved_at)
            .limit(_HISTORY_LIMIT)
            .to_list()
        )
