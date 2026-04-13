from datetime import datetime, timezone
from typing import Annotated, AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.session_factory() as session:
        yield session


class TokenData:
    def __init__(self, user_id: str, jti: str, exp: datetime):
        self.user_id = user_id
        self.jti = jti
        self.exp = exp


async def get_token_data(
    authorization: Annotated[str | None, Header()] = None,
    redis: aioredis.Redis = Depends(get_redis),
) -> TokenData:
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
        exp_ts = payload.get("exp")
        if not user_id or not jti or not exp_ts:
            raise credentials_error
        exp = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    except JWTError:
        raise credentials_error

    if await redis.get(f"jwt:blacklist:{jti}"):
        raise credentials_error

    return TokenData(user_id=user_id, jti=jti, exp=exp)


async def get_current_user_id(token: TokenData = Depends(get_token_data)) -> str:
    return token.user_id
