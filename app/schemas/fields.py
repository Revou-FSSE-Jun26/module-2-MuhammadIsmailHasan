from marshmallow import fields

from app.utils.images import build_image_url


class ImageUrlField(fields.String):

    def _serialize(self, value, attr, obj, **kwargs):
        return build_image_url(value)
