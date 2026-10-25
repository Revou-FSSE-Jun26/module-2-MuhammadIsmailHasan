from flask import current_app

from app.integrations import s3
from app.integrations.s3 import ImageStorageError
from app.utils.images import validate_image_upload


def replace_image(record, prefix, file_storage, save):
    if not s3.is_configured():
        raise ImageStorageError("image storage is not configured")

    extension, content_type = validate_image_upload(
        file_storage, current_app.config["MAX_IMAGE_UPLOAD_BYTES"]
    )

    old_key = record.image
    key = s3.build_key(prefix, record.id, extension)
    s3.upload(file_storage.stream, key, content_type)

    try:
        updated = save(record, {"image": key})
    except Exception:
        s3.delete(key)
        raise

    if s3.is_managed_key(old_key, prefix):
        s3.delete(old_key)

    return updated
