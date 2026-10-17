from flask import current_app

DEFAULT_IMAGE_BASE_URL = "/static/images"


def image_base_url():
    try:
        base = current_app.config.get("IMAGE_BASE_URL") or DEFAULT_IMAGE_BASE_URL
    except RuntimeError:
        base = DEFAULT_IMAGE_BASE_URL
    return base.rstrip("/")


def build_image_url(value):
    if not value:
        return None
    if value.startswith(("http://", "https://", "/")):
        return value
    return f"{image_base_url()}/{value}"


ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

EXTENSION_BY_SIGNATURE = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)

CONTENT_TYPE_BY_EXTENSION = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


class InvalidImageError(Exception):
    pass


def detect_image_extension(stream):
    """Ekstensi dari magic bytes, bukan dari nama file yang dikirim client."""
    head = stream.read(16)
    stream.seek(0)

    for signature, extension in EXTENSION_BY_SIGNATURE:
        if head.startswith(signature):
            return extension
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def validate_image_upload(file_storage, max_bytes):
    """Pastikan upload benar-benar gambar dan ukurannya wajar.

    Mengembalikan (extension, content_type). Nama file dan Content-Type dari
    client tidak dipercaya; keduanya bisa dipalsukan.
    """
    if file_storage is None or not file_storage.filename:
        raise InvalidImageError("file is required")

    stream = file_storage.stream
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)

    if size == 0:
        raise InvalidImageError("file is empty")
    if size > max_bytes:
        raise InvalidImageError(
            f"file is too large, maximum is {max_bytes // (1024 * 1024)} MB"
        )

    extension = detect_image_extension(stream)
    if extension is None:
        raise InvalidImageError(
            "file is not a valid image, allowed types are JPEG, PNG and WebP"
        )

    return extension, CONTENT_TYPE_BY_EXTENSION[extension]
