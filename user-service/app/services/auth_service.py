import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import redis.asyncio as aioredis
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.kafka.producer import publish_event
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenPair

REFRESH_TOKEN_COOKIE = "refresh_token"

# Redis key схема:
#   refresh:{hash}       → JSON {user_id, ua, ip}   TTL = 30d
#   sessions:{user_id}   → Set хешей токенов         (для revoke-all)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(12)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _make_access_token(user_id: uuid.UUID, jti: str) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": str(user_id), "jti": jti, "exp": expire, "type": "access"},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


_REFRESH_TTL = settings.refresh_token_expire_days * 86400


class AuthService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis):
        self._repo = UserRepository(session)
        self._redis = redis

    async def register(
        self, email: str, password: str, display_name: str | None = None
    ) -> tuple[User, TokenPair, str]:
        if await self._repo.get_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = await self._repo.create(email, _hash_password(password), display_name)
        token_pair, refresh_raw = await self._issue_tokens(user)

        await publish_event(
            "user.events",
            "user.registered",
            {"user_id": str(user.id), "email": user.email},
            key=str(user.id),
        )
        return user, token_pair, refresh_raw

    async def login(
        self,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_addr: str | None = None,
    ) -> tuple[User, TokenPair, str]:
        user = await self._repo.get_by_email(email)
        if not user or not _verify_password(password, user.pass_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        token_pair, refresh_raw = await self._issue_tokens(user, user_agent, ip_addr)
        return user, token_pair, refresh_raw

    async def refresh(self, refresh_raw: str) -> TokenPair:
        token_hash = _hash_token(refresh_raw)
        data = await self._redis.get(f"refresh:{token_hash}")
        if not data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = json.loads(data)["user_id"]
        user = await self._repo.get_by_id(uuid.UUID(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        # Ротация: удаляем старый, выдаём новый access
        await self._revoke_token(token_hash, user_id)
        jti = str(uuid.uuid4())
        return TokenPair(access_token=_make_access_token(user.id, jti))

    async def logout(self, jti: str, access_exp: datetime, refresh_raw: str | None) -> None:
        # Blacklist access token до истечения
        ttl = int((access_exp - datetime.now(tz=timezone.utc)).total_seconds())
        if ttl > 0:
            await self._redis.setex(f"jwt:blacklist:{jti}", ttl, "1")

        if refresh_raw:
            token_hash = _hash_token(refresh_raw)
            raw = await self._redis.get(f"refresh:{token_hash}")
            if raw:
                user_id = json.loads(raw)["user_id"]
                await self._revoke_token(token_hash, user_id)

    async def revoke_all_sessions(self, user_id: str) -> None:
        """Отзывает все refresh-токены пользователя (выход со всех устройств)."""
        key = f"sessions:{user_id}"
        hashes = await self._redis.smembers(key)
        if hashes:
            pipe = self._redis.pipeline()
            for h in hashes:
                pipe.delete(f"refresh:{h}")
            pipe.delete(key)
            await pipe.execute()

    # ── Внутренние методы ─────────────────────────────────────────────────

    async def _issue_tokens(
        self,
        user: User,
        user_agent: str | None = None,
        ip_addr: str | None = None,
    ) -> tuple[TokenPair, str]:
        jti = str(uuid.uuid4())
        access_token = _make_access_token(user.id, jti)

        refresh_raw = secrets.token_urlsafe(64)
        token_hash = _hash_token(refresh_raw)
        payload = json.dumps({"user_id": str(user.id), "ua": user_agent, "ip": ip_addr})

        pipe = self._redis.pipeline()
        # Данные токена с TTL
        pipe.setex(f"refresh:{token_hash}", _REFRESH_TTL, payload)
        # Добавляем хеш в Set сессий пользователя
        pipe.sadd(f"sessions:{user.id}", token_hash)
        pipe.expire(f"sessions:{user.id}", _REFRESH_TTL)
        await pipe.execute()

        return TokenPair(access_token=access_token), refresh_raw

    async def _revoke_token(self, token_hash: str, user_id: str) -> None:
        pipe = self._redis.pipeline()
        pipe.delete(f"refresh:{token_hash}")
        pipe.srem(f"sessions:{user_id}", token_hash)
        await pipe.execute()
