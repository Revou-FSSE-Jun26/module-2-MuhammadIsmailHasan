from marshmallow import Schema, fields, validate


class CreatePaymentSchema(Schema):
    order_id = fields.Integer(
        required=True,
        error_messages={
            "required": "order_id is required",
            "invalid": "order_id must be a number",
        },
    )


class MidtransNotificationSchema(Schema):
    order_id = fields.String(required=True)
    status_code = fields.String(required=True)
    gross_amount = fields.String(required=True)
    signature_key = fields.String(required=True)
    transaction_status = fields.String(required=True)
    transaction_time = fields.String(load_default=None)
    settlement_time = fields.String(load_default=None)
    payment_type = fields.String(load_default=None)
    fraud_status = fields.String(load_default=None)

    class Meta:
        unknown = 'EXCLUDE'


class PaymentResponseSchema(Schema):
    id = fields.Integer()
    order_id = fields.Integer()
    payment_reference = fields.String()
    amount = fields.Float()
    status = fields.String(
        validate=validate.OneOf(['pending', 'paid', 'expired', 'failed', 'refunded'])
    )
    payment_method = fields.String(allow_none=True)
    transaction_time = fields.DateTime(format='iso', allow_none=True)
    settlement_time = fields.DateTime(format='iso', allow_none=True)
    expires_at = fields.DateTime(format='iso')
    created_at = fields.DateTime(format='iso')
    updated_at = fields.DateTime(format='iso', allow_none=True)
