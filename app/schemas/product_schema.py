from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load


class ProductQuerySchema(Schema):
    name = fields.String(load_default=None)
    category_id = fields.Integer(load_default=None)
    seller_id = fields.Integer(load_default=None)
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


class CreateProductSchema(Schema):
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


class ProductImageResponseSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    url = fields.String()
    order = fields.Integer()
    is_active = fields.Boolean()
    created_at = fields.DateTime(format='iso')


class ProductResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    slug = fields.String()
    price = fields.Float()
    stock = fields.Integer()
    image = fields.Method('get_primary_image')

    def get_primary_image(self, obj):
        primary = obj.primary_image
        return primary.url if primary else None


class CategoryResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    created_at = fields.DateTime(format='iso')
    is_active = fields.Boolean()


class ProductDetailResponseSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    slug = fields.String()
    price = fields.Float()
    stock = fields.Integer()
    description = fields.String()
    seller_id = fields.Integer(allow_none=True)
    created_at = fields.DateTime(format='iso')
    is_active = fields.Boolean()
    category = fields.Nested(CategoryResponseSchema, allow_none=True)
    images = fields.Method('get_images')

    def get_images(self, obj):
        return [img.to_dict() for img in obj.active_images]
