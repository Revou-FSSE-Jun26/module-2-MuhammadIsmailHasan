from app.models.user_addresses import UserAddress
from tests.conftest import get_auth_token, auth_header


def _buyer_token(client):
    return get_auth_token(client, 'buyer@test.com', 'password123')


def _seller_token(client):
    return get_auth_token(client, 'seller@test.com', 'password123')


def _valid_address(**overrides):
    payload = {
        'label': 'Home',
        'recipient_name': 'Buyer One',
        'phone': '+628123456789',
        'address_line': 'Jl. Mawar No. 1',
        'city': 'Jakarta',
        'postal_code': '10110',
    }
    payload.update(overrides)
    return payload


def _create(client, token, **overrides):
    return client.post('/api/v1/addresses', json=_valid_address(**overrides),
                       headers=auth_header(token))


class TestCreateAddress:

    def test_first_address_is_default(self, client, db, seed_users):
        UserAddress.query.filter_by(user_id=seed_users['buyer'].id).delete()
        db.session.commit()

        token = _buyer_token(client)
        response = _create(client, token)
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['is_default'] is True

    def test_second_address_not_default(self, client, seed_users):
        token = _buyer_token(client)
        _create(client, token)
        response = _create(client, token, label='Office')
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['is_default'] is False

    def test_missing_required_field_returns_422(self, client, seed_users):
        token = _buyer_token(client)
        response = client.post('/api/v1/addresses', json={'label': 'Home'},
                               headers=auth_header(token))
        assert response.status_code == 422

    def test_seller_cannot_create_address(self, client, seed_users):
        token = _seller_token(client)
        response = _create(client, token)
        assert response.status_code == 403


class TestListAndGet:

    def test_list_addresses(self, client, db, seed_users):
        UserAddress.query.filter_by(user_id=seed_users['buyer'].id).delete()
        db.session.commit()

        token = _buyer_token(client)
        _create(client, token)
        _create(client, token, label='Office')

        response = client.get('/api/v1/addresses', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert len(data['data']) == 2
        assert data['data'][0]['is_default'] is True

    def test_get_single_address(self, client, seed_users):
        token = _buyer_token(client)
        created = _create(client, token).get_json()['data']

        response = client.get(f"/api/v1/addresses/{created['id']}",
                              headers=auth_header(token))
        assert response.status_code == 200
        assert response.get_json()['data']['id'] == created['id']

    def test_get_missing_returns_404(self, client, seed_users):
        token = _buyer_token(client)
        response = client.get('/api/v1/addresses/999', headers=auth_header(token))
        assert response.status_code == 404


class TestSetDefault:

    def test_set_default_switches_default(self, client, seed_users):
        token = _buyer_token(client)
        first = _create(client, token).get_json()['data']
        second = _create(client, token, label='Office').get_json()['data']

        response = client.put(f"/api/v1/addresses/{second['id']}/default",
                              headers=auth_header(token))
        assert response.status_code == 200
        assert response.get_json()['data']['is_default'] is True

        listing = client.get('/api/v1/addresses',
                             headers=auth_header(token)).get_json()['data']
        by_id = {a['id']: a for a in listing}
        assert by_id[first['id']]['is_default'] is False
        assert by_id[second['id']]['is_default'] is True

    def test_exactly_one_default_after_switch(self, client, seed_users):
        token = _buyer_token(client)
        _create(client, token)
        second = _create(client, token, label='Office').get_json()['data']
        client.put(f"/api/v1/addresses/{second['id']}/default",
                   headers=auth_header(token))

        listing = client.get('/api/v1/addresses',
                             headers=auth_header(token)).get_json()['data']
        defaults = [a for a in listing if a['is_default']]
        assert len(defaults) == 1


class TestDeleteAddress:

    def test_delete_non_default(self, client, seed_users):
        token = _buyer_token(client)
        _create(client, token)
        second = _create(client, token, label='Office').get_json()['data']

        response = client.delete(f"/api/v1/addresses/{second['id']}",
                                 headers=auth_header(token))
        assert response.status_code == 200

    def test_cannot_delete_default_with_others(self, client, db, seed_users):
        UserAddress.query.filter_by(user_id=seed_users['buyer'].id).delete()
        db.session.commit()

        token = _buyer_token(client)
        first = _create(client, token).get_json()['data']
        _create(client, token, label='Office')

        response = client.delete(f"/api/v1/addresses/{first['id']}",
                                 headers=auth_header(token))
        assert response.status_code == 409

    def test_can_delete_last_default(self, client, db, seed_users):
        UserAddress.query.filter_by(user_id=seed_users['buyer'].id).delete()
        db.session.commit()

        token = _buyer_token(client)
        only = _create(client, token).get_json()['data']

        response = client.delete(f"/api/v1/addresses/{only['id']}",
                                 headers=auth_header(token))
        assert response.status_code == 200
