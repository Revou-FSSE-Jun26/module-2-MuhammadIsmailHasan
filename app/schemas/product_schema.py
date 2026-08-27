"""
Product schemas using Marshmallow.

- Request schemas: validate incoming data (used by @blp.arguments)
- Response schemas: serialize outgoing data (used by @blp.response)
- Query schemas: validate query parameters for filtering/pagination
"""

from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load


# ─── Query Parameter Schema ──────────────────────────────────────────────────


class ProductQuerySchema(Schema):
    """Validates query parameters for GET /products."""

    name = fields.String(load_default=None)
    category_id = fields.Integer(load_default=None)
    min_price = fields.Float(load_default=None)
    max_price = fields.Float(load_default=None)
    sort_by = fields.String(
        load_default='id',
        validate=validate.OneOf(['id', 'name', 'price', 'created_at']),
    )
    order = fields.String(
        load_default='asc',
        validate=validate.OneOf(['asc', 'desc']),
    )
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    limit = fields.Integer(load_default=10, validate=validate.Range(min=1, max=100))


# ─── Request Schemas (input validation) ──────────────────────────────────────


class CreateProductSchema(Schema):
    """Validates incoming data when creating a product."""

    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error="name cannot exceed 255 characters"),
        error_messages={"required": "name is required", "null": "name cannot be empty"},
    )
    price = fields.Float(
        required=True,
        error_messages={"required": "price is required", "invalid": "price must be a number"},
    )
    stock = fields.Integer(
        required=True,
        error_messages={"required": "stock is required", "invalid": "stock must be number"},
    )
    description = fields.String(
        load_default=None,
        validate=validate.Length(max=1000, error="description cannot exceed 1000 characters"),
    )
    category_id = fields.Integer(
        load_default=None,
        error_messages={"invalid": "category_id must be a number"},
    )

    @pre_load
    def strip_name(self, data, **kwargs):
        """Strip whitespace from name before validation."""
        if 'name' in data and isinstance(data['name'], str):
            data['name'] = data['name'].strip()
            if not data['name']:
                data['name'] = None
        return data

    @validates('price')
    def validate_price(self, value, **kwargs):
        if value < 0:
            raise ValidationError("price cannot be negative")
        if value > 10**11:
            raise ValidationError("price cannot exceed 11 digits number")

    @validates('stock')
    def validate_stock(self, value, **kwargs):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError("stock must be number")


class UpdateProductSchema(Schema):
    """Validates incoming data when updating a product. All fields optional."""

    name = fields.String(
        load_default=None,
        validate=validate.Length(min=1, max=255, error="name cannot exceed 255 characters"),
    )
    price = fields.Float(
        load_default=None,
        error_messages={"invalid": "price must be a number"},
    )
    stock = fields.Integer(
        load_default=None,
        error_messages={"invalid": "stock must be number"},
    )
    description = fields.String(
        load_default=None,
        validate=validate.Length(max=1000, error="description cannot exceed 1000 characters"),
    )
    category_id = fields.Integer(
        load_default=None,
        error_messages={"invalid": "category_id must be a number"},
    )

    @pre_load
    def strip_name(self, data, **kwargs):
        if 'name' in data and isinstance(data['name'], str):
            data['name'] = data['name'].strip()
            if not data['name']:
                data['name'] = None
        return data

    @validates('price')
    def validate_price(self, value, **kwargs):
        if value is None:
            return
        if value < 0:
            raise ValidationError("price cannot be negative")
        if value > 10**11:
            raise ValidationError("price cannot exceed 11 digits number")

    @validates('stock')
    def validate_stock(self, value, **kwargs):
        if value is None:
            return
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError("stock must be number")


# ─── Response Schemas (output serialization) ─────────────────────────────────


class ProductResponseSchema(Schema):
    """Serializes product for list responses."""

    id = fields.Integer()
    name = fields.String()
    price = fields.Float()
    stock = fields.Integer()


class CategoryResponseSchema(Schema):
    """Nested schema for category in product detail."""

    id = fields.Integer()
    name = fields.String()
    created_at = fields.DateTime(format='iso')
    is_active = fields.Boolean()


class ProductDetailResponseSchema(Schema):
    """Serializes full product detail including category."""

    id = fields.Integer()
    name = fields.String()
    price = fields.Float()
    stock = fields.Integer()
    description = fields.String()
    created_at = fields.DateTime(format='iso')
    is_active = fields.Boolean()
    category = fields.Nested(CategoryResponseSchema, allow_none=True)
