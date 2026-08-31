from tests.conftest import get_auth_token, auth_header


def _make_image(db, product_id, url, order, is_active=True):
    from app.models.product_images import ProductImage
    image = ProductImage(product_id=product_id, url=url, order=order, is_active=is_active)
    db.session.add(image)
    db.session.commit()
    return image


class TestListProductImages:

    def test_list_images_ordered_by_order_asc(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        _make_image(db, product.id, 'http://img/c.jpg', order=2)
        _make_image(db, product.id, 'http://img/a.jpg', order=0)
        _make_image(db, product.id, 'http://img/b.jpg', order=1)

        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.get(f'/api/v1/products/{product.id}/images/',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert [img['order'] for img in data['data']] == [0, 1, 2]
        assert data['data'][0]['url'] == 'http://img/a.jpg'

    def test_list_excludes_inactive(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        _make_image(db, product.id, 'http://img/active.jpg', order=0)
        _make_image(db, product.id, 'http://img/deleted.jpg', order=1, is_active=False)

        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.get(f'/api/v1/products/{product.id}/images/',
                              headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert len(data['data']) == 1

    def test_list_product_not_found(self, client, seed_users):
        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.get('/api/v1/products/9999/images/',
                              headers=auth_header(token))
        assert response.status_code == 404

    def test_list_no_auth(self, client, seed_products):
        product = seed_products[0]
        response = client.get(f'/api/v1/products/{product.id}/images/')
        assert response.status_code == 401


class TestCreateProductImage:

    def test_seller_owner_can_create(self, client, seed_users, seed_products):
        product = seed_products[0]
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post(f'/api/v1/products/{product.id}/images/', json={
            'url': 'http://img/new.jpg',
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 201
        assert data['data']['url'] == 'http://img/new.jpg'
        assert data['data']['order'] == 0
        assert data['data']['product_id'] == product.id

    def test_create_auto_appends_order(self, client, seed_users, seed_products):
        product = seed_products[0]
        token = get_auth_token(client, 'seller@test.com', 'password123')

        first = client.post(f'/api/v1/products/{product.id}/images/', json={
            'url': 'http://img/1.jpg',
        }, headers=auth_header(token)).get_json()
        second = client.post(f'/api/v1/products/{product.id}/images/', json={
            'url': 'http://img/2.jpg',
        }, headers=auth_header(token)).get_json()
        third = client.post(f'/api/v1/products/{product.id}/images/', json={
            'url': 'http://img/3.jpg',
        }, headers=auth_header(token)).get_json()

        assert first['data']['order'] == 0
        assert second['data']['order'] == 1
        assert third['data']['order'] == 2

    def test_create_rejects_client_supplied_order(self, client, seed_users, seed_products):
        product = seed_products[0]
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post(f'/api/v1/products/{product.id}/images/', json={
            'url': 'http://img/new.jpg',
            'order': 99,
        }, headers=auth_header(token))

        # order is server-managed; it is not an accepted input field
        assert response.status_code == 422

    def test_admin_can_create(self, client, seed_users, seed_products):
        product = seed_products[0]
        token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.post(f'/api/v1/products/{product.id}/images/', json={
            'url': 'http://img/admin.jpg',
        }, headers=auth_header(token))

        assert response.status_code == 201
        assert response.get_json()['data']['order'] == 0

    def test_seller_non_owner_forbidden(self, client, seed_users, seed_products):
        product = seed_products[0]
        token = get_auth_token(client, 'seller2@test.com', 'password123')

        response = client.post(f'/api/v1/products/{product.id}/images/', json={
            'url': 'http://img/hack.jpg',
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_buyer_forbidden(self, client, seed_users, seed_products):
        product = seed_products[0]
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.post(f'/api/v1/products/{product.id}/images/', json={
            'url': 'http://img/hack.jpg',
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_create_missing_url(self, client, seed_users, seed_products):
        product = seed_products[0]
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post(f'/api/v1/products/{product.id}/images/', json={
            'order': 1,
        }, headers=auth_header(token))

        assert response.status_code == 422
        assert response.get_json()['message'] == 'url is required'

    def test_create_product_not_found(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.post('/api/v1/products/9999/images/', json={
            'url': 'http://img/x.jpg',
        }, headers=auth_header(token))

        assert response.status_code == 404


class TestUpdateProductImage:

    def test_seller_owner_can_update_url(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        image = _make_image(db, product.id, 'http://img/old.jpg', order=0)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/{image.id}', json={
            'url': 'http://img/updated.jpg',
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data['data']['url'] == 'http://img/updated.jpg'

    def test_update_rejects_order_field(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        image = _make_image(db, product.id, 'http://img/old.jpg', order=2)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/{image.id}', json={
            'url': 'http://img/new.jpg',
            'order': 9,
        }, headers=auth_header(token))

        # order is server-managed; it is not an accepted input field
        assert response.status_code == 422

    def test_seller_non_owner_forbidden(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        image = _make_image(db, product.id, 'http://img/old.jpg', order=0)
        token = get_auth_token(client, 'seller2@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/{image.id}', json={
            'url': 'http://img/hack.jpg',
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_update_image_not_found(self, client, seed_users, seed_products):
        product = seed_products[0]
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/9999', json={
            'url': 'http://img/x.jpg',
        }, headers=auth_header(token))

        assert response.status_code == 404


class TestDeleteProductImage:

    def test_seller_owner_can_delete(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        image = _make_image(db, product.id, 'http://img/x.jpg', order=0)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.delete(f'/api/v1/products/{product.id}/images/{image.id}',
                                 headers=auth_header(token))

        assert response.status_code == 200
        assert response.get_json()['message'] == 'success delete product image'

    def test_admin_can_delete(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        image = _make_image(db, product.id, 'http://img/x.jpg', order=0)
        token = get_auth_token(client, 'admin@test.com', 'password123')

        response = client.delete(f'/api/v1/products/{product.id}/images/{image.id}',
                                 headers=auth_header(token))

        assert response.status_code == 200

    def test_deleted_image_excluded_from_list(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        image = _make_image(db, product.id, 'http://img/x.jpg', order=0)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        client.delete(f'/api/v1/products/{product.id}/images/{image.id}',
                      headers=auth_header(token))

        listing = client.get(f'/api/v1/products/{product.id}/images/',
                             headers=auth_header(token))
        assert len(listing.get_json()['data']) == 0

    def test_seller_non_owner_forbidden(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        image = _make_image(db, product.id, 'http://img/x.jpg', order=0)
        token = get_auth_token(client, 'seller2@test.com', 'password123')

        response = client.delete(f'/api/v1/products/{product.id}/images/{image.id}',
                                 headers=auth_header(token))

        assert response.status_code == 403

    def test_delete_image_not_found(self, client, seed_users, seed_products):
        product = seed_products[0]
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.delete(f'/api/v1/products/{product.id}/images/9999',
                                 headers=auth_header(token))

        assert response.status_code == 404


class TestProductResponseImageFields:

    def test_get_all_returns_primary_image_smallest_order(
        self, client, seed_users, seed_products, db
    ):
        product = seed_products[0]
        _make_image(db, product.id, 'http://img/second.jpg', order=5)
        _make_image(db, product.id, 'http://img/primary.jpg', order=1)

        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.get('/api/v1/products/', headers=auth_header(token))
        data = response.get_json()

        target = next(p for p in data['data'] if p['id'] == product.id)
        assert target['image'] == 'http://img/primary.jpg'

    def test_get_all_image_null_when_no_images(self, client, seed_users, seed_products):
        product = seed_products[1]
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.get('/api/v1/products/', headers=auth_header(token))
        data = response.get_json()

        target = next(p for p in data['data'] if p['id'] == product.id)
        assert target['image'] is None

    def test_get_by_id_returns_all_images_ordered_asc(
        self, client, seed_users, seed_products, db
    ):
        product = seed_products[0]
        _make_image(db, product.id, 'http://img/c.jpg', order=2)
        _make_image(db, product.id, 'http://img/a.jpg', order=0)
        _make_image(db, product.id, 'http://img/b.jpg', order=1)

        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.get(f'/api/v1/products/{product.id}',
                              headers=auth_header(token))
        data = response.get_json()['data']

        assert 'images' in data
        assert [img['order'] for img in data['images']] == [0, 1, 2]
        assert data['images'][0]['url'] == 'http://img/a.jpg'

    def test_get_by_id_excludes_inactive_images(
        self, client, seed_users, seed_products, db
    ):
        product = seed_products[0]
        _make_image(db, product.id, 'http://img/active.jpg', order=0)
        _make_image(db, product.id, 'http://img/deleted.jpg', order=1, is_active=False)

        token = get_auth_token(client, 'buyer@test.com', 'password123')
        response = client.get(f'/api/v1/products/{product.id}',
                              headers=auth_header(token))
        data = response.get_json()['data']

        assert len(data['images']) == 1
        assert data['images'][0]['url'] == 'http://img/active.jpg'


class TestReorderProductImages:

    def _three_images(self, db, product_id):
        a = _make_image(db, product_id, 'http://img/a.jpg', order=0)
        b = _make_image(db, product_id, 'http://img/b.jpg', order=1)
        c = _make_image(db, product_id, 'http://img/c.jpg', order=2)
        return a, b, c

    def test_reorder_success(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        a, b, c = self._three_images(db, product.id)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/reorder', json={
            'image_ids': [c.id, a.id, b.id],
        }, headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        result = {img['id']: img['order'] for img in data['data']}
        assert result[c.id] == 0
        assert result[a.id] == 1
        assert result[b.id] == 2

    def test_reorder_reflected_in_listing(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        a, b, c = self._three_images(db, product.id)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        client.put(f'/api/v1/products/{product.id}/images/reorder', json={
            'image_ids': [c.id, b.id, a.id],
        }, headers=auth_header(token))

        listing = client.get(f'/api/v1/products/{product.id}/images/',
                             headers=auth_header(token)).get_json()['data']
        assert [img['id'] for img in listing] == [c.id, b.id, a.id]

    def test_reorder_missing_id_rejected(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        a, b, c = self._three_images(db, product.id)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/reorder', json={
            'image_ids': [a.id, b.id],
        }, headers=auth_header(token))

        assert response.status_code == 422

    def test_reorder_extra_id_rejected(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        a, b, c = self._three_images(db, product.id)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/reorder', json={
            'image_ids': [a.id, b.id, c.id, 9999],
        }, headers=auth_header(token))

        assert response.status_code == 422

    def test_reorder_duplicate_id_rejected(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        a, b, c = self._three_images(db, product.id)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/reorder', json={
            'image_ids': [a.id, a.id, b.id],
        }, headers=auth_header(token))

        assert response.status_code == 422

    def test_reorder_empty_rejected(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        self._three_images(db, product.id)
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/reorder', json={
            'image_ids': [],
        }, headers=auth_header(token))

        assert response.status_code == 422

    def test_reorder_seller_non_owner_forbidden(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        a, b, c = self._three_images(db, product.id)
        token = get_auth_token(client, 'seller2@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/reorder', json={
            'image_ids': [c.id, b.id, a.id],
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_reorder_buyer_forbidden(self, client, seed_users, seed_products, db):
        product = seed_products[0]
        a, b, c = self._three_images(db, product.id)
        token = get_auth_token(client, 'buyer@test.com', 'password123')

        response = client.put(f'/api/v1/products/{product.id}/images/reorder', json={
            'image_ids': [c.id, b.id, a.id],
        }, headers=auth_header(token))

        assert response.status_code == 403

    def test_reorder_product_not_found(self, client, seed_users):
        token = get_auth_token(client, 'seller@test.com', 'password123')

        response = client.put('/api/v1/products/9999/images/reorder', json={
            'image_ids': [1, 2],
        }, headers=auth_header(token))

        assert response.status_code == 404
