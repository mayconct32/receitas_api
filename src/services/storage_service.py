import os
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.interfaces.storage import IStorage


class LocalstackS3Storage(IStorage):
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ) -> None:
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET")
        self.endpoint_url = endpoint_url or os.getenv("AWS_S3_ENDPOINT_URL")
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

        return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{file_name}"

    async def delete(self, *, file_name: str) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except (BotoCoreError, ClientError):
            return

        self.client.delete_object(Bucket=self.bucket_name, Key=file_name)
