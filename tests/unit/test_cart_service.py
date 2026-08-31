from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.cart_service import (
    CartService,
    ProductNotFoundError,
    CartItemNotFoundError,
    InsufficientStockError,
    EmptyCartError,
    ProductUnavailableError,
    CartSelectionError,
)


def make_product(id=1, name='Laptop', price=100.0, stock=10,
                 seller_id=10, seller_name='alice', is_active=True,
                 primary_url='http://img/a.jpg'):
    seller = SimpleNamespace(id=seller_id, username=seller_name) if seller_id else None
    primary = SimpleNamespace(url=primary_url) if primary_url else None
    return SimpleNamespace(
        id=id, name=name, slug=f'p-{id}', price=price, stock=stock,
        seller_id=seller_id, seller=seller, is_active=is_active,
        primary_image=primary,
    )


def make_item(id=1, product=None, quantity=1, product_id=None):
    product = product if product is not None else make_product()
    return SimpleNamespace(
        id=id,
        product=product,
        product_id=product_id if product_id is not None else product.id,
        quantity=quantity,
    )


def make_cart(id=1, items=None):
    return SimpleNamespace(id=id, items=items or [])


@pytest.fixture
def repo():
    with patch('app.services.cart_service.CartRepository') as mock_repo:
        yield mock_repo


@pytest.fixture
def order_service():
    with patch('app.services.cart_service.OrderService') as mock_os:
        yield mock_os


class TestAddItem:

    def test_add_new_item(self, repo):
        product = make_product(stock=10)
        repo.get_product.return_value = product
        repo.get_or_create_cart.return_value = make_cart()
        repo.get_item_by_product.return_value = None
        repo.get_active_cart.return_value = make_cart()

        CartService.add_item(1, product.id, 2)

        repo.add_item.assert_called_once_with(1, product.id, 2)

    def test_add_existing_item_accumulates(self, repo):
        product = make_product(stock=10)
        repo.get_product.return_value = product
        repo.get_or_create_cart.return_value = make_cart()
        existing = make_item(product=product, quantity=3)
        repo.get_item_by_product.return_value = existing
        repo.get_active_cart.return_value = make_cart()

        CartService.add_item(1, product.id, 2)

        repo.set_quantity.assert_called_once_with(existing, 5)
        repo.add_item.assert_not_called()

    def test_add_product_not_found(self, repo):
        repo.get_product.return_value = None
        with pytest.raises(ProductNotFoundError):
            CartService.add_item(1, 999, 1)

    def test_add_exceeds_stock(self, repo):
        product = make_product(stock=3)
        repo.get_product.return_value = product
        repo.get_or_create_cart.return_value = make_cart()
        repo.get_item_by_product.return_value = None

        with pytest.raises(InsufficientStockError):
            CartService.add_item(1, product.id, 5)
        repo.add_item.assert_not_called()

    def test_add_accumulation_exceeds_stock(self, repo):
        product = make_product(stock=4)
        repo.get_product.return_value = product
        repo.get_or_create_cart.return_value = make_cart()
        repo.get_item_by_product.return_value = make_item(product=product, quantity=3)

        with pytest.raises(InsufficientStockError):
            CartService.add_item(1, product.id, 2)  # 3 + 2 > 4


class TestUpdateItem:

    def test_update_success(self, repo):
        product = make_product(stock=10)
        item = make_item(product=product, quantity=1)
        repo.get_active_cart.return_value = make_cart(items=[item])
        repo.get_item.return_value = item
        repo.get_product.return_value = product

        CartService.update_item(1, item.id, 4)

        repo.set_quantity.assert_called_once_with(item, 4)

    def test_update_zero_deletes(self, repo):
        item = make_item(quantity=2)
        repo.get_active_cart.return_value = make_cart(items=[item])
        repo.get_item.return_value = item

        CartService.update_item(1, item.id, 0)

        repo.delete_item.assert_called_once_with(item)
        repo.set_quantity.assert_not_called()

    def test_update_no_cart(self, repo):
        repo.get_active_cart.return_value = None
        with pytest.raises(CartItemNotFoundError):
            CartService.update_item(1, 5, 2)

    def test_update_item_not_found(self, repo):
        repo.get_active_cart.return_value = make_cart()
        repo.get_item.return_value = None
        with pytest.raises(CartItemNotFoundError):
            CartService.update_item(1, 999, 2)

    def test_update_exceeds_stock(self, repo):
        product = make_product(stock=3)
        item = make_item(product=product, quantity=1)
        repo.get_active_cart.return_value = make_cart(items=[item])
        repo.get_item.return_value = item
        repo.get_product.return_value = product

        with pytest.raises(InsufficientStockError):
            CartService.update_item(1, item.id, 5)


class TestRemoveItem:

    def test_remove_success(self, repo):
        item = make_item()
        repo.get_active_cart.return_value = make_cart(items=[item])
        repo.get_item.return_value = item

        CartService.remove_item(1, item.id)

        repo.delete_item.assert_called_once_with(item)

    def test_remove_no_cart(self, repo):
        repo.get_active_cart.return_value = None
        with pytest.raises(CartItemNotFoundError):
            CartService.remove_item(1, 5)

    def test_remove_item_not_found(self, repo):
        repo.get_active_cart.return_value = make_cart()
        repo.get_item.return_value = None
        with pytest.raises(CartItemNotFoundError):
            CartService.remove_item(1, 999)


class TestGetCartView:

    def test_empty_when_no_cart(self, repo):
        repo.get_active_cart.return_value = None

        view = CartService.get_cart(1)

        assert view['cart_id'] is None
        assert view['groups'] == []
        assert view['total_items'] == 0
        assert view['grand_total'] == 0.0

    def test_grouping_by_seller(self, repo):
        p_alice = make_product(id=1, price=100.0, stock=10, seller_id=10, seller_name='alice')
        p_alice2 = make_product(id=2, price=50.0, stock=10, seller_id=10, seller_name='alice')
        p_charlie = make_product(id=3, price=20.0, stock=10, seller_id=20, seller_name='charlie')

        items = [
            make_item(id=1, product=p_alice, quantity=2),    # 200
            make_item(id=2, product=p_charlie, quantity=1),  # 20
            make_item(id=3, product=p_alice2, quantity=3),   # 150
        ]
        repo.get_active_cart.return_value = make_cart(id=7, items=items)

        view = CartService.get_cart(1)

        assert view['cart_id'] == 7
        assert len(view['groups']) == 2

        alice_group = next(g for g in view['groups'] if g['seller_id'] == 10)
        charlie_group = next(g for g in view['groups'] if g['seller_id'] == 20)

        assert alice_group['seller_name'] == 'alice'
        assert alice_group['group_total_items'] == 2
        assert alice_group['group_total_quantity'] == 5
        assert alice_group['group_total'] == 350.0

        assert charlie_group['group_total'] == 20.0

        assert view['total_items'] == 3
        assert view['total_quantity'] == 6
        assert view['grand_total'] == 370.0

    def test_item_view_includes_primary_image_and_subtotal(self, repo):
        product = make_product(id=1, price=99.99, stock=10, primary_url='http://img/x.jpg')
        repo.get_active_cart.return_value = make_cart(items=[make_item(product=product, quantity=2)])

        view = CartService.get_cart(1)
        item = view['groups'][0]['items'][0]

        assert item['unit_price'] == 99.99
        assert item['sub_total'] == round(99.99 * 2, 2)
        assert item['product']['image'] == 'http://img/x.jpg'
        assert item['available'] is True

    def test_item_flagged_unavailable_when_out_of_stock(self, repo):
        product = make_product(stock=1)
        repo.get_active_cart.return_value = make_cart(items=[make_item(product=product, quantity=5)])

        view = CartService.get_cart(1)
        item = view['groups'][0]['items'][0]

        assert item['available'] is False
        assert 'stock' in item['note']

    def test_null_seller_grouped_as_unknown(self, repo):
        product = make_product(seller_id=None, seller_name=None)
        repo.get_active_cart.return_value = make_cart(items=[make_item(product=product)])

        view = CartService.get_cart(1)

        assert view['groups'][0]['seller_id'] is None
        assert view['groups'][0]['seller_name'] == 'Unknown seller'


class TestCheckout:

    def test_empty_cart(self, repo, order_service):
        repo.get_active_cart.return_value = None
        with pytest.raises(EmptyCartError):
            CartService.checkout(1)

        repo.get_active_cart.return_value = make_cart(items=[])
        with pytest.raises(EmptyCartError):
            CartService.checkout(1)

    def test_checkout_delegates_and_clears(self, repo, order_service):
        product = make_product(stock=10, is_active=True)
        cart = make_cart(items=[make_item(product=product, quantity=2)])
        repo.get_active_cart.return_value = cart
        order_service.create.return_value = SimpleNamespace(id=42)

        order = CartService.checkout(1)

        assert order.id == 42
        order_service.create.assert_called_once()
        called_args = order_service.create.call_args
        assert called_args.args[0] == 1
        assert called_args.args[1] == {
            'items': [{'product_id': product.id, 'quantity': 2}],
            'address_id': None,
        }
        repo.delete_items_by_product_ids.assert_called_once_with(cart, [product.id])

    def test_checkout_removes_only_ordered_products(self, repo, order_service):
        p1 = make_product(id=1, stock=10, is_active=True)
        p2 = make_product(id=2, stock=10, is_active=True)
        cart = make_cart(items=[
            make_item(id=1, product=p1, quantity=1),
            make_item(id=2, product=p2, quantity=2),
        ])
        repo.get_active_cart.return_value = cart
        order_service.create.return_value = SimpleNamespace(id=99)

        CartService.checkout(1)

        args = repo.delete_items_by_product_ids.call_args.args
        assert args[0] is cart
        assert set(args[1]) == {1, 2}

    def test_checkout_unavailable_product(self, repo, order_service):
        product = make_product(is_active=False)
        cart = make_cart(items=[make_item(product=product, quantity=1)])
        repo.get_active_cart.return_value = cart

        with pytest.raises(ProductUnavailableError):
            CartService.checkout(1)
        order_service.create.assert_not_called()
        repo.delete_items_by_product_ids.assert_not_called()

    def test_checkout_insufficient_stock(self, repo, order_service):
        product = make_product(stock=1, is_active=True)
        cart = make_cart(items=[make_item(product=product, quantity=5)])
        repo.get_active_cart.return_value = cart

        with pytest.raises(InsufficientStockError):
            CartService.checkout(1)
        order_service.create.assert_not_called()


class TestCheckoutSelection:

    def _two_seller_cart(self, repo):
        p_alice = make_product(id=1, stock=10, seller_id=10, seller_name='alice')
        p_charlie = make_product(id=2, stock=10, seller_id=20, seller_name='charlie')
        cart = make_cart(items=[
            make_item(id=1, product=p_alice, quantity=2),
            make_item(id=2, product=p_charlie, quantity=3),
        ])
        repo.get_active_cart.return_value = cart
        return cart, p_alice, p_charlie

    def test_checkout_by_seller_orders_only_that_seller(self, repo, order_service):
        cart, p_alice, _ = self._two_seller_cart(repo)
        order_service.create.return_value = SimpleNamespace(id=1)

        CartService.checkout(1, seller_id=10)

        payload = order_service.create.call_args.args[1]
        assert payload == {
            'items': [{'product_id': p_alice.id, 'quantity': 2}],
            'address_id': None,
        }
        repo.delete_items_by_product_ids.assert_called_once_with(cart, [p_alice.id])

    def test_checkout_by_seller_no_match(self, repo, order_service):
        self._two_seller_cart(repo)
        with pytest.raises(CartSelectionError):
            CartService.checkout(1, seller_id=999)
        order_service.create.assert_not_called()

    def test_checkout_by_item_ids(self, repo, order_service):
        cart, _, p_charlie = self._two_seller_cart(repo)
        order_service.create.return_value = SimpleNamespace(id=1)

        CartService.checkout(1, cart_item_ids=[2])

        payload = order_service.create.call_args.args[1]
        assert payload == {
            'items': [{'product_id': p_charlie.id, 'quantity': 3}],
            'address_id': None,
        }
        repo.delete_items_by_product_ids.assert_called_once_with(cart, [p_charlie.id])

    def test_checkout_by_item_ids_unknown_id(self, repo, order_service):
        self._two_seller_cart(repo)
        with pytest.raises(CartSelectionError):
            CartService.checkout(1, cart_item_ids=[2, 999])
        order_service.create.assert_not_called()

    def test_full_checkout_when_no_selection(self, repo, order_service):
        cart, p_alice, p_charlie = self._two_seller_cart(repo)
        order_service.create.return_value = SimpleNamespace(id=1)

        CartService.checkout(1)

        payload = order_service.create.call_args.args[1]
        assert len(payload['items']) == 2
        removed = repo.delete_items_by_product_ids.call_args.args[1]
        assert set(removed) == {p_alice.id, p_charlie.id}
