from tests.conftest import get_auth_token, auth_header


class TestGetSubCategories:
    def test_get_sub_categories_success(self, client, seed_users, seed_sub_categories):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get("/api/v1/sub-categories/", headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] is True
        assert len(data["data"]) == 2
        assert data["pagination"]["total_items"] == 2

    def test_get_sub_categories_filter_by_category_id(
        self, client, seed_users, seed_sub_categories, seed_categories
    ):
        token = get_auth_token(client, "buyer@test.com", "password123")
        electronics = seed_categories[0]

        response = client.get(
            f"/api/v1/sub-categories/?category_id={electronics.id}",
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Laptops"

    def test_get_sub_categories_public(self, client, seed_sub_categories):
        # the list endpoint is public (no auth required)
        response = client.get("/api/v1/sub-categories/")
        assert response.status_code == 200


class TestCreateSubCategory:
    def test_create_sub_category_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.post(
            "/api/v1/sub-categories/",
            json={
                "name": "Tablets",
                "category_id": seed_categories[0].id,
            },
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 201
        assert data["data"]["name"] == "Tablets"
        assert data["data"]["category_id"] == seed_categories[0].id

    def test_create_sub_category_duplicate_name(
        self, client, seed_users, seed_sub_categories, seed_categories
    ):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.post(
            "/api/v1/sub-categories/",
            json={
                "name": "Laptops",
                "category_id": seed_categories[0].id,
            },
            headers=auth_header(token),
        )

        assert response.status_code == 409
        assert response.get_json()["message"] == "sub category name already exists"

    def test_create_sub_category_parent_not_found(self, client, seed_users):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.post(
            "/api/v1/sub-categories/",
            json={
                "name": "Orphan",
                "category_id": 9999,
            },
            headers=auth_header(token),
        )

        assert response.status_code == 404

    def test_create_sub_category_buyer_forbidden(
        self, client, seed_users, seed_categories
    ):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.post(
            "/api/v1/sub-categories/",
            json={
                "name": "Hack",
                "category_id": seed_categories[0].id,
            },
            headers=auth_header(token),
        )

        assert response.status_code == 403

    def test_create_sub_category_missing_name(
        self, client, seed_users, seed_categories
    ):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.post(
            "/api/v1/sub-categories/",
            json={
                "category_id": seed_categories[0].id,
            },
            headers=auth_header(token),
        )

        assert response.status_code == 422


class TestGetSubCategory:
    def test_get_sub_category_success(self, client, seed_users, seed_sub_categories):
        token = get_auth_token(client, "buyer@test.com", "password123")
        sub_category = seed_sub_categories[0]

        response = client.get(
            f"/api/v1/sub-categories/{sub_category.id}", headers=auth_header(token)
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["data"]["name"] == "Laptops"
        assert data["data"]["category"]["name"] == "Electronics"

    def test_get_sub_category_not_found(self, client, seed_users):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get("/api/v1/sub-categories/9999", headers=auth_header(token))

        assert response.status_code == 404


class TestUpdateSubCategory:
    def test_update_sub_category_success(self, client, seed_users, seed_sub_categories):
        token = get_auth_token(client, "seller@test.com", "password123")
        sub_category = seed_sub_categories[0]

        response = client.put(
            f"/api/v1/sub-categories/{sub_category.id}",
            json={
                "name": "Notebooks",
            },
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["data"]["name"] == "Notebooks"

    def test_update_sub_category_duplicate_name(
        self, client, seed_users, seed_sub_categories
    ):
        token = get_auth_token(client, "seller@test.com", "password123")
        sub_category = seed_sub_categories[0]

        response = client.put(
            f"/api/v1/sub-categories/{sub_category.id}",
            json={
                "name": "Men",
            },
            headers=auth_header(token),
        )

        assert response.status_code == 409
        assert response.get_json()["message"] == "sub category name already exists"

    def test_update_sub_category_not_found(self, client, seed_users):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.put(
            "/api/v1/sub-categories/9999",
            json={
                "name": "Ghost",
            },
            headers=auth_header(token),
        )

        assert response.status_code == 404

    def test_update_sub_category_buyer_forbidden(
        self, client, seed_users, seed_sub_categories
    ):
        token = get_auth_token(client, "buyer@test.com", "password123")
        sub_category = seed_sub_categories[0]

        response = client.put(
            f"/api/v1/sub-categories/{sub_category.id}",
            json={
                "name": "Hacked",
            },
            headers=auth_header(token),
        )

        assert response.status_code == 403


class TestDeleteSubCategory:
    def test_delete_sub_category_success(self, client, seed_users, seed_sub_categories):
        token = get_auth_token(client, "seller@test.com", "password123")
        sub_category = seed_sub_categories[0]

        response = client.delete(
            f"/api/v1/sub-categories/{sub_category.id}", headers=auth_header(token)
        )

        assert response.status_code == 200
        assert response.get_json()["message"] == "success delete sub category"

    def test_delete_sub_category_not_found(self, client, seed_users):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.delete(
            "/api/v1/sub-categories/9999", headers=auth_header(token)
        )

        assert response.status_code == 404

    def test_delete_sub_category_buyer_forbidden(
        self, client, seed_users, seed_sub_categories
    ):
        token = get_auth_token(client, "buyer@test.com", "password123")
        sub_category = seed_sub_categories[0]

        response = client.delete(
            f"/api/v1/sub-categories/{sub_category.id}", headers=auth_header(token)
        )

        assert response.status_code == 403


class TestGetProductsBySubCategory:
    def test_get_products_by_sub_category(self, client, seed_users, seed_products):
        token = get_auth_token(client, "buyer@test.com", "password123")
        laptops_sub = seed_products[0].sub_category

        response = client.get(
            f"/api/v1/sub-categories/{laptops_sub.id}/products",
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] is True

        # nested shape: sub_category object with its products nested
        sub_category = data["data"]
        assert sub_category["name"] == "Laptops"
        assert sub_category["image"] == (
            "https://cdn.example.com/sub-categories/laptops.jpg"
        )
        assert len(sub_category["products"]) == 1

        product = sub_category["products"][0]
        assert product["name"] == "Laptop"
        assert set(product.keys()) == {"id", "image", "name", "price", "slug", "stock"}

    def test_get_products_by_sub_category_not_found(self, client, seed_users):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get(
            "/api/v1/sub-categories/9999/products", headers=auth_header(token)
        )

        assert response.status_code == 404


class TestGetSubCategoriesWithProducts:
    def test_get_sub_categories_with_products(self, client, seed_users, seed_products):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get(
            "/api/v1/sub-categories/products", headers=auth_header(token)
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] is True
        assert "pagination" in data
        assert all("products" in sub for sub in data["data"])

        laptops = next(sub for sub in data["data"] if sub["name"] == "Laptops")
        assert laptops["image"] == (
            "https://cdn.example.com/sub-categories/laptops.jpg"
        )
        assert len(laptops["products"]) == 1

        product = laptops["products"][0]
        assert product["name"] == "Laptop"
        assert set(product.keys()) == {"id", "image", "name", "price", "slug", "stock"}

    def test_get_sub_categories_with_products_filter_by_category_id(
        self, client, seed_users, seed_products
    ):
        token = get_auth_token(client, "buyer@test.com", "password123")
        electronics = seed_products[0].sub_category.category

        response = client.get(
            f"/api/v1/sub-categories/products?category_id={electronics.id}",
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Laptops"


class TestSubCategoryImage:
    def test_create_sub_category_with_image(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "seller@test.com", "password123")
        image_url = "https://cdn.example.com/sub-categories/tablets.jpg"

        response = client.post(
            "/api/v1/sub-categories/",
            json={
                "name": "Tablets",
                "category_id": seed_categories[0].id,
                "image": image_url,
            },
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 201
        assert data["data"]["name"] == "Tablets"
        assert data["data"]["image"] == image_url

    def test_update_sub_category_image(self, client, seed_users, seed_sub_categories):
        token = get_auth_token(client, "seller@test.com", "password123")
        sub_category = seed_sub_categories[0]
        new_image = "https://cdn.example.com/sub-categories/laptops-v2.jpg"

        response = client.put(
            f"/api/v1/sub-categories/{sub_category.id}",
            json={"image": new_image},
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["data"]["image"] == new_image
