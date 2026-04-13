import asyncio
import json
import logging
import uuid

from aiokafka import AIOKafkaConsumer

from app.config import settings

logger = logging.getLogger(__name__)

_consumer: AIOKafkaConsumer | None = None
_task: asyncio.Task | None = None


async def handle_user_deleted(payload: dict) -> None:
    """Delete all files belonging to the user from MinIO and mark them in the DB."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.repositories.file_repository import FileRepository
    from app.storage.minio import get_s3_client

    engine = create_async_engine(settings.database_url)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        repo = FileRepository(session)
        owner_id = uuid.UUID(payload["user_id"])
        files = await repo.list_by_owner(owner_id)

        async with get_s3_client() as s3:
            for f in files:
                try:
                    await s3.delete_object(Bucket=f.bucket, Key=f.object_key)
                except Exception:
                    logger.exception("Failed to delete object %s from bucket %s", f.object_key, f.bucket)

        await repo.delete_by_owner(owner_id)
        logger.info("Deleted %d files for user %s", len(files), payload["user_id"])

    await engine.dispose()


HANDLERS = {
    "user.deleted": handle_user_deleted,
}


async def _consume_loop() -> None:
    global _consumer
    _consumer = AIOKafkaConsumer(
        "user.events",
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        value_deserializer=lambda v: json.loads(v.decode()),
        auto_offset_reset="earliest",
    )
    await _consumer.start()
    try:
        async for msg in _consumer:
            event_type = msg.value.get("event_type")
            payload = msg.value.get("payload", {})
            handler = HANDLERS.get(event_type)
            if handler:
                try:
                    await handler(payload)
                except Exception:
                    logger.exception("Error handling event %s", event_type)
    finally:
        await _consumer.stop()


async def start_consumer() -> None:
    global _task
    _task = asyncio.create_task(_consume_loop())
    logger.info("Kafka consumer started (topic: user.events)")


async def stop_consumer() -> None:
    global _task, _consumer
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    if _consumer:
        await _consumer.stop()
