import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from app.config import settings

logger = logging.getLogger(__name__)

_consumer: AIOKafkaConsumer | None = None
_task: asyncio.Task | None = None


async def handle_user_registered(payload: dict) -> None:
    """Create a welcome note for the new user."""
    from app.repositories.note_repository import NoteRepository
    repo = NoteRepository()
    await repo.create(
        user_id=payload["user_id"],
        title="Мой первый дневник",
        body="Добро пожаловать в NoteFlow! ✨\n\nЗдесь ты можешь вести личный дневник и заметки в формате **Markdown**.",
        tags=["welcome"],
    )
    logger.info("Welcome note created for user %s", payload.get("user_id"))


async def handle_user_deleted(payload: dict) -> None:
    """Soft-delete all notes when a user account is deleted."""
    from datetime import datetime
    from app.models.note import Note
    await Note.find(Note.user_id == payload["user_id"]).update(
        {"$set": {"deleted_at": datetime.utcnow()}}
    )
    logger.info("Soft-deleted all notes for user %s", payload.get("user_id"))


async def handle_file_uploaded(payload: dict) -> None:
    """Insert an attachment link into the referenced note."""
    from app.models.note import Note, Attachment
    from beanie import PydanticObjectId

    note_id = payload.get("note_id")
    if not note_id:
        return

    note = await Note.find_one(Note.id == PydanticObjectId(note_id))
    if note:
        attachment = Attachment(
            file_id=payload["file_id"],
            filename=payload["filename"],
            url=payload["url"],
        )
        note.attachments.append(attachment)
        await note.save()
        logger.info("Attachment %s added to note %s", payload["file_id"], note_id)


HANDLERS = {
    "user.registered": handle_user_registered,
    "user.deleted": handle_user_deleted,
    "file.uploaded": handle_file_uploaded,
}


async def _consume_loop() -> None:
    global _consumer
    _consumer = AIOKafkaConsumer(
        "user.events",
        "file.events",
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
    logger.info("Kafka consumer started (topics: user.events, file.events)")


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
