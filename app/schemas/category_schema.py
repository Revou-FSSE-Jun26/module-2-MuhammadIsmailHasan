from marshmallow import Schema, fields, validate, pre_load

from app.utils.text import strip_or_none
from app.schemas.product_schema import ProductResponseSchema


class CategoryQuerySchema(Schema):
    name = fields.String(load_default=None)
    sort_by = fields.String(
        load_default="id",
        validate=validate.OneOf(["id", "name", "created_at"]),
    )
    order = fields.String(
        load_default="asc",
        validate=validate.OneOf(["asc", "desc"]),
    )
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    limit = fields.Integer(load_default=10, validate=validate.Range(min=1, max=100))


class CreateCategorySchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(
            min=1, max=255, error="name cannot exceed 255 characters"
        ),
        error_messages={"required": "name is required", "null": "name cannot be empty"},
    )
    image = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=500, error="image cannot exceed 500 characters"),
    )

    @pre_load
    def strip_name(self, data, **kwargs):
        if "name" in data:
            data["name"] = strip_or_none(data["name"])
        return data


class UpdateCategorySchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(
            min=1, max=255, error="name cannot exceed 255 characters"
        ),
        error_messages={"required": "name is required", "null": "name cannot be empty"},
    )
    image = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=500, error="image cannot exceed 500 characters"),
    )

    @pre_load
    def strip_name(self, data, **kwargs):
        if "name" in data:
            data["name"] = strip_or_none(data["name"])
        return data


class CategoryResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    image = fields.String(allow_none=True)
    created_at = fields.DateTime(format="iso")
    is_active = fields.Boolean()


class SubCategoryWithProductsSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    image = fields.String(allow_none=True)
    category_id = fields.Integer(allow_none=True)
    created_at = fields.DateTime(format="iso")
    is_active = fields.Boolean()
    products = fields.List(
        fields.Nested(ProductResponseSchema), attribute="active_products"
    )


class CategoryWithProductsSchema(Schema):
    """Category list item carrying a flat `products` list.

    Used by GET /api/v1/categories/products, whose existing response shape is
    preserved (a flat product list per category, not the nested
    category -> sub_categories -> products tree used by the detail endpoints).
    """

    id = fields.Integer()
    name = fields.String()
    image = fields.String(allow_none=True)
    created_at = fields.DateTime(format="iso")
    is_active = fields.Boolean()
    products = fields.List(fields.Nested(ProductResponseSchema))


class CategoryDetailResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    image = fields.String(allow_none=True)
    created_at = fields.DateTime(format="iso")
    is_active = fields.Boolean()
    sub_categories = fields.List(
        fields.Nested(SubCategoryWithProductsSchema),
        attribute="active_sub_categories",
    )
