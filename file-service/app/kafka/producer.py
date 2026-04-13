import json

from aiokafka import AIOKafkaProducer

from app.config import settings

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode(),
            key_serializer=lambda k: k.encode() if k else None,
        )
        await _producer.start()
    return _producer


async def publish_event(topic: str, event_type: str, payload: dict, key: str | None = None) -> None:
    producer = await get_producer()
    message = {"event_type": event_type, "payload": payload}
    await producer.send(topic, value=message, key=key)


async def stop_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
