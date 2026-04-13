import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Response, Security, status
from fastapi.security import HTTPBearer

_bearer = HTTPBearer(auto_error=False)
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db, get_redis, get_token_data
from app.schemas.user import ProfileUpdate, UserOut
from app.services.user_service import UserService

router = APIRouter(dependencies=[Security(_bearer)])


@router.get("/me", response_model=UserOut)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    svc = UserService(db, redis)
    user = await svc.get_profile(uuid.UUID(user_id))
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    svc = UserService(db, redis)
    user = await svc.update_profile(
        uuid.UUID(user_id),
        display_name=data.display_name,
        avatar_url=data.avatar_url,
    )
    return UserOut.model_validate(user)


@router.delete("/me", status_code=204)
async def delete_me(
    response: Response,
    token=Depends(get_token_data),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    svc = UserService(db, redis)
    await svc.delete_account(uuid.UUID(token.user_id))
    # Сразу инвалидируем текущий access token
    from datetime import datetime, timezone
    ttl = int((token.exp - datetime.now(tz=timezone.utc)).total_seconds())
    if ttl > 0:
        await redis.setex(f"jwt:blacklist:{token.jti}", ttl, "1")
