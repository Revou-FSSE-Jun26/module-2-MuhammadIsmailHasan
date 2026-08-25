from tests.conftest import get_auth_token, auth_header


class TestGetCategories:

    def test_get_categories_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/categories/', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['status'] is True
        assert len(data['data']) == 2
        assert data['pagination']['total_items'] == 2

    def test_get_categories_with_products(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/categories/?with_products=true',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        has_products = any('products' in cat for cat in data['data'])
        assert has_products is True

    def test_get_categories_filter_by_name(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/categories/?name=elec',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert len(data['data']) == 1
        assert data['data'][0]['name'] == 'Electronics'

    def test_get_categories_no_auth(self, client):
        response = client.get('/api/v1/categories/')
        assert response.status_code == 401


class TestCreateCategory:

    def test_create_category_success(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/categories/', json={
            'name': 'Books'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['name'] == 'Books'

    def test_create_category_duplicate_name(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/categories/', json={
            'name': 'Electronics'
        }, headers=auth_header(token))

        assert response.status_code == 409
        assert response.get_json()['message'] == 'category name already exists'

    def test_create_category_missing_name(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/categories/', json={'name': None},
                               headers=auth_header(token))

        assert response.status_code == 400
        assert response.get_json()['message'] == 'name is required'

    def test_create_category_empty_name(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/categories/', json={'name': ''},
                               headers=auth_header(token))

        assert response.status_code == 400

    def test_create_category_buyer_forbidden(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.post('/api/v1/categories/', json={'name': 'Hack'},
                               headers=auth_header(token))

        assert response.status_code == 403


class TestGetCategory:

    def test_get_category_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        category = seed_categories[0]

        response = client.get(f'/api/v1/categories/{category.id}',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['name'] == 'Electronics'

    def test_get_category_not_found(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/categories/9999',
                              headers=auth_header(token))

        assert response.status_code == 404


class TestUpdateCategory:

    def test_update_category_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'seller@test.com', 'password123')
        category = seed_categories[0]

        response = client.put(f'/api/v1/categories/{category.id}', json={
            'name': 'Tech & Gadgets'
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['name'] == 'Tech & Gadgets'

    def test_update_category_duplicate_name(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'seller@test.com', 'password123')
        category = seed_categories[0]

        response = client.put(f'/api/v1/categories/{category.id}', json={
            'name': 'Clothing'
        }, headers=auth_header(token))

        assert response.status_code == 409
        assert response.get_json()['message'] == 'category name already exists'

    def test_update_category_not_found(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put('/api/v1/categories/9999', json={
            'name': 'Ghost'
        }, headers=auth_header(token))

        assert response.status_code == 404

    def test_update_category_buyer_forbidden(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        category = seed_categories[0]

        response = client.put(f'/api/v1/categories/{category.id}', json={
            'name': 'Hacked'
        }, headers=auth_header(token))

        assert response.status_code == 403


class TestDeleteCategory:

    def test_delete_category_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'seller@test.com', 'password123')
        category = seed_categories[0]

        response = client.delete(f'/api/v1/categories/{category.id}',
                                 headers=auth_header(token))

        assert response.status_code == 200
        assert response.get_json()['message'] == 'success delete category'

    def test_delete_category_not_found(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.delete('/api/v1/categories/9999',
                                 headers=auth_header(token))

        assert response.status_code == 404

    def test_delete_category_buyer_forbidden(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        category = seed_categories[0]

        response = client.delete(f'/api/v1/categories/{category.id}',
                                 headers=auth_header(token))

        assert response.status_code == 403
