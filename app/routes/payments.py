from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import current_app, request

from app.schemas.payment_schema import (
    CreatePaymentSchema,
    MidtransNotificationSchema,
    PaymentResponseSchema,
)
from app.services.payment_service import (
    PaymentService,
    OrderNotFoundError,
    OrderNotPayableError,
    OrderPermissionError,
    InvalidSignatureError,
    PaymentNotFoundError,
    PaymentGatewayError,
)
from app.auth import roles_required
from app.utils.auth_context import current_user_id
from app.utils.http import make_response

payments_blp = Blueprint(
    'payments',
    __name__,
    url_prefix='/api/v1/payments',
    description='Payment operations',
)


@payments_blp.route('/')
class PaymentCreate(MethodView):

    @payments_blp.arguments(CreatePaymentSchema)
    @roles_required('buyer')
    def post(self, validated_data):
        user_id = current_user_id()

        try:
            payment, snap = PaymentService.create_payment(
                validated_data['order_id'], user_id
            )
        except OrderNotFoundError as e:
            abort(404, message=str(e))
        except OrderPermissionError as e:
            abort(403, message=str(e))
        except OrderNotPayableError as e:
            abort(409, message=str(e))
        except PaymentGatewayError as e:
            abort(502, message=str(e))

        data = PaymentResponseSchema().dump(payment)
        data['snap_token'] = snap['token']
        data['redirect_url'] = snap['redirect_url']

        return make_response('payment created', data, 201)


@payments_blp.route('/webhook/midtrans')
class MidtransWebhook(MethodView):

    def post(self):
        payload = request.get_json(silent=True)
        if not payload:
            abort(400, message="invalid or missing JSON body")

        errors = MidtransNotificationSchema().validate(payload)
        if errors:
            current_app.logger.warning('malformed midtrans payload: %s', errors)
            abort(400, message="malformed notification payload")

        try:
            PaymentService.handle_notification(payload)
        except InvalidSignatureError as e:
            current_app.logger.warning('rejected webhook: %s', str(e))
            abort(403, message="invalid signature")
        except PaymentNotFoundError as e:
            abort(404, message=str(e))

        return make_response('notification processed')
