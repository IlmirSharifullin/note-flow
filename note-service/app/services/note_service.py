from typing import Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.kafka.producer import publish_event
from app.models.note import Note, NoteHistory
from app.repositories.note_repository import NoteRepository
from app.schemas.note import NoteCreate, NoteUpdate

_repo = NoteRepository()


class NoteService:
    async def create_note(self, user_id: str, data: NoteCreate) -> Note:
        note = await _repo.create(user_id, data.title, data.body, data.tags)
        await publish_event(
            "note.events",
            "note.created",
            {"note_id": str(note.id), "user_id": user_id, "title": note.title},
            key=str(note.id),
        )
        return note

    async def get_note(self, note_id: str, user_id: str) -> Note:
        note = await _repo.get_by_id(note_id, user_id)
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        return note

    async def list_notes(
        self, user_id: str, tag: Optional[str], page: int, size: int
    ) -> tuple[list[Note], int]:
        return await _repo.list_by_user(user_id, tag, page, size)

    async def update_note(self, note_id: str, user_id: str, data: NoteUpdate) -> Note:
        note = await self.get_note(note_id, user_id)
        await _repo.save_history(note)
        update_fields = data.model_dump(exclude_none=True)
        note = await _repo.update(note, **update_fields)
        await publish_event(
            "note.events",
            "note.updated",
            {"note_id": note_id, "user_id": user_id},
            key=note_id,
        )
        return note

    async def delete_note(self, note_id: str, user_id: str) -> None:
        note = await self.get_note(note_id, user_id)
        await _repo.soft_delete(note)
        await publish_event(
            "note.events",
            "note.deleted",
            {"note_id": note_id, "user_id": user_id},
            key=note_id,
        )

    async def restore_note(self, note_id: str, user_id: str) -> Note:
        # Look in trash (soft-deleted)
        note = await Note.find_one(
            Note.id == PydanticObjectId(note_id),
            Note.user_id == user_id,
            Note.deleted_at != None,
        )
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found in trash")
        return await _repo.restore(note)

    async def get_trash(self, user_id: str) -> list[Note]:
        return await _repo.get_trash(user_id)

    async def search(self, user_id: str, q: str) -> list[Note]:
        return await _repo.full_text_search(user_id, q)

    async def get_tags(self, user_id: str) -> list[dict]:
        return await _repo.get_tags(user_id)

    async def get_history(self, note_id: str, user_id: str) -> list[NoteHistory]:
        await self.get_note(note_id, user_id)  # verify ownership
        return await _repo.get_history(note_id)
