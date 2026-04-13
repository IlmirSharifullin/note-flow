import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File


class FileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        owner_id: uuid.UUID,
        original_name: str,
        mime_type: Optional[str],
        size_bytes: Optional[int],
        bucket: str,
        object_key: str,
        note_ref: Optional[uuid.UUID] = None,
    ) -> File:
        file = File(
            owner_id=owner_id,
            original_name=original_name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            bucket=bucket,
            object_key=object_key,
            note_ref=note_ref,
        )
        self.session.add(file)
        await self.session.commit()
        await self.session.refresh(file)
        return file

    async def get_by_id(self, file_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[File]:
        result = await self.session.execute(
            select(File).where(
                File.id == file_id,
                File.owner_id == owner_id,
                File.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[File]:
        result = await self.session.execute(
            select(File).where(File.owner_id == owner_id, File.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def soft_delete(self, file: File) -> File:
        file.deleted_at = datetime.utcnow()
        file.status = "deleted"
        await self.session.commit()
        return file

    async def delete_by_owner(self, owner_id: uuid.UUID) -> None:
        files = await self.list_by_owner(owner_id)
        now = datetime.utcnow()
        for f in files:
            f.deleted_at = now
            f.status = "deleted"
        await self.session.commit()

    async def touch(self, file: File) -> None:
        file.last_accessed = datetime.utcnow()
        await self.session.commit()
