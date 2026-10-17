import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import current_app

PRODUCT_PREFIX = "products"


class ImageStorageError(Exception):
    pass


def _bucket():
    bucket = current_app.config.get("AWS_S3_BUCKET")
    if not bucket:
        raise ImageStorageError("image storage is not configured")
    return bucket


def _client():
    return boto3.client("s3", region_name=current_app.config.get("AWS_S3_REGION"))


def is_configured():
    return bool(current_app.config.get("AWS_S3_BUCKET"))


def build_product_key(product_id, extension):
    return f"{PRODUCT_PREFIX}/{product_id}/{uuid.uuid4().hex}.{extension}"


def upload(stream, key, content_type):
    try:
        _client().upload_fileobj(
            stream,
            _bucket(),
            key,
            ExtraArgs={
                "ContentType": content_type,
                "CacheControl": "public, max-age=31536000, immutable",
            },
        )
    except (BotoCoreError, ClientError) as error:
        raise ImageStorageError(f"failed to upload image: {error}") from error
    return key


def delete(key):
    try:
        _client().delete_object(Bucket=_bucket(), Key=key)
    except (BotoCoreError, ClientError) as error:
        current_app.logger.warning("failed to delete orphan object %s: %s", key, error)
