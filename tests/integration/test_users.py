from tests.conftest import get_auth_token, auth_header


class TestRegisterUser:

    def test_register_success(self, client, db):
        response = client.post('/api/v1/users/', json={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'securepass',
            'role': 'buyer'
        })
        data = response.get_json()

        assert response.status_code == 201
        assert data['status'] is True
        assert data['data']['username'] == 'newuser'
        assert data['data']['email'] == 'new@test.com'
        assert data['data']['role'] == 'buyer'
        assert 'password' not in data['data']
        assert 'password_hash' not in data['data']

    def test_register_duplicate_username(self, client, seed_users):
        response = client.post('/api/v1/users/', json={
            'username': 'buyer_test',
            'email': 'different@test.com',
            'password': 'pass123',
            'role': 'buyer'
        })

        assert response.status_code == 409
        assert 'username already exists' in response.get_json()['message']

    def test_register_duplicate_email(self, client, seed_users):
        response = client.post('/api/v1/users/', json={
            'username': 'differentuser',
            'email': 'buyer@test.com',
            'password': 'pass123',
            'role': 'buyer'
        })

        assert response.status_code == 409
        assert 'email already exists' in response.get_json()['message']

    def test_register_missing_fields(self, client, db):
        response = client.post('/api/v1/users/', json={
            'username': 'test'
        })

        assert response.status_code == 422

    def test_register_invalid_email(self, client, db):
        response = client.post('/api/v1/users/', json={
            'username': 'test',
            'email': 'not-an-email',
            'password': 'pass123',
            'role': 'buyer'
        })

        assert response.status_code == 422
        assert response.get_json()['message'] == 'invalid email format'

    def test_register_invalid_role(self, client, db):
        response = client.post('/api/v1/users/', json={
            'username': 'test',
            'email': 'test@test.com',
            'password': 'pass123',
            'role': 'admin'
        })

        assert response.status_code == 422
        assert 'buyer or seller only' in response.get_json()['message']

    def test_register_empty_body(self, client, db):
        response = client.post('/api/v1/users/',
                               data='',
                               content_type='application/json')

        assert response.status_code == 422


class TestGetUserAccount:

    def test_get_me_success(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/users/me', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['email'] == 'buyer@test.com'
        assert data['data']['role'] == 'buyer'

    def test_get_me_no_token(self, client):
        response = client.get('/api/v1/users/me')

        assert response.status_code == 401


class TestGetUser:

    def test_get_user_by_id(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        seller = seed_users['seller']

        response = client.get(f'/api/v1/users/{seller.id}',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['username'] == 'seller_test'

    def test_get_user_not_found(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/users/9999',
                              headers=auth_header(token))

        assert response.status_code == 404

    def test_get_user_no_token(self, client):
        response = client.get('/api/v1/users/1')

        assert response.status_code == 401


class TestDeleteUser:

    def test_delete_own_account(self, client, seed_users):
        buyer = seed_users['buyer']
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/users/{buyer.id}',
                                 headers=auth_header(token))

        assert response.status_code == 200
        assert response.get_json()['message'] == 'success delete user'

    def test_admin_can_delete_others(self, client, seed_users):
        buyer = seed_users['buyer']
        admin_token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.delete(f'/api/v1/users/{buyer.id}',
                                 headers=auth_header(admin_token))

        assert response.status_code == 200

    def test_cannot_delete_other_user(self, client, seed_users):
        seller = seed_users['seller']
        buyer_token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.delete(f'/api/v1/users/{seller.id}',
                                 headers=auth_header(buyer_token))

        assert response.status_code == 403

    def test_delete_nonexistent_user(self, client, seed_users):
        admin_token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.delete('/api/v1/users/9999',
                                 headers=auth_header(admin_token))

        assert response.status_code == 404
