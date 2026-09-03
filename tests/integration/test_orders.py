import pytest
from app.models.orders import Order, OrderItem
from app.models.products import Product
from tests.conftest import get_auth_token, auth_header


@pytest.fixture
def seed_order(db, seed_users, seed_products):
    buyer = seed_users['buyer']
    product = seed_products[0]

    order = Order(
        user_id=buyer.id,
        total_amount=999.99,
        status='waiting_for_payment'
    )
    db.session.add(order)
    db.session.flush()

    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        unit_price=999.99,
        quantity=1,
        sub_total=999.99
    )
    db.session.add(order_item)

    product.stock -= 1
    db.session.commit()

    return order


class TestCreateOrder:

    def test_create_order_success(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        product = seed_products[0]

        response = client.post('/api/v1/orders/', json={
            'items': [
                {'product_id': product.id, 'quantity': 2}
            ]
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 201
        assert data['status'] is True
        assert data['data']['status'] == 'waiting_for_payment'
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['quantity'] == 2

    def test_create_order_multiple_items(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.post('/api/v1/orders/', json={
            'items': [
                {'product_id': seed_products[0].id, 'quantity': 1},
                {'product_id': seed_products[1].id, 'quantity': 3}
            ]
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 201
        assert len(data['data']['items']) == 2

    def test_create_order_product_not_found(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.post('/api/v1/orders/', json={
            'items': [{'product_id': 9999, 'quantity': 1}]
        }, headers=auth_header(token))

        assert response.status_code == 404
        assert 'product with id 9999 not found' in response.get_json()['message']

    def test_create_order_insufficient_stock(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        product = seed_products[0]

        response = client.post('/api/v1/orders/', json={
            'items': [{'product_id': product.id, 'quantity': 999}]
        }, headers=auth_header(token))

        assert response.status_code == 422
        assert 'insufficient stock' in response.get_json()['message']

    def test_create_order_empty_items(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.post('/api/v1/orders/', json={
            'items': []
        }, headers=auth_header(token))

        assert response.status_code == 422

    def test_create_order_seller_forbidden(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/orders/', json={
            'items': [{'product_id': seed_products[0].id, 'quantity': 1}]
        }, headers=auth_header(token))

        assert response.status_code == 403


class TestGetOrders:

    def test_get_orders_buyer_sees_own(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/orders/', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['pagination']['total_items'] >= 1
        for order in data['data']:
            assert order['user_id'] == seed_users['buyer'].id

    def test_get_orders_admin_sees_all(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.get('/api/v1/orders/', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['pagination']['total_items'] >= 1

    def test_get_orders_filter_by_status(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/orders/?status=waiting_for_payment',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        for order in data['data']:
            assert order['status'] == 'waiting_for_payment'


class TestGetOrder:

    def test_get_order_success(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get(f'/api/v1/orders/{seed_order.id}',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['id'] == seed_order.id
        assert 'items' in data['data']
        assert len(data['data']['items']) > 0

    def test_get_order_not_found(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/orders/9999',
                              headers=auth_header(token))

        assert response.status_code == 404

    def test_get_order_other_user_forbidden(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller2@test.com', 'password123')

        response = client.get(f'/api/v1/orders/{seed_order.id}',
                              headers=auth_header(token))

        assert response.status_code == 403

    def test_get_order_seller_owning_product_can_view(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.get(f'/api/v1/orders/{seed_order.id}',
                              headers=auth_header(token))

        assert response.status_code == 200
        assert response.get_json()['data']['id'] == seed_order.id


class TestGetOrdersSellerScope:

    def test_seller_sees_orders_with_their_products(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.get('/api/v1/orders/', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['pagination']['total_items'] >= 1
        assert seed_order.id in [o['id'] for o in data['data']]

    def test_seller_without_matching_products_sees_none(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller2@test.com', 'password123')

        response = client.get('/api/v1/orders/', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['pagination']['total_items'] == 0


class TestUpdateOrderStatus:

    def test_seller_owning_product_can_confirm_payment(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'paid'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'paid'

    def test_admin_can_confirm_payment(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'paid'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'paid'

    def test_buyer_cannot_advance_fulfillment(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'paid'
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_seller_without_owned_product_forbidden(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller2@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'paid'
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_seller_can_cancel_via_put_and_restores_stock(self, client, db, seed_users, seed_order, seed_products):
        seed_order.status = 'processing'
        db.session.commit()
        stock_before = seed_products[0].stock
        qty = seed_order.items[0].quantity

        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'cancelled'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'cancelled'
        assert data['data']['refund_note'] == 'payment refund will be processed'
        db.session.refresh(seed_products[0])
        assert seed_products[0].stock == stock_before + qty

    def test_buyer_can_cancel_waiting_order_no_refund_note(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'cancelled'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'cancelled'
        assert data['data'].get('refund_note') is None

    def test_update_status_skip_step(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'shipped'
        }, headers=auth_header(token))

        assert response.status_code == 400
        assert 'cannot change status' in response.get_json()['message']

    def test_update_status_stamps_updated_by(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'paid'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['updated_by'] == seed_users['seller'].id

    def test_update_cancelled_order_rejected(self, client, seed_users, seed_order, db):
        seed_order.status = 'cancelled'
        seed_order.is_active = False
        db.session.commit()

        token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'processing'
        }, headers=auth_header(token))

        assert response.status_code == 400
        assert 'can no longer be modified' in response.get_json()['message']

    def test_update_status_invalid_value(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'flying'
        }, headers=auth_header(token))

        assert response.status_code == 422

    def test_update_status_not_found(self, client, seed_users):
        token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.put('/api/v1/orders/9999', json={
            'status': 'processing'
        }, headers=auth_header(token))

        assert response.status_code == 404


class TestShipTracking:

    def _processing_order(self, seed_order, db):
        seed_order.status = 'processing'
        db.session.commit()
        return seed_order

    def test_ship_requires_tracking_id(self, client, db, seed_users, seed_order):
        self._processing_order(seed_order, db)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'shipped'
        }, headers=auth_header(token))

        assert response.status_code == 422
        assert 'tracking_id is required' in response.get_json()['message']

    def test_ship_with_tracking_id_succeeds(self, client, db, seed_users, seed_order):
        self._processing_order(seed_order, db)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'shipped', 'tracking_id': 'JNE-0001234567'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'shipped'
        assert data['data']['tracking_id'] == 'JNE-0001234567'

    def test_tracking_id_ignored_on_processing(self, client, db, seed_users, seed_order):
        seed_order.status = 'paid'
        db.session.commit()
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'processing', 'tracking_id': 'SHOULD-NOT-STICK'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['tracking_id'] is None

    def test_tracking_id_frozen_after_shipped(self, client, db, seed_users, seed_order):
        self._processing_order(seed_order, db)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'shipped', 'tracking_id': 'JNE-0001234567'
        }, headers=auth_header(token))

        client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'delivered'
        }, headers=auth_header(token))

        fetched = client.get(f'/api/v1/orders/{seed_order.id}',
                             headers=auth_header(token)).get_json()['data']
        assert fetched['tracking_id'] == 'JNE-0001234567'


class TestDeleteOrder:

    def test_delete_cancelled_order(self, client, seed_users, seed_order, db):
        seed_order.status = 'cancelled'
        db.session.commit()
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'cancelled'
        assert 'refund_note' not in data['data']

    def test_delete_delivered_order(self, client, seed_users, seed_order, db):
        seed_order.status = 'delivered'
        db.session.commit()
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'delivered'

    def test_delete_waiting_for_payment_blocked(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))

        assert response.status_code == 400
        assert "cannot delete order with status 'waiting_for_payment'" in response.get_json()['message']

    def test_delete_shipped_blocked(self, client, seed_users, seed_order, db):
        seed_order.status = 'shipped'
        db.session.commit()

        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))

        assert response.status_code == 400
        assert "cannot delete order with status 'shipped'" in response.get_json()['message']

    def test_delete_order_not_found(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete('/api/v1/orders/9999',
                                 headers=auth_header(token))

        assert response.status_code == 404

    def test_delete_buyer_other_user_forbidden(self, client, seed_users, seed_order, db):
        from app.models.users import User
        from app.auth import hash_password

        seed_order.status = 'cancelled'
        db.session.commit()

        other = User(username='other_buyer', email='other@test.com',
                     password_hash=hash_password('password123'), role='buyer')
        db.session.add(other)
        db.session.commit()

        token = get_auth_token(client, 'other@test.com', 'password123')
        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))

        assert response.status_code == 403

    def test_delete_does_not_restore_stock(self, client, seed_users, seed_order, seed_products, db):
        seed_order.status = 'cancelled'
        db.session.commit()
        stock_before = seed_products[0].stock

        token = get_auth_token(client, 'seller@test.com', 'password123')
        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))

        assert response.status_code == 200
        db.session.refresh(seed_products[0])
        assert seed_products[0].stock == stock_before

    def test_seller_without_owned_product_forbidden_to_delete(self, client, seed_users, seed_order, db):
        seed_order.status = 'cancelled'
        db.session.commit()
        token = get_auth_token(client, 'seller2@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))

        assert response.status_code == 403


class TestOrderItemCalculations:

    @pytest.fixture
    def seed_multi_item_order(self, db, seed_users, seed_products):
        buyer = seed_users['buyer']
        p1, p2 = seed_products[0], seed_products[1]

        order = Order(user_id=buyer.id, total_amount=0, status='processing')
        db.session.add(order)
        db.session.flush()

        db.session.add(OrderItem(
            order_id=order.id, product_id=p1.id,
            unit_price=p1.price, quantity=2, sub_total=p1.price * 2,
        ))
        db.session.add(OrderItem(
            order_id=order.id, product_id=p2.id,
            unit_price=p2.price, quantity=3, sub_total=p2.price * 3,
        ))
        db.session.commit()
        return order

    def test_get_all_includes_total_items_and_quantity(
        self, client, seed_users, seed_multi_item_order
    ):
        order = seed_multi_item_order
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/orders/', headers=auth_header(token))
        data = response.get_json()

        target = next(o for o in data['data'] if o['id'] == order.id)
        assert target['total_items'] == 2
        assert target['total_quantity'] == 5

    def test_get_all_empty_counts_for_no_items(self, client, seed_users, db):
        buyer = seed_users['buyer']
        order = Order(user_id=buyer.id, total_amount=0, status='processing')
        db.session.add(order)
        db.session.commit()

        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.get('/api/v1/orders/', headers=auth_header(token))
        data = response.get_json()

        target = next(o for o in data['data'] if o['id'] == order.id)
        assert target['total_items'] == 0
        assert target['total_quantity'] == 0


class TestOrderItemProductDetail:

    @pytest.fixture
    def seed_order_with_images(self, db, seed_users, seed_products):
        from app.models.product_images import ProductImage

        buyer = seed_users['buyer']
        product = seed_products[0]

        db.session.add_all([
            ProductImage(product_id=product.id, url='http://img/c.jpg', order=2),
            ProductImage(product_id=product.id, url='http://img/a.jpg', order=0),
            ProductImage(product_id=product.id, url='http://img/b.jpg', order=1),
            ProductImage(product_id=product.id, url='http://img/gone.jpg',
                         order=3, is_active=False),
        ])

        order = Order(user_id=buyer.id, total_amount=product.price,
                      status='processing')
        db.session.add(order)
        db.session.flush()
        db.session.add(OrderItem(
            order_id=order.id, product_id=product.id,
            unit_price=product.price, quantity=1, sub_total=product.price,
        ))
        db.session.commit()
        return order, product

    def test_get_by_id_item_has_product_detail(
        self, client, seed_users, seed_order_with_images
    ):
        order, product = seed_order_with_images
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get(f'/api/v1/orders/{order.id}',
                              headers=auth_header(token))
        data = response.get_json()['data']

        item = data['items'][0]
        assert 'product' in item
        assert item['product']['id'] == product.id
        assert item['product']['name'] == product.name
        assert item['product']['slug'] == product.slug

    def test_get_by_id_product_primary_image_is_smallest_order(
        self, client, seed_users, seed_order_with_images
    ):
        order, _ = seed_order_with_images
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get(f'/api/v1/orders/{order.id}',
                              headers=auth_header(token))
        product = response.get_json()['data']['items'][0]['product']

        assert product['image'] == 'http://img/a.jpg'

    def test_get_by_id_product_has_no_images_list(
        self, client, seed_users, seed_order_with_images
    ):
        order, _ = seed_order_with_images
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get(f'/api/v1/orders/{order.id}',
                              headers=auth_header(token))
        product = response.get_json()['data']['items'][0]['product']

        # Order detail only carries the primary image, not the full list.
        assert 'image' in product
        assert 'images' not in product

    def test_get_all_does_not_embed_product_detail(
        self, client, seed_users, seed_order_with_images
    ):
        order, _ = seed_order_with_images
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/orders/', headers=auth_header(token))
        target = next(o for o in response.get_json()['data'] if o['id'] == order.id)

        assert 'items' not in target
        assert 'product' not in target
