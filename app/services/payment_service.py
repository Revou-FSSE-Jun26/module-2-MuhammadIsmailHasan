import hashlib
from datetime import timedelta

from flask import current_app

from app.extensions import db
from app.repositories.payment_repository import PaymentRepository
from app.repositories.order_repository import OrderRepository
from app.models.products import Product
from app.models.users import User
from app.utils.timezone import utcnow
from app.integrations.midtrans import create_snap_transaction, MidtransError
from app.validation import (
    MIDTRANS_STATUS_TO_PAYMENT_STATUS,
    PAYMENT_STATUS_TO_ORDER_STATUS,
)


class OrderNotFoundError(Exception):
    pass


class OrderNotPayableError(Exception):
    pass


class OrderPermissionError(Exception):
    pass


class InvalidSignatureError(Exception):
    pass


class PaymentNotFoundError(Exception):
    pass


class PaymentGatewayError(Exception):
    pass


class PaymentService:

    @staticmethod
    def create_payment(order_id, user_id):
        order = OrderRepository.get_by_id(order_id)
        if not order or not order.is_active:
            raise OrderNotFoundError("order not found")

        if order.user_id != user_id:
            raise OrderPermissionError(
                "you don't have permission to pay for this order"
            )

        if order.status != 'waiting_for_payment':
            raise OrderNotPayableError(
                f"order is '{order.status}' and cannot be paid"
            )

        attempt = 1
        latest = PaymentRepository.get_latest_for_order(order_id)
        if latest and latest.payment_reference:
            try:
                attempt = int(latest.payment_reference.rsplit('-', 1)[1]) + 1
            except (ValueError, IndexError):
                attempt = 1
        payment_reference = f"order-{order_id}-{attempt}"

        expiry_minutes = current_app.config.get('MIDTRANS_EXPIRY_MINUTES', 1440)
        expires_at = utcnow() + timedelta(minutes=expiry_minutes)

        payment = PaymentRepository.create(
            order_id=order_id,
            payment_reference=payment_reference,
            amount=order.total_amount,
            expires_at=expires_at,
        )

        current_app.logger.info(
            'payment %s created for order %s (ref=%s)',
            payment.id, order_id, payment_reference,
        )

        buyer = User.query.get(order.user_id)
        customer = {
            'first_name': buyer.username if buyer else 'customer',
            'email': buyer.email if buyer else None,
        }

        item_details = [
            {
                'id': str(item.product_id),
                'price': int(round(item.unit_price)),
                'quantity': item.quantity,
                'name': (item.product.name[:50] if item.product else 'item'),
            }
            for item in order.items
        ]

        gross_amount = sum(i['price'] * i['quantity'] for i in item_details)

        try:
            snap = create_snap_transaction(
                payment_reference=payment_reference,
                gross_amount=gross_amount,
                customer=customer,
                item_details=item_details,
                expiry_minutes=expiry_minutes,
            )
        except MidtransError as exc:
            current_app.logger.error(
                'midtrans create failed for payment %s: %s', payment.id, exc
            )
            raise PaymentGatewayError(str(exc))

        return payment, snap

    @staticmethod
    def verify_signature(order_id, status_code, gross_amount, signature_key):
        server_key = current_app.config.get('MIDTRANS_SERVER_KEY', '')

        raw = f"{order_id}{status_code}{gross_amount}{server_key}"
        expected = hashlib.sha512(raw.encode('utf-8')).hexdigest()

        if not signature_key or not _constant_time_equals(expected, signature_key):
            raise InvalidSignatureError("invalid signature")

        return True

    @staticmethod
    def resolve_payment_status(transaction_status, fraud_status=None):
        if transaction_status == 'capture':
            if fraud_status == 'accept':
                return 'paid'
            return 'pending'

        return MIDTRANS_STATUS_TO_PAYMENT_STATUS.get(transaction_status)

    @staticmethod
    def handle_notification(payload):
        order_ref = payload.get('order_id')
        status_code = payload.get('status_code')
        gross_amount = payload.get('gross_amount')
        signature_key = payload.get('signature_key')
        transaction_status = payload.get('transaction_status')

        PaymentService.verify_signature(
            order_ref, status_code, gross_amount, signature_key
        )

        payment = PaymentRepository.get_by_reference(order_ref)
        if not payment:
            raise PaymentNotFoundError(
                f"no payment found for reference {order_ref}"
            )

        fraud_status = payload.get('fraud_status')
        new_payment_status = PaymentService.resolve_payment_status(
            transaction_status, fraud_status
        )
        if new_payment_status is None:
            current_app.logger.warning(
                'unhandled midtrans transaction_status=%r fraud_status=%r '
                'for payment %s; leaving status unchanged',
                transaction_status, fraud_status, payment.id,
            )
            return payment

        if payment.status == new_payment_status:
            current_app.logger.info(
                'payment %s already in status %s, ignoring duplicate',
                payment.id, new_payment_status,
            )
            return payment

        if payment.status == 'refunded':
            current_app.logger.warning(
                'ignoring %s webhook for refunded payment %s',
                new_payment_status, payment.id,
            )
            return payment

        if payment.status == 'paid' and new_payment_status != 'refunded':
            current_app.logger.warning(
                'ignoring %s webhook for already-paid payment %s',
                new_payment_status, payment.id,
            )
            return payment

        PaymentRepository.update_from_notification(
            payment,
            new_status=new_payment_status,
            payment_method=payload.get('payment_type'),
            transaction_time=_parse_dt(payload.get('transaction_time')),
            settlement_time=_parse_dt(payload.get('settlement_time')),
            raw_response=str(payload),
            commit=False,
        )

        target_order_status = PAYMENT_STATUS_TO_ORDER_STATUS.get(new_payment_status)
        if target_order_status:
            PaymentService._apply_order_status(
                payment.order_id, target_order_status, new_payment_status
            )

        db.session.commit()

        current_app.logger.info(
            'payment %s -> %s, order %s reacted',
            payment.id, new_payment_status, payment.order_id,
        )
        return payment

    @staticmethod
    def _apply_order_status(order_id, target_status, payment_status):
        order = OrderRepository.get_by_id(order_id)
        if not order:
            return

        if target_status == 'cancelled':
            if payment_status == 'expired':
                if order.status != 'waiting_for_payment':
                    current_app.logger.warning(
                        'refusing to cancel order %s from status %s (%s)',
                        order_id, order.status, payment_status,
                    )
                    return
            elif payment_status == 'refunded':
                if order.status not in ('paid', 'processing'):
                    current_app.logger.warning(
                        'refusing to cancel order %s from status %s on refund',
                        order_id, order.status,
                    )
                    return

        if target_status == 'paid' and order.status != 'waiting_for_payment':
            return

        order.status = target_status

        if target_status == 'cancelled':
            for item in order.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock += item.quantity


def _constant_time_equals(a, b):
    import hmac
    return hmac.compare_digest(a, b)


def _parse_dt(value):
    if not value:
        return None
    from datetime import datetime
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None
