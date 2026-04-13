import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.kafka.producer import publish_event
from app.models.file import File
from app.repositories.file_repository import FileRepository
from app.storage.minio import get_s3_client


class FileService:
    def __init__(self, session: AsyncSession):
        self._repo = FileRepository(session)

    async def upload(
        self,
        owner_id: uuid.UUID,
        file: UploadFile,
        note_ref: Optional[uuid.UUID] = None,
    ) -> File:
        content = await file.read()
        if len(content) > settings.max_upload_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.max_upload_size // (1024 * 1024)} MB",
            )

        object_key = f"{owner_id}/{uuid.uuid4()}_{file.filename}"
        bucket = settings.minio_bucket_hot

        async with get_s3_client() as s3:
            await s3.put_object(
                Bucket=bucket,
                Key=object_key,
                Body=content,
                ContentType=file.content_type or "application/octet-stream",
            )

        db_file = await self._repo.create(
            owner_id=owner_id,
            original_name=file.filename or "unnamed",
            mime_type=file.content_type,
            size_bytes=len(content),
            bucket=bucket,
            object_key=object_key,
            note_ref=note_ref,
        )

        presigned_url = await self._presign(db_file.bucket, db_file.object_key)

        await publish_event(
            "file.events",
            "file.uploaded",
            {
                "file_id": str(db_file.id),
                "note_id": str(note_ref) if note_ref else None,
                "user_id": str(owner_id),
                "filename": db_file.original_name,
                "url": presigned_url,
            },
            key=str(db_file.id),
        )
        return db_file

    async def get_presigned_url(self, file_id: uuid.UUID, owner_id: uuid.UUID) -> str:
        db_file = await self._get_or_404(file_id, owner_id)
        await self._repo.touch(db_file)
        return await self._presign(db_file.bucket, db_file.object_key)

    async def get_meta(self, file_id: uuid.UUID, owner_id: uuid.UUID) -> File:
        return await self._get_or_404(file_id, owner_id)

    async def list_files(self, owner_id: uuid.UUID) -> list[File]:
        return await self._repo.list_by_owner(owner_id)

    async def delete_file(self, file_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        db_file = await self._get_or_404(file_id, owner_id)
        await self._repo.soft_delete(db_file)
        await publish_event(
            "file.events",
            "file.deleted",
            {"file_id": str(file_id), "user_id": str(owner_id)},
            key=str(file_id),
        )

    async def _get_or_404(self, file_id: uuid.UUID, owner_id: uuid.UUID) -> File:
        db_file = await self._repo.get_by_id(file_id, owner_id)
        if not db_file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        return db_file

    @staticmethod
    async def _presign(bucket: str, object_key: str) -> str:
        async with get_s3_client() as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": object_key},
                ExpiresIn=3600,
            )
