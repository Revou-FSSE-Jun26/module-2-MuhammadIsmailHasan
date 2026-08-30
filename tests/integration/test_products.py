from tests.conftest import get_auth_token, auth_header


class TestGetProducts:

    def test_get_products_success(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/products/', headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['status'] is True
        assert len(data['data']) == 2
        assert 'pagination' in data
        assert data['pagination']['total_items'] == 2

    def test_get_products_filter_by_name(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/products/?name=laptop',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert len(data['data']) == 1
        assert data['data'][0]['name'] == 'Laptop'

    def test_get_products_filter_by_price_range(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/products/?min_price=100&max_price=2000',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert len(data['data']) == 1

    def test_get_products_filter_by_seller(self, client, seed_users, seed_products, db):
        from app.models.products import Product

        seller2_product = Product(
            name='Seller2 Gadget',
            slug='seller2-gadget',
            price=25.0,
            stock=5,
            seller_id=seed_users['seller2'].id,
        )
        db.session.add(seller2_product)
        db.session.commit()

        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get(
            f'/api/v1/products/?seller_id={seed_users["seller"].id}',
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert len(data['data']) == 2
        returned_ids = {p['id'] for p in data['data']}
        assert seller2_product.id not in returned_ids

    def test_get_products_filter_by_seller_no_match(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/products/?seller_id=999999',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert len(data['data']) == 0

    def test_get_products_no_auth(self, client):
        response = client.get('/api/v1/products/')
        assert response.status_code == 401


class TestCreateProduct:

    def test_create_product_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/products/', json={
            'name': 'New Phone',
            'price': 599.99,
            'stock': 25,
            'category_id': seed_categories[0].id
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['name'] == 'New Phone'
        assert data['data']['price'] == 599.99
        assert data['data']['stock'] == 25
        assert data['data']['slug'] == 'new-phone'

    def test_create_product_sets_seller_id(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        create = client.post('/api/v1/products/', json={
            'name': 'Owned Phone',
            'price': 100,
            'stock': 5,
            'category_id': seed_categories[0].id
        }, headers=auth_header(token))
        product_id = create.get_json()['data']['id']

        detail = client.get(f'/api/v1/products/{product_id}',
                            headers=auth_header(token))
        data = detail.get_json()['data']

        assert 'seller_id' in data
        assert data['seller_id'] == seed_users['seller'].id

    def test_create_product_buyer_forbidden(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.post('/api/v1/products/', json={
            'name': 'Hack Product',
            'price': 1,
            'stock': 1
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_create_product_missing_name(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/products/', json={
            'price': 10,
            'stock': 5
        }, headers=auth_header(token))

        assert response.status_code == 422
        assert response.get_json()['message'] == 'name is required'

    def test_create_product_negative_price(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/products/', json={
            'name': 'Bad Product',
            'price': -50,
            'stock': 5
        }, headers=auth_header(token))

        assert response.status_code == 422

    def test_create_product_empty_body(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/products/',
                               data='',
                               content_type='application/json',
                               headers=auth_header(token))

        assert response.status_code == 422


class TestGetProduct:

    def test_get_product_success(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        product = seed_products[0]

        response = client.get(f'/api/v1/products/{product.id}',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['name'] == 'Laptop'
        assert 'category' in data['data']

    def test_get_product_not_found(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/products/9999',
                              headers=auth_header(token))

        assert response.status_code == 404

    def test_get_deleted_product(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        product.is_active = False
        db.session.commit()

        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.get(f'/api/v1/products/{product.id}',
                              headers=auth_header(token))

        assert response.status_code == 404


class TestGetProductBySlug:

    def test_get_by_slug_success(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/products/slug/laptop',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['name'] == 'Laptop'
        assert data['data']['slug'] == 'laptop'

    def test_get_by_slug_not_found(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/products/slug/does-not-exist',
                              headers=auth_header(token))

        assert response.status_code == 404

    def test_get_by_slug_deleted_product(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        product.is_active = False
        db.session.commit()

        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.get('/api/v1/products/slug/laptop',
                              headers=auth_header(token))

        assert response.status_code == 404

    def test_duplicate_name_gets_unique_slug(self, client, seed_users, seed_categories):
        token = get_auth_token(client, 'seller@test.com', 'password123')
        payload = {'name': 'Gadget X', 'price': 10, 'stock': 5}

        first = client.post('/api/v1/products/', json=payload, headers=auth_header(token))
        second = client.post('/api/v1/products/', json=payload, headers=auth_header(token))

        slug1 = first.get_json()['data']['slug']
        slug2 = second.get_json()['data']['slug']

        assert slug1 == 'gadget-x'
        assert slug2 == 'gadget-x-2'
        assert slug1 != slug2


class TestUpdateProduct:

    def test_update_product_success(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'seller@test.com', 'password123')
        product = seed_products[0]

        response = client.put(f'/api/v1/products/{product.id}', json={
            'name': 'Updated Laptop',
            'price': 1299.99
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['name'] == 'Updated Laptop'
        assert data['data']['price'] == 1299.99

    def test_update_product_partial(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'seller@test.com', 'password123')
        product = seed_products[0]

        response = client.put(f'/api/v1/products/{product.id}', json={
            'stock': 99
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['stock'] == 99

    def test_update_product_not_found(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put('/api/v1/products/9999', json={
            'name': 'Ghost'
        }, headers=auth_header(token))

        assert response.status_code == 404

    def test_update_product_buyer_forbidden(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        product = seed_products[0]

        response = client.put(f'/api/v1/products/{product.id}', json={
            'price': 1
        }, headers=auth_header(token))

        assert response.status_code == 403


class TestDeleteProduct:

    def test_delete_product_success(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'seller@test.com', 'password123')
        product = seed_products[0]

        response = client.delete(f'/api/v1/products/{product.id}',
                                 headers=auth_header(token))

        assert response.status_code == 200
        assert response.get_json()['message'] == 'success delete product'

    def test_delete_product_not_found(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.delete('/api/v1/products/9999',
                                 headers=auth_header(token))

        assert response.status_code == 404

    def test_delete_product_buyer_forbidden(self, client, seed_users, seed_products):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        product = seed_products[0]

        response = client.delete(f'/api/v1/products/{product.id}',
                                 headers=auth_header(token))

        assert response.status_code == 403

    def test_delete_product_with_active_order(self, client, seed_users, seed_products, db):
        from app.models.orders import Order, OrderItem

        product = seed_products[0]
        buyer = seed_users['buyer']

        order = Order(user_id=buyer.id, total_amount=999.99, status='processing')
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
        db.session.commit()

        token = get_auth_token(client, 'seller@test.com', 'password123')
        response = client.delete(f'/api/v1/products/{product.id}',
                                 headers=auth_header(token))

        assert response.status_code == 400
        assert 'active orders' in response.get_json()['message']
