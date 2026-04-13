import uuid
from typing import Optional

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.kafka.producer import publish_event
from app.models.user import User
from app.repositories.user_repository import UserRepository

_PROFILE_CACHE_TTL = 900  # 15 min


class UserService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis):
        self._repo = UserRepository(session)
        self._redis = redis

    async def get_profile(self, user_id: uuid.UUID) -> User:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def update_profile(
        self,
        user_id: uuid.UUID,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        user = await self.get_profile(user_id)

        fields: dict = {}
        if display_name is not None:
            fields["display_name"] = display_name
        if avatar_url is not None:
            fields["avatar_url"] = avatar_url

        if not fields:
            return user

        user = await self._repo.update(user, **fields)

        # Инвалидируем кэш профиля
        await self._redis.delete(f"user:{user_id}")

        await publish_event(
            "user.events",
            "user.updated",
            {"user_id": str(user_id)},
            key=str(user_id),
        )
        return user

    async def delete_account(self, user_id: uuid.UUID) -> None:
        user = await self.get_profile(user_id)
        await self._repo.soft_delete(user)

        # Отзываем все refresh-токены пользователя из Redis
        sessions_key = f"sessions:{user_id}"
        hashes = await self._redis.smembers(sessions_key)
        if hashes:
            pipe = self._redis.pipeline()
            for h in hashes:
                pipe.delete(f"refresh:{h}")
            pipe.delete(sessions_key)
            await pipe.execute()

        # Чистим кэш профиля
        await self._redis.delete(f"user:{user_id}")

        await publish_event(
            "user.events",
            "user.deleted",
            {"user_id": str(user_id)},
            key=str(user_id),
        )
