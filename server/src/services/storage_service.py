import inspect
import os
from typing import Optional
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile

from ..interfaces.storage import IStorage


class LocalstackS3Storage(IStorage):
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        public_endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET")
        self.endpoint_url = (endpoint_url or os.getenv("AWS_S3_ENDPOINT_URL") or "http://localstack:4566").rstrip("/")
        self.public_endpoint_url = (
            public_endpoint_url
            or os.getenv("AWS_S3_PUBLIC_ENDPOINT_URL")
            or "http://localhost:4566"
        ).rstrip("/")
        self.region_name = region_name or os.getenv("AWS_DEFAULT_REGION")
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    async def upload(
        self,
        *,
        file_name: str,
        file_bytes: bytes,
        content_type: str,
    ) -> str:
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except (BotoCoreError, ClientError):
            self.client.create_bucket(Bucket=self.bucket_name)

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=file_name,
            Body=file_bytes,
            ContentType=content_type,
        )

        return f"{self.public_endpoint_url}/{self.bucket_name}/{file_name}"

    async def delete(self, *, file_name: str) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except (BotoCoreError, ClientError):
            return

        self.client.delete_object(Bucket=self.bucket_name, Key=file_name)


class RecipeImageService:
    def __init__(self, storage: IStorage) -> None:
        self.storage = storage

    @staticmethod
    def _extract_file_name(image_url: str | None) -> str | None:
        if not image_url:
            return None
        return image_url.split("/")[-1]

    async def upload(self, image: UploadFile | None) -> str | None:
        if image is None or not getattr(image, "filename", None):
            return None

        seek = getattr(image, "seek", None)
        if seek is not None:
            if inspect.iscoroutinefunction(seek):
                await seek(0)
            else:
                seek(0)

        read = getattr(image, "read")
        if inspect.iscoroutinefunction(read):
            file_bytes = await read()
        else:
            file_bytes = read()

        file_name = f"{uuid4()}-{image.filename}"
        content_type = getattr(image, "content_type", None) or "application/octet-stream"

        return await self.storage.upload(
            file_name=file_name,
            file_bytes=file_bytes,
            content_type=content_type,
        )

    async def delete(self, image_url: str | None) -> None:
        file_name = self._extract_file_name(image_url)
        if file_name is None:
            return
        await self.storage.delete(file_name=file_name)
