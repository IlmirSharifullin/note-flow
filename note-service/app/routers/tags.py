from fastapi import APIRouter, Depends

from app.dependencies import get_current_user_id
from app.services.note_service import NoteService

router = APIRouter()
_svc = NoteService()


@router.get("")
async def get_tags(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    return await _svc.get_tags(user_id)
