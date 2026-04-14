from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.kafka.producer import stop_producer
from app.middleware.rate_limit import RateLimitMiddleware
from app.models.user import Base
from app.routers import auth, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # PostgreSQL — создаём таблицы при старте (в продакшене лучше Alembic)
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.engine = engine
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)

    yield

    await stop_producer()
    await engine.dispose()


app = FastAPI(title="User Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(RateLimitMiddleware)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "user-service"}
