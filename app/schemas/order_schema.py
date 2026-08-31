from marshmallow import Schema, fields, validate, validates, ValidationError


class OrderItemInputSchema(Schema):
    product_id = fields.Integer(
        required=True,
        error_messages={"required": "product_id is required", "invalid": "product_id must be a number"},
    )
    quantity = fields.Integer(
        required=True,
        error_messages={"required": "quantity is required", "invalid": "quantity must be a number"},
    )

    @validates('quantity')
    def validate_quantity(self, value, **kwargs):
        if value <= 0:
            raise ValidationError("quantity must be greater than 0")


class CreateOrderSchema(Schema):
    items = fields.List(
        fields.Nested(OrderItemInputSchema),
        required=True,
        validate=validate.Length(min=1, error="items cannot be empty"),
        error_messages={"required": "items is required", "invalid": "items must be a list"},
    )
    address_id = fields.Integer(
        load_default=None,
        error_messages={"invalid": "address_id must be a number"},
    )


class ChangeOrderAddressSchema(Schema):
    address_id = fields.Integer(
        required=True,
        error_messages={
            "required": "address_id is required",
            "invalid": "address_id must be a number",
        },
    )


class UpdateOrderStatusSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            ['processing', 'shipped', 'delivered'],
            error="status must be one of: processing, shipped, delivered",
        ),
        error_messages={"required": "status is required"},
    )


class OrderQuerySchema(Schema):
    status = fields.String(
        load_default=None,
        validate=validate.OneOf(
            ['waiting_for_payment', 'processing', 'shipped', 'delivered', 'cancelled'],
        ),
    )
    include_deleted = fields.Boolean(load_default=False)
    sort_by = fields.String(
        load_default='id',
        validate=validate.OneOf(['id', 'total_amount', 'ordered_at']),
    )
    order = fields.String(
        load_default='desc',
        validate=validate.OneOf(['asc', 'desc']),
    )
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    limit = fields.Integer(load_default=10, validate=validate.Range(min=1, max=100))


class OrderItemProductSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    slug = fields.String()
    price = fields.Float()
    stock = fields.Integer()
    description = fields.String()
    is_active = fields.Boolean()
    image = fields.Method('get_primary_image')

    def get_primary_image(self, obj):
        primary = obj.primary_image
        return primary.url if primary else None


class OrderItemResponseSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    product_name = fields.String()
    unit_price = fields.Float()
    quantity = fields.Integer()
    sub_total = fields.Float()
    product = fields.Nested(OrderItemProductSchema, allow_none=True)


class OrderResponseSchema(Schema):
    id = fields.Integer()
    user_id = fields.Integer()
    total_amount = fields.Float()
    status = fields.String()
    ordered_at = fields.DateTime(format='iso')
    updated_by = fields.Integer(allow_none=True)
    shipping_recipient_name = fields.String(allow_none=True)
    shipping_phone = fields.String(allow_none=True)
    shipping_address_line = fields.String(allow_none=True)
    shipping_city = fields.String(allow_none=True)
    shipping_postal_code = fields.String(allow_none=True)
    total_items = fields.Method('get_total_items')
    total_quantity = fields.Method('get_total_quantity')

    def get_total_items(self, obj):
        return len(obj.items)

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items)


class OrderDetailResponseSchema(Schema):
    id = fields.Integer()
    user_id = fields.Integer()
    total_amount = fields.Float()
    status = fields.String()
    ordered_at = fields.DateTime(format='iso')
    updated_by = fields.Integer(allow_none=True)
    shipping_recipient_name = fields.String(allow_none=True)
    shipping_phone = fields.String(allow_none=True)
    shipping_address_line = fields.String(allow_none=True)
    shipping_city = fields.String(allow_none=True)
    shipping_postal_code = fields.String(allow_none=True)
    is_active = fields.Boolean()
    total_items = fields.Method('get_total_items')
    total_quantity = fields.Method('get_total_quantity')
    items = fields.List(fields.Nested(OrderItemResponseSchema))

    def get_total_items(self, obj):
        return len(obj.items)

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items)
