from marshmallow import Schema, fields, validate, pre_load

from app.utils.text import strip_or_none


class UpdateProfileSchema(Schema):
    full_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=150),
    )
    phone = fields.String(
        allow_none=True,
        validate=validate.Length(max=30),
    )
    avatar_url = fields.String(
        allow_none=True,
        validate=validate.Length(max=255),
    )

    @pre_load
    def strip_fields(self, data, **kwargs):
        for field in ('full_name', 'phone', 'avatar_url'):
            if field in data:
                data[field] = strip_or_none(data[field])
        return data


class ProfileResponseSchema(Schema):
    id = fields.Integer()
    user_id = fields.Integer()
    full_name = fields.String(allow_none=True)
    phone = fields.String(allow_none=True)
    avatar_url = fields.String(allow_none=True)
    is_active = fields.Boolean()
    created_at = fields.DateTime(format='iso', allow_none=True)
    updated_at = fields.DateTime(format='iso', allow_none=True)
