import asyncio
import logging
from functools import lru_cache
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)
S3_URI_PREFIX = "neon-s3://"


class StorageConfigurationError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _s3_client():
    required = {
        "AWS_ENDPOINT_URL_S3": settings.AWS_ENDPOINT_URL_S3,
        "AWS_ACCESS_KEY_ID": settings.AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": settings.AWS_SECRET_ACCESS_KEY,
        "AWS_BUCKET_NAME": settings.AWS_BUCKET_NAME,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise StorageConfigurationError(
            "Persistent resume storage is not configured. Set " + ", ".join(missing) + " in the backend environment."
        )
    try:
        import boto3
    except ImportError as exc:
        raise StorageConfigurationError("Persistent storage dependency is missing; install backend requirements.") from exc
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_ENDPOINT_URL_S3,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def is_remote_path(file_path: str) -> bool:
    return file_path.startswith(S3_URI_PREFIX)


def ensure_storage_ready() -> None:
    """Fail before creating a candidate record if remote storage is misconfigured."""
    if settings.USE_S3:
        _s3_client()


def _remote_key(file_path: str) -> str:
    return file_path[len(S3_URI_PREFIX):].split("/", 1)[1]


async def save_resume(filename: str, contents: bytes, content_type: Optional[str] = None) -> str:
    if settings.USE_S3:
        client = _s3_client()
        key = f"resumes/{filename}"
        kwargs = {"Bucket": settings.AWS_BUCKET_NAME, "Key": key, "Body": contents}
        if content_type:
            kwargs["ContentType"] = content_type
        await asyncio.to_thread(client.put_object, **kwargs)
        return f"{S3_URI_PREFIX}{settings.AWS_BUCKET_NAME}/{key}"

    import os
    upload_dir = os.path.join(settings.UPLOAD_DIR, "resumes")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as file_obj:
        file_obj.write(contents)
    return file_path


async def read_resume(file_path: str) -> bytes:
    if is_remote_path(file_path):
        bucket, key = file_path[len(S3_URI_PREFIX):].split("/", 1)
        result = await asyncio.to_thread(
            _s3_client().get_object, Bucket=bucket, Key=key
        )
        return await asyncio.to_thread(result["Body"].read)
    with open(file_path, "rb") as file_obj:
        return file_obj.read()
