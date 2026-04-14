import time
from dataclasses import dataclass

import redis.asyncio as aioredis
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.dependencies import get_redis


@dataclass
class _Rule:
    method: str        # HTTP метод или "*" для любого
    path: str          # точный путь или префикс
    limit: int         # максимум запросов за окно
    window: int        # размер окна в секундах
    key: str           # slug для Redis-ключа


_RULES: list[_Rule] = [
    _Rule("*", "/", limit=100, window=60, key="global"),
]


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _match_rule(request: Request) -> _Rule | None:
    path = request.url.path
    method = request.method
    for rule in _RULES:
        method_match = rule.method == "*" or rule.method == method
        path_match = path == rule.path or path.startswith(rule.path)
        if method_match and path_match:
            return rule
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.rate_limit_enabled:
            return await call_next(request)

        rule = _match_rule(request)
        if rule is None:
            return await call_next(request)

        redis: aioredis.Redis = get_redis()
        ip = _get_client_ip(request)
        window_ts = int(time.time()) // rule.window
        redis_key = f"rl:{ip}:{rule.key}:{window_ts}"

        count = await redis.incr(redis_key)
        if count == 1:
            await redis.expire(redis_key, rule.window)

        remaining = max(0, rule.limit - count)
        reset_at = (window_ts + 1) * rule.window
        retry_after = reset_at - int(time.time())

        headers = {
            "X-RateLimit-Limit": str(rule.limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }

        if count > rule.limit:
            headers["Retry-After"] = str(retry_after)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers=headers,
            )

        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response
