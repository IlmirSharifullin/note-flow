from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user_id
from app.models.note import Note
from app.schemas.note import NoteOut
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


@router.get("")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    user_id: str = Depends(get_current_user_id),
) -> list[NoteOut]:
    notes = await _svc.search(user_id, q)
    return [_to_out(n) for n in notes]
