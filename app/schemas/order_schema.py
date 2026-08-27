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


class UpdateOrderStatusSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            ['waiting_for_payment', 'processing', 'shipped', 'delivered', 'cancelled'],
            error="status must be one of: waiting_for_payment, processing, shipped, delivered, cancelled",
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


class OrderItemResponseSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    product_name = fields.String()
    unit_price = fields.Float()
    quantity = fields.Integer()
    sub_total = fields.Float()


class OrderResponseSchema(Schema):
    id = fields.Integer()
    user_id = fields.Integer()
    total_amount = fields.Float()
    status = fields.String()
    ordered_at = fields.DateTime(format='iso')


class OrderDetailResponseSchema(Schema):
    id = fields.Integer()
    user_id = fields.Integer()
    total_amount = fields.Float()
    status = fields.String()
    ordered_at = fields.DateTime(format='iso')
    is_active = fields.Boolean()
    items = fields.List(fields.Nested(OrderItemResponseSchema))
