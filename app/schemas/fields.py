from marshmallow import fields

from app.utils.images import build_image_url


class ImageUrlField(fields.String):
    """Field read-only yang menempelkan IMAGE_BASE_URL ke key gambar."""

    def _serialize(self, value, attr, obj, **kwargs):
        return build_image_url(value)
