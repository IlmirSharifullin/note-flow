from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.kafka.consumer import start_consumer, stop_consumer
from app.kafka.producer import stop_producer
from app.models.file import Base
from app.routers import files
from app.storage.minio import ensure_buckets


@asynccontextmanager
async def lifespan(app: FastAPI):
    # PostgreSQL
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.engine = engine
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # MinIO buckets
    await ensure_buckets()

    # Kafka consumer (background task)
    await start_consumer()

    yield

    await stop_consumer()
    await stop_producer()
    await engine.dispose()


app = FastAPI(title="File Service", version="0.1.0", lifespan=lifespan)

app.include_router(files.router, prefix="/files", tags=["files"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "file-service"}
