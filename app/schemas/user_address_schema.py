from marshmallow import Schema, fields, validate, pre_load


def _strip(value):
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


class CreateAddressSchema(Schema):
    label = fields.String(
        allow_none=True,
        validate=validate.Length(max=50),
    )
    recipient_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=150),
        error_messages={"required": "recipient_name is required"},
    )
    phone = fields.String(
        required=True,
        validate=validate.Length(min=1, max=30),
        error_messages={"required": "phone is required"},
    )
    address_line = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
        error_messages={"required": "address_line is required"},
    )
    city = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "city is required"},
    )
    postal_code = fields.String(
        allow_none=True,
        validate=validate.Length(max=20),
    )
    is_default = fields.Boolean(load_default=False)

    @pre_load
    def strip_fields(self, data, **kwargs):
        for field in (
            'label', 'recipient_name', 'phone',
            'address_line', 'city', 'postal_code',
        ):
            if field in data:
                data[field] = _strip(data[field])
        return data


class UpdateAddressSchema(Schema):
    label = fields.String(allow_none=True, validate=validate.Length(max=50))
    recipient_name = fields.String(validate=validate.Length(min=1, max=150))
    phone = fields.String(validate=validate.Length(min=1, max=30))
    address_line = fields.String(validate=validate.Length(min=1, max=255))
    city = fields.String(validate=validate.Length(min=1, max=100))
    postal_code = fields.String(allow_none=True, validate=validate.Length(max=20))
    is_default = fields.Boolean()

    @pre_load
    def strip_fields(self, data, **kwargs):
        for field in (
            'label', 'recipient_name', 'phone',
            'address_line', 'city', 'postal_code',
        ):
            if field in data:
                data[field] = _strip(data[field])
        return data


class AddressResponseSchema(Schema):
    id = fields.Integer()
    user_id = fields.Integer()
    label = fields.String(allow_none=True)
    recipient_name = fields.String()
    phone = fields.String()
    address_line = fields.String()
    city = fields.String()
    postal_code = fields.String(allow_none=True)
    is_default = fields.Boolean()
    is_active = fields.Boolean()
    created_at = fields.DateTime(format='iso', allow_none=True)
    updated_at = fields.DateTime(format='iso', allow_none=True)
