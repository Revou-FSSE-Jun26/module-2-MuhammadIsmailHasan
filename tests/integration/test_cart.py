import pytest

from app.models.products import Product
from app.models.product_images import ProductImage
from tests.conftest import get_auth_token, auth_header


def _buyer_token(client):
    return get_auth_token(client, 'buyer@test.com', 'password123')


def _make_product(db, seller_id, name, price=100.0, stock=10, is_active=True):
    product = Product(
        name=name,
        slug=name.lower().replace(' ', '-'),
        price=price,
        stock=stock,
        seller_id=seller_id,
        is_active=is_active,
    )
    db.session.add(product)
    db.session.commit()
    return product


class TestGetCart:

    def test_get_empty_cart(self, client, seed_users):
        token = _buyer_token(client)
        response = client.get('/api/v1/cart', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['groups'] == []
        assert data['data']['total_items'] == 0
        assert data['data']['grand_total'] == 0.0

    def test_get_cart_no_auth(self, client):
        response = client.get('/api/v1/cart')
        assert response.status_code == 401


class TestAddItem:

    def test_add_item_success(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]

        response = client.post('/api/v1/cart/items', json={
            'product_id': product.id, 'quantity': 2,
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['total_quantity'] == 2
        item = data['data']['groups'][0]['items'][0]
        assert item['product_id'] == product.id
        assert item['quantity'] == 2

    def test_add_item_default_quantity(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]

        response = client.post('/api/v1/cart/items', json={
            'product_id': product.id,
        }, headers=auth_header(token))

        assert response.status_code == 201
        assert response.get_json()['data']['total_quantity'] == 1

    def test_add_same_product_accumulates(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]
        payload = {'product_id': product.id, 'quantity': 2}

        client.post('/api/v1/cart/items', json=payload, headers=auth_header(token))
        response = client.post('/api/v1/cart/items', json=payload, headers=auth_header(token))
        data = response.get_json()

        assert data['data']['total_items'] == 1
        assert data['data']['total_quantity'] == 4

    def test_add_product_not_found(self, client, seed_users):
        token = _buyer_token(client)
        response = client.post('/api/v1/cart/items', json={
            'product_id': 9999, 'quantity': 1,
        }, headers=auth_header(token))
        assert response.status_code == 404

    def test_add_exceeds_stock(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]  # stock 10

        response = client.post('/api/v1/cart/items', json={
            'product_id': product.id, 'quantity': 99,
        }, headers=auth_header(token))
        assert response.status_code == 422

    def test_add_invalid_quantity(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]

        response = client.post('/api/v1/cart/items', json={
            'product_id': product.id, 'quantity': 0,
        }, headers=auth_header(token))
        assert response.status_code == 422


class TestSellerGrouping:

    def test_cart_grouped_by_seller(self, client, seed_users, seed_products, db):
        token = _buyer_token(client)
        seller1_product = seed_products[0]  # owned by seed_users['seller']
        seller2_product = _make_product(db, seed_users['seller2'].id, 'Seller2 Widget')

        client.post('/api/v1/cart/items', json={
            'product_id': seller1_product.id, 'quantity': 1,
        }, headers=auth_header(token))
        response = client.post('/api/v1/cart/items', json={
            'product_id': seller2_product.id, 'quantity': 2,
        }, headers=auth_header(token))
        data = response.get_json()['data']

        assert len(data['groups']) == 2
        seller_ids = {g['seller_id'] for g in data['groups']}
        assert seed_users['seller'].id in seller_ids
        assert seed_users['seller2'].id in seller_ids

    def test_group_totals(self, client, seed_users, db):
        token = _buyer_token(client)
        p1 = _make_product(db, seed_users['seller'].id, 'Alpha', price=100.0, stock=10)
        p2 = _make_product(db, seed_users['seller'].id, 'Beta', price=50.0, stock=10)

        client.post('/api/v1/cart/items', json={'product_id': p1.id, 'quantity': 2},
                    headers=auth_header(token))
        response = client.post('/api/v1/cart/items', json={'product_id': p2.id, 'quantity': 1},
                               headers=auth_header(token))
        data = response.get_json()['data']

        group = next(g for g in data['groups'] if g['seller_id'] == seed_users['seller'].id)
        assert group['group_total'] == 250.0
        assert data['grand_total'] == 250.0

    def test_primary_image_in_item(self, client, seed_users, seed_products, db):
        token = _buyer_token(client)
        product = seed_products[0]
        db.session.add_all([
            ProductImage(product_id=product.id, url='http://img/b.jpg', order=1),
            ProductImage(product_id=product.id, url='http://img/a.jpg', order=0),
        ])
        db.session.commit()

        response = client.post('/api/v1/cart/items', json={
            'product_id': product.id, 'quantity': 1,
        }, headers=auth_header(token))
        item = response.get_json()['data']['groups'][0]['items'][0]

        assert item['product']['image'] == 'http://img/a.jpg'


class TestUpdateAndRemove:

    def _add(self, client, token, product_id, quantity=1):
        return client.post('/api/v1/cart/items', json={
            'product_id': product_id, 'quantity': quantity,
        }, headers=auth_header(token))

    def test_update_quantity(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]
        add = self._add(client, token, product.id, 1)
        item_id = add.get_json()['data']['groups'][0]['items'][0]['id']

        response = client.put(f'/api/v1/cart/items/{item_id}', json={'quantity': 5},
                              headers=auth_header(token))
        data = response.get_json()['data']

        assert response.status_code == 200
        assert data['total_quantity'] == 5

    def test_update_quantity_zero_removes(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]
        add = self._add(client, token, product.id, 1)
        item_id = add.get_json()['data']['groups'][0]['items'][0]['id']

        response = client.put(f'/api/v1/cart/items/{item_id}', json={'quantity': 0},
                              headers=auth_header(token))
        data = response.get_json()['data']

        assert response.status_code == 200
        assert data['total_items'] == 0

    def test_update_exceeds_stock(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]
        add = self._add(client, token, product.id, 1)
        item_id = add.get_json()['data']['groups'][0]['items'][0]['id']

        response = client.put(f'/api/v1/cart/items/{item_id}', json={'quantity': 999},
                              headers=auth_header(token))
        assert response.status_code == 422

    def test_update_item_not_found(self, client, seed_users):
        token = _buyer_token(client)
        response = client.put('/api/v1/cart/items/9999', json={'quantity': 2},
                              headers=auth_header(token))
        assert response.status_code == 404

    def test_remove_item(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]
        add = self._add(client, token, product.id, 1)
        item_id = add.get_json()['data']['groups'][0]['items'][0]['id']

        response = client.delete(f'/api/v1/cart/items/{item_id}',
                                 headers=auth_header(token))
        assert response.status_code == 200
        assert response.get_json()['data']['total_items'] == 0

    def test_remove_item_not_found(self, client, seed_users):
        token = _buyer_token(client)
        response = client.delete('/api/v1/cart/items/9999', headers=auth_header(token))
        assert response.status_code == 404

    def test_clear_cart(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        self._add(client, token, seed_products[0].id, 1)
        self._add(client, token, seed_products[1].id, 1)

        response = client.delete('/api/v1/cart', headers=auth_header(token))
        assert response.status_code == 200
        assert response.get_json()['data']['total_items'] == 0


class TestCheckout:

    def _add(self, client, token, product_id, quantity=1):
        return client.post('/api/v1/cart/items', json={
            'product_id': product_id, 'quantity': quantity,
        }, headers=auth_header(token))

    def test_checkout_creates_order_and_clears_cart(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        product = seed_products[0]
        self._add(client, token, product.id, 2)

        response = client.post('/api/v1/cart/checkout', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['status'] == 'waiting_for_payment'
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['quantity'] == 2

        cart = client.get('/api/v1/cart', headers=auth_header(token)).get_json()
        assert cart['data']['total_items'] == 0

    def test_checkout_decrements_stock(self, client, seed_users, seed_products, db):
        token = _buyer_token(client)
        product = seed_products[0]
        original_stock = product.stock
        self._add(client, token, product.id, 3)

        client.post('/api/v1/cart/checkout', headers=auth_header(token))

        db.session.refresh(product)
        assert product.stock == original_stock - 3

    def test_checkout_empty_cart(self, client, seed_users):
        token = _buyer_token(client)
        response = client.post('/api/v1/cart/checkout', headers=auth_header(token))
        assert response.status_code == 400

    def test_checkout_unavailable_product(self, client, seed_users, seed_products, db):
        token = _buyer_token(client)
        product = seed_products[0]
        self._add(client, token, product.id, 1)

        product.is_active = False
        db.session.commit()

        response = client.post('/api/v1/cart/checkout', headers=auth_header(token))
        assert response.status_code == 409


class TestCheckoutRemovesOnlyOrderedItems:

    def test_service_removes_only_given_products(self, app, seed_users, seed_products, db):
        from app.repositories.cart_repository import CartRepository

        buyer = seed_users['buyer']
        p1, p2 = seed_products[0], seed_products[1]

        cart = CartRepository.get_or_create_cart(buyer.id)
        CartRepository.add_item(cart.id, p1.id, 1)
        CartRepository.add_item(cart.id, p2.id, 1)

        cart = CartRepository.get_active_cart(buyer.id)
        CartRepository.delete_items_by_product_ids(cart, [p1.id])

        cart = CartRepository.get_active_cart(buyer.id)
        remaining = [i.product_id for i in cart.items]
        assert remaining == [p2.id]

    def test_full_checkout_empties_cart(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        client.post('/api/v1/cart/items', json={'product_id': seed_products[0].id, 'quantity': 1},
                    headers=auth_header(token))
        client.post('/api/v1/cart/items', json={'product_id': seed_products[1].id, 'quantity': 1},
                    headers=auth_header(token))

        client.post('/api/v1/cart/checkout', headers=auth_header(token))

        cart = client.get('/api/v1/cart', headers=auth_header(token)).get_json()
        assert cart['data']['total_items'] == 0


class TestCartAvailabilityIsLive:

    def test_direct_order_makes_cart_item_unavailable(
        self, client, seed_users, seed_products, db
    ):
        token = _buyer_token(client)
        product = seed_products[0]

        client.post('/api/v1/cart/items', json={'product_id': product.id, 'quantity': 8},
                    headers=auth_header(token))

        cart = client.get('/api/v1/cart', headers=auth_header(token)).get_json()['data']
        assert cart['groups'][0]['items'][0]['available'] is True

        client.post('/api/v1/orders/', json={
            'items': [{'product_id': product.id, 'quantity': 7}]
        }, headers=auth_header(token))

        cart = client.get('/api/v1/cart', headers=auth_header(token)).get_json()['data']
        item = cart['groups'][0]['items'][0]
        assert item['available'] is False
        assert '3' in item['note']

    def test_cancel_restores_cart_item_availability(
        self, client, seed_users, seed_products, db
    ):
        token = _buyer_token(client)
        product = seed_products[0]  # stock 10

        client.post('/api/v1/cart/items', json={'product_id': product.id, 'quantity': 8},
                    headers=auth_header(token))

        order_resp = client.post('/api/v1/orders/', json={
            'items': [{'product_id': product.id, 'quantity': 7}]
        }, headers=auth_header(token))
        order_id = order_resp.get_json()['data']['id']

        cart = client.get('/api/v1/cart', headers=auth_header(token)).get_json()['data']
        assert cart['groups'][0]['items'][0]['available'] is False

        client.delete(f'/api/v1/orders/{order_id}', headers=auth_header(token))

        cart = client.get('/api/v1/cart', headers=auth_header(token)).get_json()['data']
        assert cart['groups'][0]['items'][0]['available'] is True


class TestPartialCheckout:

    def _add(self, client, token, product_id, quantity=1):
        return client.post('/api/v1/cart/items', json={
            'product_id': product_id, 'quantity': quantity,
        }, headers=auth_header(token))

    def _two_seller_cart(self, client, token, seed_users, seed_products, db):
        seller1_product = seed_products[0]  # owned by seed_users['seller']
        seller2_product = _make_product(db, seed_users['seller2'].id, 'Seller2 Widget')
        self._add(client, token, seller1_product.id, 1)
        self._add(client, token, seller2_product.id, 2)
        return seller1_product, seller2_product

    def test_full_checkout_still_works_with_empty_body(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        self._add(client, token, seed_products[0].id, 1)

        response = client.post('/api/v1/cart/checkout', headers=auth_header(token))
        assert response.status_code == 201

        cart = client.get('/api/v1/cart', headers=auth_header(token)).get_json()
        assert cart['data']['total_items'] == 0

    def test_checkout_by_seller_leaves_other_group(
        self, client, seed_users, seed_products, db
    ):
        token = _buyer_token(client)
        s1_product, s2_product = self._two_seller_cart(
            client, token, seed_users, seed_products, db
        )

        response = client.post('/api/v1/cart/checkout', json={
            'seller_id': seed_users['seller'].id,
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['items'][0]['product_id'] == s1_product.id
        assert len(data['data']['items']) == 1

        cart = client.get('/api/v1/cart', headers=auth_header(token)).get_json()['data']
        assert cart['total_items'] == 1
        remaining_ids = [i['product_id'] for g in cart['groups'] for i in g['items']]
        assert remaining_ids == [s2_product.id]

    def test_checkout_by_item_ids(self, client, seed_users, seed_products, db):
        token = _buyer_token(client)
        self._two_seller_cart(client, token, seed_users, seed_products, db)

        cart = client.get('/api/v1/cart', headers=auth_header(token)).get_json()['data']
        first_item = cart['groups'][0]['items'][0]

        response = client.post('/api/v1/cart/checkout', json={
            'cart_item_ids': [first_item['id']],
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['items'][0]['product_id'] == first_item['product_id']

        after = client.get('/api/v1/cart', headers=auth_header(token)).get_json()['data']
        assert after['total_items'] == 1

    def test_checkout_by_seller_no_match(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        self._add(client, token, seed_products[0].id, 1)

        response = client.post('/api/v1/cart/checkout', json={
            'seller_id': 99999,
        }, headers=auth_header(token))
        assert response.status_code == 404

    def test_checkout_unknown_item_id(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        self._add(client, token, seed_products[0].id, 1)

        response = client.post('/api/v1/cart/checkout', json={
            'cart_item_ids': [999999],
        }, headers=auth_header(token))
        assert response.status_code == 404

    def test_checkout_both_selectors_rejected(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        self._add(client, token, seed_products[0].id, 1)

        response = client.post('/api/v1/cart/checkout', json={
            'seller_id': 1,
            'cart_item_ids': [1],
        }, headers=auth_header(token))
        assert response.status_code == 422

    def test_checkout_empty_item_ids_rejected(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        self._add(client, token, seed_products[0].id, 1)

        response = client.post('/api/v1/cart/checkout', json={
            'cart_item_ids': [],
        }, headers=auth_header(token))
        assert response.status_code == 422
