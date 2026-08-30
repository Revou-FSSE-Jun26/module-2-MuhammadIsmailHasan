from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load


class CreateProductImageSchema(Schema):
    url = fields.String(
        required=True,
        validate=validate.Length(min=1, max=500, error="url cannot exceed 500 characters"),
        error_messages={"required": "url is required", "null": "url cannot be empty"},
    )
    order = fields.Integer(
        load_default=0,
        error_messages={"invalid": "order must be a number"},
    )

    @pre_load
    def strip_url(self, data, **kwargs):
        if 'url' in data and isinstance(data['url'], str):
            data['url'] = data['url'].strip()
            if not data['url']:
                data['url'] = None
        return data

    @validates('order')
    def validate_order(self, value, **kwargs):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError("order must be a number")
        if value < 0:
            raise ValidationError("order cannot be negative")


class UpdateProductImageSchema(Schema):
    url = fields.String(
        load_default=None,
        validate=validate.Length(min=1, max=500, error="url cannot exceed 500 characters"),
    )
    order = fields.Integer(
        load_default=None,
        error_messages={"invalid": "order must be a number"},
    )

    @pre_load
    def strip_url(self, data, **kwargs):
        if 'url' in data and isinstance(data['url'], str):
            data['url'] = data['url'].strip()
            if not data['url']:
                data['url'] = None
        return data

    @validates('order')
    def validate_order(self, value, **kwargs):
        if value is None:
            return
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError("order must be a number")
        if value < 0:
            raise ValidationError("order cannot be negative")


class ProductImageResponseSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    url = fields.String()
    order = fields.Integer()
    is_active = fields.Boolean()
    created_at = fields.DateTime(format='iso')
