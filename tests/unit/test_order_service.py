"""
Unit tests for OrderService.

These are pure unit tests: OrderRepository is mocked so the service's
business logic (stock checks, price calculation, ownership, status
transitions, refund rules) is exercised in isolation, with no database.
"""

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
)


def make_product(id=1, name='Laptop', price=Decimal('100.00'), stock=10):
    return SimpleNamespace(id=id, name=name, price=price, stock=stock)


def make_order(id=1, user_id=1, status='waiting_for_payment', is_active=True, items=None):
    return SimpleNamespace(
        id=id, user_id=user_id, status=status,
        is_active=is_active, items=items or [],
    )


@pytest.fixture
def repo():
    with patch('app.services.order_service.OrderRepository') as mock_repo:
        yield mock_repo


class TestCreate:

    def test_create_success_calculates_totals(self, repo):
        product = make_product(id=5, price=Decimal('100.00'), stock=10)
        repo.get_product_by_id.return_value = product
        repo.create.return_value = make_order(id=99)

        data = {'items': [{'product_id': 5, 'quantity': 3}]}
        result = OrderService.create(user_id=1, data=data)

        assert result.id == 99
        # repo.create called with computed items
        called_user_id, called_items = repo.create.call_args[0]
        assert called_user_id == 1
        assert len(called_items) == 1
        item = called_items[0]
        assert item['product_id'] == 5
        assert item['quantity'] == 3
        assert item['unit_price'] == Decimal('100.00')
        assert item['sub_total'] == Decimal('300.00')

    def test_create_multiple_items(self, repo):
        p1 = make_product(id=1, price=Decimal('10.00'), stock=100)
        p2 = make_product(id=2, price=Decimal('5.00'), stock=100)
        repo.get_product_by_id.side_effect = lambda pid: {1: p1, 2: p2}[pid]
        repo.create.return_value = make_order()

        data = {'items': [
            {'product_id': 1, 'quantity': 2},
            {'product_id': 2, 'quantity': 4},
        ]}
        OrderService.create(user_id=7, data=data)

        _, called_items = repo.create.call_args[0]
        assert called_items[0]['sub_total'] == Decimal('20.00')
        assert called_items[1]['sub_total'] == Decimal('20.00')

    def test_create_product_not_found(self, repo):
        repo.get_product_by_id.return_value = None

        with pytest.raises(ProductNotFoundError) as exc:
            OrderService.create(user_id=1, data={'items': [{'product_id': 999, 'quantity': 1}]})
        assert 'product with id 999 not found' in str(exc.value)
        repo.create.assert_not_called()

    def test_create_insufficient_stock(self, repo):
        repo.get_product_by_id.return_value = make_product(stock=2)

        with pytest.raises(InsufficientStockError) as exc:
            OrderService.create(user_id=1, data={'items': [{'product_id': 1, 'quantity': 5}]})
        assert 'insufficient stock' in str(exc.value)
        repo.create.assert_not_called()

    def test_create_stock_exactly_equal_is_allowed(self, repo):
        repo.get_product_by_id.return_value = make_product(stock=5)
        repo.create.return_value = make_order()

        # requesting exactly the available stock should NOT raise
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

    def test_buyer_cannot_update_status(self, repo):
        repo.get_by_id.return_value = make_order(status='waiting_for_payment', user_id=1)
        with pytest.raises(OrderPermissionError):
            OrderService.update_status(1, {'status': 'processing'}, user_id=1, role='buyer')
        repo.update_status.assert_not_called()

    def test_seller_valid_transition_stamps_updated_by(self, repo):
        order = make_order(status='waiting_for_payment', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True
        repo.update_status.return_value = order

        OrderService.update_status(1, {'status': 'processing'}, user_id=7, role='seller')

        repo.order_has_seller_product.assert_called_once_with(order.id, 7)
        repo.update_status.assert_called_once_with(order, 'processing', updated_by=7)

    def test_seller_advances_shipped_to_delivered(self, repo):
        order = make_order(status='shipped', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True
        repo.update_status.return_value = order

        OrderService.update_status(1, {'status': 'delivered'}, user_id=7, role='seller')
        repo.update_status.assert_called_once_with(order, 'delivered', updated_by=7)

    def test_seller_cannot_set_cancelled_via_update(self, repo):
        order = make_order(status='processing', user_id=99)
        repo.get_by_id.return_value = order
        repo.order_has_seller_product.return_value = True

        with pytest.raises(OrderPermissionError):
            OrderService.update_status(1, {'status': 'cancelled'}, user_id=7, role='seller')
        repo.update_status.assert_not_called()

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

        OrderService.update_status(1, {'status': 'processing'}, user_id=1, role='admin')
        repo.update_status.assert_called_once_with(order, 'processing', updated_by=1)

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

    def test_from_terminal_status_rejected(self, repo):
        repo.get_by_id.return_value = make_order(status='delivered', user_id=1)
        with pytest.raises(InvalidStatusTransitionError):
            OrderService.update_status(1, {'status': 'processing'}, user_id=1, role='admin')


class TestCancel:

    def test_not_found(self, repo):
        repo.get_active_by_id.return_value = None
        with pytest.raises(OrderNotFoundError):
            OrderService.cancel(1, user_id=1, role='buyer')

    def test_buyer_forbidden_other_user(self, repo):
        repo.get_active_by_id.return_value = make_order(user_id=2)
        with pytest.raises(OrderPermissionError):
            OrderService.cancel(1, user_id=1, role='buyer')

    def test_seller_forbidden_when_no_owned_product(self, repo):
        repo.get_active_by_id.return_value = make_order(user_id=999)
        repo.order_has_seller_product.return_value = False
        with pytest.raises(OrderPermissionError):
            OrderService.cancel(1, user_id=7, role='seller')
        repo.cancel_order.assert_not_called()

    def test_shipped_cannot_be_cancelled(self, repo):
        repo.get_active_by_id.return_value = make_order(status='shipped', user_id=1)
        with pytest.raises(OrderCannotBeDeletedError):
            OrderService.cancel(1, user_id=1, role='buyer')

    def test_delivered_cannot_be_cancelled(self, repo):
        repo.get_active_by_id.return_value = make_order(status='delivered', user_id=1)
        with pytest.raises(OrderCannotBeDeletedError):
            OrderService.cancel(1, user_id=1, role='buyer')

    def test_buyer_cancels_restores_stock_no_note(self, repo):
        order = make_order(status='waiting_for_payment', user_id=1)
        repo.get_active_by_id.return_value = order

        _, refund_note = OrderService.cancel(1, user_id=1, role='buyer')

        assert refund_note is None
        repo.cancel_order.assert_called_once_with(order, updated_by=1)

    def test_processing_cancel_has_refund_note(self, repo):
        order = make_order(status='processing', user_id=1)
        repo.get_active_by_id.return_value = order

        _, refund_note = OrderService.cancel(1, user_id=1, role='buyer')

        assert refund_note == 'payment refund will be processed'
        repo.cancel_order.assert_called_once_with(order, updated_by=1)

    def test_seller_cancels_owned_order_restores_stock(self, repo):
        order = make_order(status='processing', user_id=999)
        repo.get_active_by_id.return_value = order
        repo.order_has_seller_product.return_value = True

        _, refund_note = OrderService.cancel(1, user_id=7, role='seller')

        assert refund_note == 'payment refund will be processed'
        repo.cancel_order.assert_called_once_with(order, updated_by=7)

    def test_admin_can_cancel_other_users_order(self, repo):
        order = make_order(status='waiting_for_payment', user_id=999)
        repo.get_active_by_id.return_value = order

        OrderService.cancel(1, user_id=1, role='admin')
        repo.cancel_order.assert_called_once_with(order, updated_by=1)
