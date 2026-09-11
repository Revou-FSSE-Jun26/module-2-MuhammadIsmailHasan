import hashlib
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from app.services.payment_service import (
    PaymentService,
    OrderNotFoundError,
    OrderNotPayableError,
    OrderPermissionError,
    InvalidSignatureError,
    PaymentNotFoundError,
    PaymentGatewayError,
    MidtransError,
)


SERVER_KEY = 'test-server-key'


def make_order(id=1, user_id=1, status='waiting_for_payment', is_active=True,
               total_amount=Decimal('50000'), items=None):
    return SimpleNamespace(
        id=id, user_id=user_id, status=status, is_active=is_active,
        total_amount=total_amount, items=items or [],
    )


def make_item(product_id=1, unit_price=Decimal('50000'), quantity=1, name='Item'):
    product = SimpleNamespace(name=name)
    return SimpleNamespace(
        product_id=product_id, unit_price=unit_price,
        quantity=quantity, product=product,
    )


def make_payment(id=1, order_id=1, status='pending', reference='order-1-1'):
    return SimpleNamespace(
        id=id, order_id=order_id, status=status, payment_reference=reference,
    )


def signed_payload(reference, transaction_status, gross='50000.00',
                   status_code='200', fraud_status=None):
    raw = f"{reference}{status_code}{gross}{SERVER_KEY}"
    signature = hashlib.sha512(raw.encode()).hexdigest()
    payload = {
        'order_id': reference,
        'status_code': status_code,
        'gross_amount': gross,
        'signature_key': signature,
        'transaction_status': transaction_status,
    }
    if fraud_status is not None:
        payload['fraud_status'] = fraud_status
    return payload


@pytest.fixture
def app_ctx():
    mock_app = MagicMock()
    mock_app.config = {'MIDTRANS_SERVER_KEY': SERVER_KEY, 'MIDTRANS_EXPIRY_MINUTES': 1440}
    with patch('app.services.payment_service.current_app', new=mock_app):
        yield mock_app


@pytest.fixture
def payment_repo():
    with patch('app.services.payment_service.PaymentRepository') as mock_repo:
        yield mock_repo


@pytest.fixture
def order_repo():
    with patch('app.services.payment_service.OrderRepository') as mock_repo:
        yield mock_repo


@pytest.fixture
def gateway():
    with patch('app.services.payment_service.create_snap_transaction') as mock_call:
        mock_call.return_value = {'token': 'tok', 'redirect_url': 'https://snap/tok'}
        yield mock_call


@pytest.fixture
def db_session():
    with patch('app.services.payment_service.db') as mock_db:
        yield mock_db


class TestResolvePaymentStatus:

    def test_settlement_is_paid(self):
        assert PaymentService.resolve_payment_status('settlement') == 'paid'

    def test_capture_with_accept_is_paid(self):
        assert PaymentService.resolve_payment_status('capture', 'accept') == 'paid'

    def test_capture_with_challenge_is_pending(self):
        assert PaymentService.resolve_payment_status('capture', 'challenge') == 'pending'

    def test_expire_is_expired(self):
        assert PaymentService.resolve_payment_status('expire') == 'expired'

    def test_deny_is_failed(self):
        assert PaymentService.resolve_payment_status('deny') == 'failed'

    def test_refund_is_refunded(self):
        assert PaymentService.resolve_payment_status('refund') == 'refunded'

    def test_unknown_is_none(self):
        assert PaymentService.resolve_payment_status('something_new') is None


class TestVerifySignature:

    def test_valid_signature_passes(self, app_ctx):
        raw = f"order-1-1200{'50000.00'}{SERVER_KEY}"
        sig = hashlib.sha512(raw.encode()).hexdigest()
        assert PaymentService.verify_signature('order-1-1', '200', '50000.00', sig) is True

    def test_wrong_signature_raises(self, app_ctx):
        with pytest.raises(InvalidSignatureError):
            PaymentService.verify_signature('order-1-1', '200', '50000.00', 'deadbeef')

    def test_missing_signature_raises(self, app_ctx):
        with pytest.raises(InvalidSignatureError):
            PaymentService.verify_signature('order-1-1', '200', '50000.00', None)

    def test_tampered_amount_raises(self, app_ctx):
        raw = f"order-1-1200{'50000.00'}{SERVER_KEY}"
        sig = hashlib.sha512(raw.encode()).hexdigest()
        with pytest.raises(InvalidSignatureError):
            PaymentService.verify_signature('order-1-1', '200', '99999.00', sig)


class TestCreatePayment:

    def test_create_success_returns_payment_and_snap(self, app_ctx, payment_repo, order_repo, gateway):
        order = make_order(items=[make_item()])
        order_repo.get_by_id.return_value = order
        payment_repo.get_latest_for_order.return_value = None
        payment_repo.create.return_value = make_payment()

        with patch('app.services.payment_service.User') as user_cls:
            user_cls.query.get.return_value = SimpleNamespace(username='buyer', email='b@test.com')
            payment, snap = PaymentService.create_payment(order_id=1, user_id=1)

        assert snap['redirect_url'] == 'https://snap/tok'
        assert gateway.called

    def test_reference_sent_to_gateway_matches_created(self, app_ctx, payment_repo, order_repo, gateway):
        order = make_order(items=[make_item()])
        order_repo.get_by_id.return_value = order
        payment_repo.get_latest_for_order.return_value = None
        payment_repo.create.return_value = make_payment(reference='order-1-1')

        with patch('app.services.payment_service.User') as user_cls:
            user_cls.query.get.return_value = SimpleNamespace(username='buyer', email='b@test.com')
            PaymentService.create_payment(order_id=1, user_id=1)

        assert gateway.call_args.kwargs['payment_reference'] == 'order-1-1'

    def test_gross_amount_matches_item_sum(self, app_ctx, payment_repo, order_repo, gateway):
        items = [make_item(unit_price=Decimal('10000'), quantity=2),
                 make_item(product_id=2, unit_price=Decimal('5000'), quantity=1)]
        order = make_order(items=items, total_amount=Decimal('25000'))
        order_repo.get_by_id.return_value = order
        payment_repo.get_latest_for_order.return_value = None
        payment_repo.create.return_value = make_payment()

        with patch('app.services.payment_service.User') as user_cls:
            user_cls.query.get.return_value = SimpleNamespace(username='buyer', email='b@test.com')
            PaymentService.create_payment(order_id=1, user_id=1)

        assert gateway.call_args.kwargs['gross_amount'] == 25000

    def test_retry_bumps_attempt_counter(self, app_ctx, payment_repo, order_repo, gateway):
        order = make_order(items=[make_item()])
        order_repo.get_by_id.return_value = order
        payment_repo.get_latest_for_order.return_value = make_payment(reference='order-1-1')
        payment_repo.create.return_value = make_payment(reference='order-1-2')

        with patch('app.services.payment_service.User') as user_cls:
            user_cls.query.get.return_value = SimpleNamespace(username='buyer', email='b@test.com')
            PaymentService.create_payment(order_id=1, user_id=1)

        assert gateway.call_args.kwargs['payment_reference'] == 'order-1-2'

    def test_order_not_found(self, app_ctx, payment_repo, order_repo):
        order_repo.get_by_id.return_value = None
        with pytest.raises(OrderNotFoundError):
            PaymentService.create_payment(order_id=1, user_id=1)

    def test_wrong_owner_forbidden(self, app_ctx, payment_repo, order_repo):
        order_repo.get_by_id.return_value = make_order(user_id=2)
        with pytest.raises(OrderPermissionError):
            PaymentService.create_payment(order_id=1, user_id=1)

    def test_order_not_payable(self, app_ctx, payment_repo, order_repo):
        order_repo.get_by_id.return_value = make_order(status='paid')
        with pytest.raises(OrderNotPayableError):
            PaymentService.create_payment(order_id=1, user_id=1)

    def test_gateway_failure_raises(self, app_ctx, payment_repo, order_repo, gateway):
        order = make_order(items=[make_item()])
        order_repo.get_by_id.return_value = order
        payment_repo.get_latest_for_order.return_value = None
        payment_repo.create.return_value = make_payment()
        gateway.side_effect = MidtransError('boom')

        with patch('app.services.payment_service.User') as user_cls:
            user_cls.query.get.return_value = SimpleNamespace(username='buyer', email='b@test.com')
            with pytest.raises(PaymentGatewayError):
                PaymentService.create_payment(order_id=1, user_id=1)


class TestGetById:

    def test_owner_can_get(self, payment_repo, order_repo):
        payment_repo.get_by_id.return_value = make_payment(order_id=5)
        order_repo.get_by_id.return_value = make_order(id=5, user_id=1)
        result = PaymentService.get_by_id(1, user_id=1, role='buyer')
        assert result.order_id == 5

    def test_admin_can_get_any(self, payment_repo, order_repo):
        payment_repo.get_by_id.return_value = make_payment(order_id=5)
        result = PaymentService.get_by_id(1, user_id=999, role='admin')
        assert result.order_id == 5

    def test_not_found_raises(self, payment_repo, order_repo):
        payment_repo.get_by_id.return_value = None
        with pytest.raises(PaymentNotFoundError):
            PaymentService.get_by_id(1, user_id=1, role='buyer')

    def test_non_owner_forbidden(self, payment_repo, order_repo):
        payment_repo.get_by_id.return_value = make_payment(order_id=5)
        order_repo.get_by_id.return_value = make_order(id=5, user_id=2)
        with pytest.raises(OrderPermissionError):
            PaymentService.get_by_id(1, user_id=1, role='buyer')


class TestHandleNotification:

    def test_bad_signature_raises(self, app_ctx, payment_repo, order_repo, db_session):
        payload = signed_payload('order-1-1', 'settlement')
        payload['signature_key'] = 'forged'
        with pytest.raises(InvalidSignatureError):
            PaymentService.handle_notification(payload)

    def test_unknown_reference_raises(self, app_ctx, payment_repo, order_repo, db_session):
        payment_repo.get_by_reference.return_value = None
        with pytest.raises(PaymentNotFoundError):
            PaymentService.handle_notification(signed_payload('order-1-1', 'settlement'))

    def test_settlement_marks_paid_and_order_paid(self, app_ctx, payment_repo, order_repo, db_session):
        payment = make_payment(status='pending')
        payment_repo.get_by_reference.return_value = payment
        order = make_order(status='waiting_for_payment')
        order_repo.get_by_id.return_value = order

        PaymentService.handle_notification(signed_payload('order-1-1', 'settlement'))

        assert payment_repo.update_from_notification.call_args.kwargs['new_status'] == 'paid'
        assert order.status == 'paid'

    def test_expire_cancels_and_restocks_order(self, app_ctx, payment_repo, order_repo, db_session):
        payment = make_payment(status='pending')
        payment_repo.get_by_reference.return_value = payment
        item = make_item(quantity=3)
        order = make_order(status='waiting_for_payment', items=[item])
        order_repo.get_by_id.return_value = order

        with patch('app.services.payment_service.Product') as product_cls:
            product = SimpleNamespace(stock=10)
            product_cls.query.get.return_value = product
            PaymentService.handle_notification(signed_payload('order-1-1', 'expire'))

        assert order.status == 'cancelled'
        assert product.stock == 13

    def test_failed_attempt_keeps_order_waiting(self, app_ctx, payment_repo, order_repo, db_session):
        payment = make_payment(status='pending')
        payment_repo.get_by_reference.return_value = payment
        order = make_order(status='waiting_for_payment')
        order_repo.get_by_id.return_value = order

        PaymentService.handle_notification(signed_payload('order-1-1', 'deny'))

        assert payment_repo.update_from_notification.call_args.kwargs['new_status'] == 'failed'
        assert order.status == 'waiting_for_payment'

    def test_duplicate_same_status_ignored(self, app_ctx, payment_repo, order_repo, db_session):
        payment = make_payment(status='paid')
        payment_repo.get_by_reference.return_value = payment

        PaymentService.handle_notification(signed_payload('order-1-1', 'settlement'))

        assert not payment_repo.update_from_notification.called

    def test_late_deny_after_paid_ignored(self, app_ctx, payment_repo, order_repo, db_session):
        payment = make_payment(status='paid')
        payment_repo.get_by_reference.return_value = payment

        PaymentService.handle_notification(signed_payload('order-1-1', 'deny'))

        assert not payment_repo.update_from_notification.called

    def test_refund_after_paid_allowed(self, app_ctx, payment_repo, order_repo, db_session):
        payment = make_payment(status='paid')
        payment_repo.get_by_reference.return_value = payment
        order = make_order(status='paid', items=[make_item(quantity=1)])
        order_repo.get_by_id.return_value = order

        with patch('app.services.payment_service.Product') as product_cls:
            product_cls.query.get.return_value = SimpleNamespace(stock=5)
            PaymentService.handle_notification(signed_payload('order-1-1', 'refund'))

        assert payment_repo.update_from_notification.call_args.kwargs['new_status'] == 'refunded'
        assert order.status == 'cancelled'

    def test_refunded_is_terminal(self, app_ctx, payment_repo, order_repo, db_session):
        payment = make_payment(status='refunded')
        payment_repo.get_by_reference.return_value = payment

        PaymentService.handle_notification(signed_payload('order-1-1', 'deny'))

        assert not payment_repo.update_from_notification.called

    def test_unknown_status_leaves_untouched(self, app_ctx, payment_repo, order_repo, db_session):
        payment = make_payment(status='pending')
        payment_repo.get_by_reference.return_value = payment

        PaymentService.handle_notification(signed_payload('order-1-1', 'weird_status'))

        assert not payment_repo.update_from_notification.called
