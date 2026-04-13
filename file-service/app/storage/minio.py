from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from aiobotocore.session import get_session

from app.config import settings


@asynccontextmanager
async def get_s3_client() -> AsyncGenerator[Any, None]:
    session = get_session()
    scheme = "https" if settings.minio_use_ssl else "http"
    async with session.create_client(
        "s3",
        endpoint_url=f"{scheme}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name="us-east-1",
    ) as client:
        yield client


async def ensure_buckets() -> None:
    """Create MinIO buckets on startup if they don't exist."""
    async with get_s3_client() as s3:
        for bucket in (settings.minio_bucket_hot, settings.minio_bucket_warm):
            try:
                await s3.head_bucket(Bucket=bucket)
            except Exception:
                await s3.create_bucket(Bucket=bucket)

