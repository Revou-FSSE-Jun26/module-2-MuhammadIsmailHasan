from marshmallow import Schema, fields, validate, pre_load


def _strip(value):
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value


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
                data[field] = _strip(data[field])
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
