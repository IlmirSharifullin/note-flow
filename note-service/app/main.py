from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.kafka.consumer import start_consumer, stop_consumer
from app.kafka.producer import stop_producer
from app.models.note import Note, NoteHistory
from app.routers import notes, search, tags


@asynccontextmanager
async def lifespan(app: FastAPI):
    # MongoDB / Beanie
    client = AsyncIOMotorClient(settings.mongodb_url)
    await init_beanie(
        database=client[settings.mongodb_db],
        document_models=[Note, NoteHistory],
    )
    app.state.mongo_client = client

    # Kafka consumer (background task)
    await start_consumer()

    yield

    await stop_consumer()
    await stop_producer()
    client.close()


app = FastAPI(title="Note Service", version="0.1.0", lifespan=lifespan)

app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(tags.router, prefix="/tags", tags=["tags"])
app.include_router(search.router, prefix="/search", tags=["search"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "note-service"}
