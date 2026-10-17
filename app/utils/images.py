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
