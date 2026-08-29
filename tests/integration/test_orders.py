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

    def test_seller_owning_product_can_advance(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'processing'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'processing'

    def test_admin_can_advance(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'processing'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'processing'

    def test_buyer_cannot_update_status(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'processing'
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_seller_without_owned_product_forbidden(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller2@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'processing'
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_seller_can_cancel(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'cancelled'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'cancelled'

    def test_update_status_skip_step(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'shipped'
        }, headers=auth_header(token))

        assert response.status_code == 400
        assert 'cannot change status' in response.get_json()['message']

    def test_update_status_backward(self, client, seed_users, seed_order, db):
        seed_order.status = 'processing'
        db.session.commit()

        token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'waiting_for_payment'
        }, headers=auth_header(token))

        assert response.status_code == 400

    def test_seller_cannot_target_waiting_for_payment(self, client, seed_users, seed_order, db):
        seed_order.status = 'processing'
        db.session.commit()

        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/orders/{seed_order.id}', json={
            'status': 'waiting_for_payment'
        }, headers=auth_header(token))

        assert response.status_code == 403

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


class TestDeleteOrder:

    def test_delete_waiting_for_payment(self, client, seed_users, seed_order, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'cancelled'

    def test_delete_processing_has_refund_note(self, client, seed_users, seed_order, db):
        seed_order.status = 'processing'
        db.session.commit()

        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['status'] == 'cancelled'
        assert data['data']['refund_note'] == 'payment refund will be processed'

    def test_delete_shipped_blocked(self, client, seed_users, seed_order, db):
        seed_order.status = 'shipped'
        db.session.commit()

        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))

        assert response.status_code == 400
        assert "cannot delete order with status 'shipped'" in response.get_json()['message']

    def test_delete_delivered_blocked(self, client, seed_users, seed_order, db):
        seed_order.status = 'delivered'
        db.session.commit()

        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))

        assert response.status_code == 400
        assert "cannot delete order with status 'delivered'" in response.get_json()['message']

    def test_delete_order_not_found(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete('/api/v1/orders/9999',
                                 headers=auth_header(token))

        assert response.status_code == 404

    def test_delete_order_other_user_forbidden(self, client, seed_users, seed_order):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.delete(f'/api/v1/orders/{seed_order.id}',
                                 headers=auth_header(token))

        assert response.status_code == 403
