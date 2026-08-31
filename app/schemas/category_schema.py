from marshmallow import Schema, fields, validate, pre_load

from app.utils.text import strip_or_none


class CategoryQuerySchema(Schema):
    name = fields.String(load_default=None)
    sort_by = fields.String(
        load_default='id',
        validate=validate.OneOf(['id', 'name', 'created_at']),
    )
    order = fields.String(
        load_default='asc',
        validate=validate.OneOf(['asc', 'desc']),
    )
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    limit = fields.Integer(load_default=10, validate=validate.Range(min=1, max=100))


class CreateCategorySchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error="name cannot exceed 255 characters"),
        error_messages={"required": "name is required", "null": "name cannot be empty"},
    )

    @pre_load
    def strip_name(self, data, **kwargs):
        if 'name' in data:
            data['name'] = strip_or_none(data['name'])
        return data


class UpdateCategorySchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error="name cannot exceed 255 characters"),
        error_messages={"required": "name is required", "null": "name cannot be empty"},
    )

    @pre_load
    def strip_name(self, data, **kwargs):
        if 'name' in data:
            data['name'] = strip_or_none(data['name'])
        return data


class CategoryResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    created_at = fields.DateTime(format='iso')
    is_active = fields.Boolean()


class ProductInCategorySchema(Schema):
    id = fields.Integer()
    name = fields.String()
    price = fields.Float()
    stock = fields.Integer()


class CategoryDetailResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    created_at = fields.DateTime(format='iso')
    is_active = fields.Boolean()
    products = fields.List(fields.Nested(ProductInCategorySchema))
