from tests.conftest import get_auth_token, auth_header

URL_EMAIL = '/api/v1/users/me/email'
URL_PASSWORD = '/api/v1/users/me/password'


class TestChangeEmail:

    def test_success(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.put(
            URL_EMAIL,
            json={'email': 'new@test.com', 'current_password': 'password123'},
            headers=auth_header(token),
        )

        assert response.status_code == 200
        assert response.get_json()['data']['email'] == 'new@test.com'
        assert get_auth_token(client, 'new@test.com', 'password123')

    def test_wrong_password(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.put(
            URL_EMAIL,
            json={'email': 'new@test.com', 'current_password': 'wrong'},
            headers=auth_header(token),
        )

        assert response.status_code == 400

    def test_duplicate_email(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.put(
            URL_EMAIL,
            json={'email': 'seller@test.com', 'current_password': 'password123'},
            headers=auth_header(token),
        )

        assert response.status_code == 409

    def test_invalid_format(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.put(
            URL_EMAIL,
            json={'email': 'not-an-email', 'current_password': 'password123'},
            headers=auth_header(token),
        )

        assert response.status_code == 422

    def test_requires_login(self, client, seed_users):
        response = client.put(
            URL_EMAIL,
            json={'email': 'new@test.com', 'current_password': 'password123'},
        )

        assert response.status_code == 401


class TestChangePassword:

    def test_success(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.put(
            URL_PASSWORD,
            json={'current_password': 'password123', 'new_password': 'newpass456'},
            headers=auth_header(token),
        )

        assert response.status_code == 200
        assert get_auth_token(client, 'buyer@test.com', 'newpass456')
        assert get_auth_token(client, 'buyer@test.com', 'password123') is None

    def test_wrong_current_password(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.put(
            URL_PASSWORD,
            json={'current_password': 'wrong', 'new_password': 'newpass456'},
            headers=auth_header(token),
        )

        assert response.status_code == 400

    def test_same_password(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.put(
            URL_PASSWORD,
            json={'current_password': 'password123', 'new_password': 'password123'},
            headers=auth_header(token),
        )

        assert response.status_code == 422

    def test_too_short(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.put(
            URL_PASSWORD,
            json={'current_password': 'password123', 'new_password': 'abc'},
            headers=auth_header(token),
        )

        assert response.status_code == 422
