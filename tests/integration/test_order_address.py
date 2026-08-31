import pytest

from app.models.user_addresses import UserAddress
from app.models.orders import Order
from tests.conftest import get_auth_token, auth_header


def _buyer_token(client):
    return get_auth_token(client, 'buyer@test.com', 'password123')


def _place_order(client, token, product, quantity=1, address_id=None):
    body = {'items': [{'product_id': product.id, 'quantity': quantity}]}
    if address_id is not None:
        body['address_id'] = address_id
    return client.post('/api/v1/orders/', json=body, headers=auth_header(token))


def _add_address(client, token, **overrides):
    payload = {
        'recipient_name': 'Buyer Test',
        'phone': '+628000',
        'address_line': 'Jl. Second No. 2',
        'city': 'Bandung',
        'postal_code': '40111',
    }
    payload.update(overrides)
    return client.post('/api/v1/addresses', json=payload, headers=auth_header(token))


class TestOrderUsesDefaultAddress:

    def test_order_snapshots_default_address(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        response = _place_order(client, token, seed_products[0])
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['shipping_recipient_name'] == 'Buyer Test'
        assert data['data']['shipping_city'] == 'Jakarta'
        assert data['data']['shipping_address_line'] == 'Jl. Test No. 1'

    def test_order_with_explicit_address_id(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        second = _add_address(client, token).get_json()['data']

        response = _place_order(client, token, seed_products[0], address_id=second['id'])
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['shipping_city'] == 'Bandung'


class TestNoAddressRejected:

    def test_order_without_any_address_rejected(self, client, db, seed_products):
        from app.auth import hash_password
        from app.models.users import User

        user = User(
            username='noaddr', email='noaddr@test.com',
            password_hash=hash_password('password123'), role='buyer',
        )
        db.session.add(user)
        db.session.commit()

        token = get_auth_token(client, 'noaddr@test.com', 'password123')
        response = _place_order(client, token, seed_products[0])

        assert response.status_code == 422
        assert 'shipping address is required' in response.get_json()['message']


class TestAddressOwnership:

    def test_order_with_other_users_address_rejected(self, client, db, seed_users, seed_products):
        seller = seed_users['seller']
        foreign = UserAddress(
            user_id=seller.id, recipient_name='Seller', phone='1',
            address_line='X', city='Y', is_default=True,
        )
        db.session.add(foreign)
        db.session.commit()

        token = _buyer_token(client)
        response = _place_order(client, token, seed_products[0], address_id=foreign.id)

        assert response.status_code == 404


class TestChangeOrderAddress:

    def test_change_address_while_waiting(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        order = _place_order(client, token, seed_products[0]).get_json()['data']
        second = _add_address(client, token).get_json()['data']

        response = client.put(
            f"/api/v1/orders/{order['id']}/address",
            json={'address_id': second['id']},
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['shipping_city'] == 'Bandung'

    def test_change_address_blocked_once_processing(self, client, db, seed_users, seed_products):
        token = _buyer_token(client)
        order = _place_order(client, token, seed_products[0]).get_json()['data']
        second = _add_address(client, token).get_json()['data']

        db_order = db.session.get(Order, order['id'])
        db_order.status = 'processing'
        db.session.commit()

        response = client.put(
            f"/api/v1/orders/{order['id']}/address",
            json={'address_id': second['id']},
            headers=auth_header(token),
        )

        assert response.status_code == 409
        assert 'can no longer be changed' in response.get_json()['message']

    def test_change_address_not_owner(self, client, db, seed_users, seed_products):
        token = _buyer_token(client)
        order = _place_order(client, token, seed_products[0]).get_json()['data']

        from app.auth import hash_password
        from app.models.users import User
        other = User(
            username='buyer2', email='buyer2@test.com',
            password_hash=hash_password('password123'), role='buyer',
        )
        db.session.add(other)
        db.session.commit()
        other_addr = UserAddress(
            user_id=other.id, recipient_name='Other', phone='1',
            address_line='X', city='Y', is_default=True,
        )
        db.session.add(other_addr)
        db.session.commit()

        other_token = get_auth_token(client, 'buyer2@test.com', 'password123')
        response = client.put(
            f"/api/v1/orders/{order['id']}/address",
            json={'address_id': other_addr.id},
            headers=auth_header(other_token),
        )

        assert response.status_code == 403

    def test_seller_cannot_change_address(self, client, seed_users, seed_products):
        token = _buyer_token(client)
        order = _place_order(client, token, seed_products[0]).get_json()['data']

        seller_token = get_auth_token(client, 'seller@test.com', 'password123')
        response = client.put(
            f"/api/v1/orders/{order['id']}/address",
            json={'address_id': 1},
            headers=auth_header(seller_token),
        )

        assert response.status_code == 403


class TestSnapshotImmutability:

    def test_editing_address_book_does_not_change_past_order(self, client, db, seed_users, seed_products):
        token = _buyer_token(client)
        order = _place_order(client, token, seed_products[0]).get_json()['data']
        original_city = order['shipping_city']

        default = UserAddress.query.filter_by(
            user_id=seed_users['buyer'].id, is_default=True
        ).first()
        client.put(
            f"/api/v1/addresses/{default.id}",
            json={'city': 'Surabaya'},
            headers=auth_header(token),
        )

        fetched = client.get(
            f"/api/v1/orders/{order['id']}", headers=auth_header(token)
        ).get_json()['data']

        assert fetched['shipping_city'] == original_city
        assert fetched['shipping_city'] != 'Surabaya'


class TestOrderingIsBuyerOnly:

    def test_admin_cannot_create_order(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'admin@test.com', 'password123')
        response = _place_order(client, token, seed_products[0])
        assert response.status_code == 403
