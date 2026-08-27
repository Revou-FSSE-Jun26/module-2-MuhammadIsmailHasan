from tests.conftest import get_auth_token, auth_header


class TestLogin:

    def test_login_success(self, client, seed_users):
        response = client.post('/api/v1/auth/login', json={
            'email': 'buyer@test.com',
            'password': 'password123'
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data['status'] is True
        assert data['message'] == 'login successful'
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['data']['email'] == 'buyer@test.com'
        assert data['data']['role'] == 'buyer'

    def test_login_wrong_password(self, client, seed_users):
        response = client.post('/api/v1/auth/login', json={
            'email': 'buyer@test.com',
            'password': 'wrongpassword'
        })
        data = response.get_json()

        assert response.status_code == 401
        assert data['message'] == 'invalid email or password'

    def test_login_nonexistent_email(self, client, seed_users):
        response = client.post('/api/v1/auth/login', json={
            'email': 'nobody@test.com',
            'password': 'password123'
        })

        assert response.status_code == 401
        assert response.get_json()['message'] == 'invalid email or password'

    def test_login_missing_email(self, client, seed_users):
        response = client.post('/api/v1/auth/login', json={
            'password': 'password123'
        })

        assert response.status_code == 422
        assert response.get_json()['message'] == 'email and password are required'

    def test_login_missing_password(self, client, seed_users):
        response = client.post('/api/v1/auth/login', json={
            'email': 'buyer@test.com'
        })

        assert response.status_code == 422
        assert response.get_json()['message'] == 'email and password are required'

    def test_login_empty_body(self, client, seed_users):
        response = client.post('/api/v1/auth/login',
                               data='',
                               content_type='application/json')

        assert response.status_code == 422

    def test_login_inactive_user(self, client, seed_users, db):
        user = seed_users['buyer']
        user.is_active = False
        db.session.commit()

        response = client.post('/api/v1/auth/login', json={
            'email': 'buyer@test.com',
            'password': 'password123'
        })

        assert response.status_code == 401


class TestRefresh:

    def test_refresh_success(self, client, seed_users):
        login_resp = client.post('/api/v1/auth/login', json={
            'email': 'buyer@test.com',
            'password': 'password123'
        })
        refresh_token = login_resp.get_json()['refresh_token']

        response = client.post('/api/v1/auth/refresh',
                               headers=auth_header(refresh_token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['status'] is True
        assert 'access_token' in data

    def test_refresh_with_access_token_fails(self, client, seed_users):
        access_token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.post('/api/v1/auth/refresh',
                               headers=auth_header(access_token))

        assert response.status_code == 422

    def test_refresh_no_token(self, client):
        response = client.post('/api/v1/auth/refresh')

        assert response.status_code == 401
