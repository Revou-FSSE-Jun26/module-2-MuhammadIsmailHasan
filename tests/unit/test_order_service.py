from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from app.services.order_service import (
    OrderService,
    OrderNotFoundError,
    OrderPermissionError,
    ProductNotFoundError,
    InsufficientStockError,
    InvalidStatusTransitionError,
    OrderCannotBeDeletedError,
    ShippingAddressRequiredError,
    AddressNotFoundError,
    AddressChangeNotAllowedError,
    TrackingIdRequiredError,
)


def make_product(id=1, name='Laptop', price=Decimal('100.00'), stock=10):
    return SimpleNamespace(id=id, name=name, price=price, stock=stock)


def make_order(id=1, user_id=1, status='waiting_for_payment', is_active=True, items=None):
    return SimpleNamespace(
        id=id, user_id=user_id, status=status,
        is_active=is_active, items=items or [],
    )


def make_address(recipient_name='Buyer', phone='123', address_line='Jl. A',
                 city='Jakarta', postal_code='10110'):
    return SimpleNamespace(
        recipient_name=recipient_name, phone=phone,
        address_line=address_line, city=city, postal_code=postal_code,
    )


@pytest.fixture
def repo():
    with patch('app.services.order_service.OrderRepository') as mock_repo:
        yield mock_repo


@pytest.fixture
def address_repo():
    with patch('app.services.order_service.UserAddressRepository') as mock_repo:
        mock_repo.get_default.return_value = make_address()
        mock_repo.get.return_value = make_address()
        yield mock_repo


class TestCreate:

    def test_create_success_calculates_totals(self, repo, address_repo):
        product = make_product(id=5, price=Decimal('100.00'), stock=10)
        repo.get_product_by_id.return_value = product
        repo.create.return_value = make_order(id=99)

        data = {'items': [{'product_id': 5, 'quantity': 3}]}
        result = OrderService.create(user_id=1, data=data)

        assert result.id == 99
        called_user_id, called_items = repo.create.call_args[0][:2]
        assert called_user_id == 1
        assert len(called_items) == 1
        item = called_items[0]
        assert item['product_id'] == 5
        assert item['quantity'] == 3
        assert item['unit_price'] == Decimal('100.00')
        assert item['sub_total'] == Decimal('300.00')

    def test_create_multiple_items(self, repo, address_repo):
        p1 = make_product(id=1, price=Decimal('10.00'), stock=100)
        p2 = make_product(id=2, price=Decimal('5.00'), stock=100)
        repo.get_product_by_id.side_effect = lambda pid: {1: p1, 2: p2}[pid]
        repo.create.return_value = make_order()

        data = {'items': [
            {'product_id': 1, 'quantity': 2},
            {'product_id': 2, 'quantity': 4},
        ]}
        OrderService.create(user_id=7, data=data)

        called_items = repo.create.call_args[0][1]
        assert called_items[0]['sub_total'] == Decimal('20.00')
        assert called_items[1]['sub_total'] == Decimal('20.00')

    def test_create_product_not_found(self, repo, address_repo):
        repo.get_product_by_id.return_value = None

        with pytest.raises(ProductNotFoundError) as exc:
            OrderService.create(user_id=1, data={'items': [{'product_id': 999, 'quantity': 1}]})
        assert 'product with id 999 not found' in str(exc.value)
        repo.create.assert_not_called()

    def test_create_insufficient_stock(self, repo, address_repo):
        repo.get_product_by_id.return_value = make_product(stock=2)

        with pytest.raises(InsufficientStockError) as exc:
            OrderService.create(user_id=1, data={'items': [{'product_id': 1, 'quantity': 5}]})
        assert 'insufficient stock' in str(exc.value)
        repo.create.assert_not_called()

    def test_create_stock_exactly_equal_is_allowed(self, repo, address_repo):
        repo.get_product_by_id.return_value = make_product(stock=5)
        repo.create.return_value = make_order()

        OrderService.create(user_id=1, data={'items': [{'product_id': 1, 'quantity': 5}]})
        repo.create.assert_called_once()


class TestGetById:

    def test_get_success_owner(self, repo):
        repo.get_by_id.return_value = make_order(id=3, user_id=1)
        result = OrderService.get_by_id(3, user_id=1, role='buyer')
        assert result.id == 3

    def test_get_admin_can_view_any(self, repo):
        repo.get_by_id.return_value = make_order(id=3, user_id=999)
        result = OrderService.get_by_id(3, user_id=1, role='admin')
        assert result.id == 3

    def test_get_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(OrderNotFoundError):
            OrderService.get_by_id(3, user_id=1, role='buyer')

    def test_get_other_user_forbidden(self, repo):
        repo.get_by_id.return_value = make_order(id=3, user_id=2)
        with pytest.raises(OrderPermissionError):
            OrderService.get_by_id(3, user_id=1, role='buyer')

    def test_get_seller_can_view_order_with_their_product(self, repo):
        repo.get_by_id.return_value = make_order(id=3, user_id=999)
        repo.order_has_seller_product.return_value = True

        result = OrderService.get_by_id(3, user_id=7, role='seller')

        assert result.id == 3
        repo.order_has_seller_product.assert_called_once_with(3, 7)

    def test_get_seller_without_product_forbidden(self, repo):
        repo.get_by_id.return_value = make_order(id=3, user_id=999)
        repo.order_has_seller_product.return_value = False

        with pytest.raises(OrderPermissionError):
            OrderService.get_by_id(3, user_id=7, role='seller')


class TestGetAll:

    def test_admin_queries_without_user_filter(self, repo):
        OrderService.get_all(user_id=1, role='admin', filters={}, page=1, limit=10)
        kwargs = repo.get_all.call_args.kwargs
        assert kwargs['user_id'] is None
        assert kwargs['seller_id'] is None

    def test_buyer_scoped_to_own_orders(self, repo):
        OrderService.get_all(user_id=1, role='buyer', filters={}, page=1, limit=10)
        kwargs = repo.get_all.call_args.kwargs
        assert kwargs['user_id'] == 1
        assert kwargs['seller_id'] is None

    def test_seller_scoped_by_seller_id(self, repo):
        OrderService.get_all(user_id=7, role='seller', filters={}, page=1, limit=10)
        kwargs = repo.get_all.call_args.kwargs
        assert kwargs['seller_id'] == 7
        assert kwargs['user_id'] is None


class TestUpdateStatus:

    def test_buyer_cannot_advance_fulfillment(self, repo):
        order = make_order(status='waiting_for_payment', user_id=1)
        repo.get_by_id.return_value = order
        with pytest.raises(OrderPermissionError):
            OrderService.update_status(1, {'status': 'processing'}, user_id=1, role='buyer')
        repo.update_status.assert_not_called()

    def test_seller_valid_transition_stamps_updated_by(self, repo):
        order = make_order(status='paid', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True
        repo.update_status.return_value = order

        OrderService.update_status(1, {'status': 'processing'}, user_id=7, role='seller')

        repo.order_has_seller_product.assert_called_once_with(order.id, 7)
        repo.update_status.assert_called_once_with(
            order, 'processing', updated_by=7, tracking_id=None, restock=False
        )

    def test_seller_confirms_payment(self, repo):
        order = make_order(status='waiting_for_payment', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True
        repo.update_status.return_value = order

        OrderService.update_status(1, {'status': 'paid'}, user_id=7, role='seller')
        repo.update_status.assert_called_once_with(
            order, 'paid', updated_by=7, tracking_id=None, restock=False
        )

    def test_seller_advances_shipped_to_delivered(self, repo):
        order = make_order(status='shipped', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True
        repo.update_status.return_value = order

        OrderService.update_status(1, {'status': 'delivered'}, user_id=7, role='seller')
        repo.update_status.assert_called_once_with(
            order, 'delivered', updated_by=7, tracking_id=None, restock=False
        )

    def test_seller_can_cancel_via_update_and_restocks(self, repo):
        order = make_order(status='processing', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True
        repo.update_status.return_value = order

        _, refund_note = OrderService.update_status(
            1, {'status': 'cancelled'}, user_id=7, role='seller'
        )

        assert refund_note == 'payment refund will be processed'
        repo.update_status.assert_called_once_with(
            order, 'cancelled', updated_by=7, tracking_id=None, restock=True
        )

    def test_buyer_can_cancel_own_waiting_order_no_refund_note(self, repo):
        order = make_order(status='waiting_for_payment', user_id=1)
        repo.get_by_id.return_value = order
        repo.update_status.return_value = order

        _, refund_note = OrderService.update_status(
            1, {'status': 'cancelled'}, user_id=1, role='buyer'
        )

        assert refund_note is None
        repo.update_status.assert_called_once_with(
            order, 'cancelled', updated_by=1, tracking_id=None, restock=True
        )

    def test_buyer_returns_delivered_order_restocks(self, repo):
        order = make_order(status='delivered', user_id=1)
        repo.get_by_id.return_value = order
        repo.update_status.return_value = order

        _, refund_note = OrderService.update_status(
            1, {'status': 'returned'}, user_id=1, role='buyer'
        )

        assert refund_note is None
        repo.update_status.assert_called_once_with(
            order, 'returned', updated_by=1, tracking_id=None, restock=True
        )

    def test_seller_forbidden_when_no_owned_product(self, repo):
        order = make_order(status='waiting_for_payment', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = False

        with pytest.raises(OrderPermissionError):
            OrderService.update_status(1, {'status': 'processing'}, user_id=7, role='seller')
        repo.update_status.assert_not_called()

    def test_admin_valid_transition(self, repo):
        order = make_order(status='waiting_for_payment', user_id=99)
        repo.get_by_id.return_value = order
        repo.update_status.return_value = order

        OrderService.update_status(1, {'status': 'paid'}, user_id=1, role='admin')
        repo.update_status.assert_called_once_with(
            order, 'paid', updated_by=1, tracking_id=None, restock=False
        )

    def test_not_found(self, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(OrderNotFoundError):
            OrderService.update_status(1, {'status': 'processing'}, user_id=1, role='admin')

    def test_cancelled_order_cannot_be_modified(self, repo):
        repo.get_by_id.return_value = make_order(status='cancelled', is_active=False, user_id=1)
        with pytest.raises(InvalidStatusTransitionError):
            OrderService.update_status(1, {'status': 'processing'}, user_id=1, role='admin')
        repo.update_status.assert_not_called()

    def test_skip_step_rejected(self, repo):
        repo.get_by_id.return_value = make_order(status='waiting_for_payment', user_id=1)
        with pytest.raises(InvalidStatusTransitionError):
            OrderService.update_status(1, {'status': 'shipped'}, user_id=1, role='admin')

    def test_delivered_cannot_go_backwards(self, repo):
        repo.get_by_id.return_value = make_order(status='delivered', user_id=1)
        with pytest.raises(InvalidStatusTransitionError):
            OrderService.update_status(1, {'status': 'processing'}, user_id=1, role='admin')

    def test_returned_is_terminal(self, repo):
        repo.get_by_id.return_value = make_order(status='returned', user_id=1)
        with pytest.raises(InvalidStatusTransitionError):
            OrderService.update_status(1, {'status': 'processing'}, user_id=1, role='admin')
        repo.update_status.assert_not_called()

    def test_shipping_requires_tracking_id(self, repo):
        order = make_order(status='processing', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True

        with pytest.raises(TrackingIdRequiredError):
            OrderService.update_status(1, {'status': 'shipped'}, user_id=7, role='seller')
        repo.update_status.assert_not_called()

    def test_shipping_with_tracking_id_persists_it(self, repo):
        order = make_order(status='processing', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True
        repo.update_status.return_value = order

        OrderService.update_status(
            1, {'status': 'shipped', 'tracking_id': 'JNE-123'}, user_id=7, role='seller'
        )
        repo.update_status.assert_called_once_with(
            order, 'shipped', updated_by=7, tracking_id='JNE-123', restock=False
        )

    def test_shipping_with_empty_tracking_id_rejected(self, repo):
        order = make_order(status='processing', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True

        with pytest.raises(TrackingIdRequiredError):
            OrderService.update_status(
                1, {'status': 'shipped', 'tracking_id': ''}, user_id=7, role='seller'
            )
        repo.update_status.assert_not_called()

    def test_admin_can_ship_with_tracking_id(self, repo):
        order = make_order(status='processing', user_id=99)
        repo.get_by_id.return_value = order
        repo.update_status.return_value = order

        OrderService.update_status(
            1, {'status': 'shipped', 'tracking_id': 'SICEPAT-9'}, user_id=1, role='admin'
        )
        repo.update_status.assert_called_once_with(
            order, 'shipped', updated_by=1, tracking_id='SICEPAT-9', restock=False
        )

    def test_tracking_id_ignored_on_non_shipped_transition(self, repo):
        order = make_order(status='paid', user_id=99)
        repo.get_by_id.return_value = order
        repo.update_status.return_value = order

        OrderService.update_status(
            1, {'status': 'processing', 'tracking_id': 'IGNORED'}, user_id=1, role='admin'
        )
        repo.update_status.assert_called_once_with(
            order, 'processing', updated_by=1, tracking_id=None, restock=False
        )


class TestDelete:

    def test_not_found(self, repo):
        repo.get_active_by_id.return_value = None
        with pytest.raises(OrderNotFoundError):
            OrderService.delete(1, user_id=1, role='buyer')

    def test_buyer_forbidden_other_user(self, repo):
        repo.get_active_by_id.return_value = make_order(user_id=2)
        with pytest.raises(OrderPermissionError):
            OrderService.delete(1, user_id=1, role='buyer')
        repo.delete_order.assert_not_called()

    def test_seller_forbidden_when_no_owned_product(self, repo):
        repo.get_active_by_id.return_value = make_order(user_id=999)
        repo.order_has_seller_product.return_value = False
        with pytest.raises(OrderPermissionError):
            OrderService.delete(1, user_id=7, role='seller')
        repo.delete_order.assert_not_called()

    def test_shipped_cannot_be_deleted(self, repo):
        repo.get_active_by_id.return_value = make_order(status='shipped', user_id=1)
        with pytest.raises(OrderCannotBeDeletedError):
            OrderService.delete(1, user_id=1, role='buyer')
        repo.delete_order.assert_not_called()

    def test_delivered_can_be_deleted(self, repo):
        order = make_order(status='delivered', user_id=1)
        repo.get_active_by_id.return_value = order

        result = OrderService.delete(1, user_id=1, role='buyer')

        assert result is order
        repo.delete_order.assert_called_once_with(order, updated_by=1)

    def test_cancelled_can_be_deleted(self, repo):
        order = make_order(status='cancelled', user_id=1)
        repo.get_active_by_id.return_value = order

        OrderService.delete(1, user_id=1, role='buyer')
        repo.delete_order.assert_called_once_with(order, updated_by=1)

    def test_admin_can_delete_other_users_order(self, repo):
        order = make_order(status='cancelled', user_id=999)
        repo.get_active_by_id.return_value = order

        OrderService.delete(1, user_id=1, role='admin')
        repo.delete_order.assert_called_once_with(order, updated_by=1)


class TestResolveShippingAddress:

    def test_uses_default_when_no_address_id(self, address_repo):
        address_repo.get_default.return_value = make_address(city='Jakarta')

        shipping = OrderService._resolve_shipping_address(1)

        address_repo.get_default.assert_called_once_with(1)
        assert shipping['shipping_city'] == 'Jakarta'

    def test_uses_given_address_id(self, address_repo):
        address_repo.get.return_value = make_address(city='Bandung')

        shipping = OrderService._resolve_shipping_address(1, address_id=5)

        address_repo.get.assert_called_once_with(1, 5)
        assert shipping['shipping_city'] == 'Bandung'

    def test_no_default_raises_required(self, address_repo):
        address_repo.get_default.return_value = None

        with pytest.raises(ShippingAddressRequiredError):
            OrderService._resolve_shipping_address(1)

    def test_unknown_address_id_raises_not_found(self, address_repo):
        address_repo.get.return_value = None

        with pytest.raises(AddressNotFoundError):
            OrderService._resolve_shipping_address(1, address_id=99)


class TestChangeAddress:

    def test_change_while_waiting(self, repo, address_repo):
        order = make_order(id=3, user_id=1, status='waiting_for_payment')
        repo.get_by_id.return_value = order
        address_repo.get.return_value = make_address(city='Bandung')
        repo.update_shipping.return_value = order

        OrderService.change_address(3, address_id=5, user_id=1)

        repo.update_shipping.assert_called_once()
        shipping = repo.update_shipping.call_args[0][1]
        assert shipping['shipping_city'] == 'Bandung'

    def test_change_blocked_when_processing(self, repo, address_repo):
        order = make_order(id=3, user_id=1, status='processing')
        repo.get_by_id.return_value = order

        with pytest.raises(AddressChangeNotAllowedError):
            OrderService.change_address(3, address_id=5, user_id=1)
        repo.update_shipping.assert_not_called()

    def test_change_not_owner(self, repo, address_repo):
        order = make_order(id=3, user_id=2, status='waiting_for_payment')
        repo.get_by_id.return_value = order

        with pytest.raises(OrderPermissionError):
            OrderService.change_address(3, address_id=5, user_id=1)
        repo.update_shipping.assert_not_called()

    def test_change_order_not_found(self, repo, address_repo):
        repo.get_by_id.return_value = None

        with pytest.raises(OrderNotFoundError):
            OrderService.change_address(3, address_id=5, user_id=1)
