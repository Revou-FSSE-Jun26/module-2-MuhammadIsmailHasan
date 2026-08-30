from tests.conftest import get_auth_token, auth_header


def _buyer_token(client):
    return get_auth_token(client, 'buyer@test.com', 'password123')


def _seller_token(client):
    return get_auth_token(client, 'seller@test.com', 'password123')


class TestGetProfile:

    def test_get_profile_before_creation_returns_404(self, client, seed_users):
        token = _buyer_token(client)
        response = client.get('/api/v1/profile', headers=auth_header(token))
        assert response.status_code == 404

    def test_get_profile_requires_auth(self, client):
        response = client.get('/api/v1/profile')
        assert response.status_code == 401


class TestUpsertProfile:

    def test_put_creates_profile(self, client, seed_users):
        token = _buyer_token(client)
        response = client.put('/api/v1/profile', json={
            'full_name': 'Buyer One',
            'phone': '+628123456789',
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['status'] is True
        assert data['data']['full_name'] == 'Buyer One'
        assert data['data']['phone'] == '+628123456789'

    def test_put_then_get_returns_saved_profile(self, client, seed_users):
        token = _buyer_token(client)
        client.put('/api/v1/profile', json={'full_name': 'Buyer One'},
                   headers=auth_header(token))

        response = client.get('/api/v1/profile', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['full_name'] == 'Buyer One'

    def test_put_twice_updates_same_profile(self, client, seed_users):
        token = _buyer_token(client)
        client.put('/api/v1/profile', json={'full_name': 'First'},
                   headers=auth_header(token))
        response = client.put('/api/v1/profile', json={'full_name': 'Second'},
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['full_name'] == 'Second'

    def test_profile_available_for_seller(self, client, seed_users):
        token = _seller_token(client)
        response = client.put('/api/v1/profile', json={'full_name': 'Seller One'},
                              headers=auth_header(token))
        assert response.status_code == 200
