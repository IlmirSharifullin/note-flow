import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.schemas.file import FileMetaOut, FileOut, PresignedUrlOut
from app.services.file_service import FileService

router = APIRouter()


@router.post("", response_model=FileOut, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    note_ref: Optional[str] = Query(None, description="Note to attach the file to"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = FileService(db)
    return await svc.upload(uuid.UUID(user_id), file, note_ref)


@router.get("/{file_id}/url", response_model=PresignedUrlOut)
async def get_presigned_url(
    file_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = FileService(db)
    url = await svc.get_presigned_url(file_id, uuid.UUID(user_id))
    return PresignedUrlOut(url=url, expires_in=3600)


@router.get("/{file_id}/meta", response_model=FileMetaOut)
async def get_file_meta(
    file_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = FileService(db)
    return await svc.get_meta(file_id, uuid.UUID(user_id))


@router.get("", response_model=list[FileOut])
async def list_files(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = FileService(db)
    return await svc.list_files(uuid.UUID(user_id))


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = FileService(db)
    await svc.delete_file(file_id, uuid.UUID(user_id))
