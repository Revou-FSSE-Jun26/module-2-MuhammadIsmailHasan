from marshmallow import Schema, fields, validate, pre_load


class CreateProductImageSchema(Schema):
    url = fields.String(
        required=True,
        validate=validate.Length(min=1, max=500, error="url cannot exceed 500 characters"),
        error_messages={"required": "url is required", "null": "url cannot be empty"},
    )

    @pre_load
    def strip_url(self, data, **kwargs):
        if 'url' in data and isinstance(data['url'], str):
            data['url'] = data['url'].strip()
            if not data['url']:
                data['url'] = None
        return data


class UpdateProductImageSchema(Schema):
    url = fields.String(
        load_default=None,
        validate=validate.Length(min=1, max=500, error="url cannot exceed 500 characters"),
    )

    @pre_load
    def strip_url(self, data, **kwargs):
        if 'url' in data and isinstance(data['url'], str):
            data['url'] = data['url'].strip()
            if not data['url']:
                data['url'] = None
        return data


class ReorderImagesSchema(Schema):
    image_ids = fields.List(
        fields.Integer(),
        required=True,
        validate=validate.Length(min=1, error="image_ids cannot be empty"),
        error_messages={
            "required": "image_ids is required",
            "invalid": "image_ids must be a list of numbers",
        },
    )


class ProductImageResponseSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    url = fields.String()
    order = fields.Integer()
    is_active = fields.Boolean()
    created_at = fields.DateTime(format='iso')
