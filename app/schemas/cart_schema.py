from marshmallow import (
    Schema, fields, validates, validates_schema, ValidationError,
)


class AddCartItemSchema(Schema):
    product_id = fields.Integer(
        required=True,
        error_messages={
            "required": "product_id is required",
            "invalid": "product_id must be a number",
        },
    )
    quantity = fields.Integer(
        load_default=1,
        error_messages={"invalid": "quantity must be a number"},
    )

    @validates('quantity')
    def validate_quantity(self, value, **kwargs):
        if value is None:
            return
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError("quantity must be a number")
        if value <= 0:
            raise ValidationError("quantity must be greater than 0")


class UpdateCartItemSchema(Schema):
    quantity = fields.Integer(
        required=True,
        error_messages={
            "required": "quantity is required",
            "invalid": "quantity must be a number",
        },
    )

    @validates('quantity')
    def validate_quantity(self, value, **kwargs):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError("quantity must be a number")
        if value < 0:
            raise ValidationError("quantity cannot be negative")


class CheckoutSchema(Schema):
    seller_id = fields.Integer(
        load_default=None,
        error_messages={"invalid": "seller_id must be a number"},
    )
    cart_item_ids = fields.List(
        fields.Integer(),
        load_default=None,
        error_messages={"invalid": "cart_item_ids must be a list of numbers"},
    )
    address_id = fields.Integer(
        load_default=None,
        error_messages={"invalid": "address_id must be a number"},
    )

    @validates_schema
    def validate_selection(self, data, **kwargs):
        seller_id = data.get('seller_id')
        cart_item_ids = data.get('cart_item_ids')

        if seller_id is not None and cart_item_ids is not None:
            raise ValidationError(
                "provide either seller_id or cart_item_ids, not both",
                field_name="_schema",
            )
        if cart_item_ids is not None and len(cart_item_ids) == 0:
            raise ValidationError(
                "cart_item_ids cannot be empty", field_name="cart_item_ids"
            )


class CartItemProductSchema(Schema):
    id = fields.Integer(allow_none=True)
    name = fields.String(allow_none=True)
    slug = fields.String(allow_none=True)
    price = fields.Float(allow_none=True)
    stock = fields.Integer(allow_none=True)
    is_active = fields.Boolean(allow_none=True)
    image = fields.String(allow_none=True)


class CartItemViewSchema(Schema):
    id = fields.Integer()
    product_id = fields.Integer()
    quantity = fields.Integer()
    unit_price = fields.Float(allow_none=True)
    sub_total = fields.Float(allow_none=True)
    available = fields.Boolean()
    note = fields.String(allow_none=True)
    product = fields.Nested(CartItemProductSchema, allow_none=True)


class CartGroupSchema(Schema):
    seller_id = fields.Integer(allow_none=True)
    seller_name = fields.String()
    items = fields.List(fields.Nested(CartItemViewSchema))
    group_total_items = fields.Integer()
    group_total_quantity = fields.Integer()
    group_total = fields.Float()


class CartResponseSchema(Schema):
    cart_id = fields.Integer(allow_none=True)
    groups = fields.List(fields.Nested(CartGroupSchema))
    total_items = fields.Integer()
    total_quantity = fields.Integer()
    grand_total = fields.Float()
