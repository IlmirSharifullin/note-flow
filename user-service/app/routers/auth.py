from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db, get_redis, get_token_data
from app.schemas.user import LoginRequest, RegisterRequest, TokenPair, UserOut
from app.services.auth_service import REFRESH_TOKEN_COOKIE, AuthService

import redis.asyncio as aioredis

router = APIRouter()

_REFRESH_COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 days in seconds


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=_REFRESH_COOKIE_MAX_AGE,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/auth/refresh")


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    svc = AuthService(db, redis)
    user, token_pair, refresh_raw = await svc.register(
        data.email, data.password, data.display_name
    )
    _set_refresh_cookie(response, refresh_raw)
    response.headers["X-Access-Token"] = token_pair.access_token
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    user_agent = request.headers.get("user-agent")
    ip_addr = request.client.host if request.client else None
    svc = AuthService(db, redis)
    _user, token_pair, refresh_raw = await svc.login(
        data.email, data.password, user_agent, ip_addr
    )
    _set_refresh_cookie(response, refresh_raw)
    return token_pair


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
):
    if not refresh_token:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    svc = AuthService(db, redis)
    return await svc.refresh(refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    token=Depends(get_token_data),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
):
    svc = AuthService(db, redis)
    await svc.logout(token.jti, token.exp, refresh_token)
    _clear_refresh_cookie(response)
