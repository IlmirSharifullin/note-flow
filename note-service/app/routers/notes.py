from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user_id
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteHistoryOut, NoteListOut, NoteOut, NoteUpdate
from app.services.note_service import NoteService

router = APIRouter()
_svc = NoteService()


def _to_out(note: Note) -> NoteOut:
    return NoteOut(
        id=str(note.id),
        user_id=note.user_id,
        title=note.title,
        body=note.body,
        tags=note.tags,
        attachments=[a.model_dump() for a in note.attachments],
        created_at=note.created_at,
        updated_at=note.updated_at,
        deleted_at=note.deleted_at,
    )


@router.get("", response_model=NoteListOut)
async def list_notes(
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
):
    items, total = await _svc.list_notes(user_id, tag, page, size)
    return NoteListOut(items=[_to_out(n) for n in items], total=total, page=page, size=size)


@router.post("", response_model=NoteOut, status_code=201)
async def create_note(data: NoteCreate, user_id: str = Depends(get_current_user_id)):
    note = await _svc.create_note(user_id, data)
    return _to_out(note)


@router.get("/trash", response_model=list[NoteOut])
async def get_trash(user_id: str = Depends(get_current_user_id)):
    items = await _svc.get_trash(user_id)
    return [_to_out(n) for n in items]


@router.get("/{note_id}", response_model=NoteOut)
async def get_note(note_id: str, user_id: str = Depends(get_current_user_id)):
    note = await _svc.get_note(note_id, user_id)
    return _to_out(note)


@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(note_id: str, data: NoteUpdate, user_id: str = Depends(get_current_user_id)):
    note = await _svc.update_note(note_id, user_id, data)
    return _to_out(note)


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str, user_id: str = Depends(get_current_user_id)):
    await _svc.delete_note(note_id, user_id)


@router.post("/{note_id}/restore", response_model=NoteOut)
async def restore_note(note_id: str, user_id: str = Depends(get_current_user_id)):
    note = await _svc.restore_note(note_id, user_id)
    return _to_out(note)


@router.get("/{note_id}/history", response_model=list[NoteHistoryOut])
async def get_history(note_id: str, user_id: str = Depends(get_current_user_id)):
    history = await _svc.get_history(note_id, user_id)
    return [
        NoteHistoryOut(id=str(h.id), note_id=h.note_id, title=h.title, body=h.body, saved_at=h.saved_at)
        for h in history
    ]
