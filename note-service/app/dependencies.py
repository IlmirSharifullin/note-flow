from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.config import settings

_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
    redis: aioredis.Redis = Depends(get_redis),
) -> str:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_error
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        if not user_id or not jti:
            raise credentials_error
    except JWTError:
        raise credentials_error

    if await redis.get(f"jwt:blacklist:{jti}"):
        raise credentials_error

    return user_id
