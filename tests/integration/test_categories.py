from tests.conftest import get_auth_token, auth_header


class TestGetCategories:
    def test_get_categories_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get("/api/v1/categories/", headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] is True
        assert len(data["data"]) == 2
        assert data["pagination"]["total_items"] == 2

    def test_get_categories_list_excludes_products(
        self, client, seed_users, seed_products
    ):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get("/api/v1/categories/", headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert all("products" not in cat for cat in data["data"])

    def test_get_categories_with_products(self, client, seed_users, seed_products):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get("/api/v1/categories/products", headers=auth_header(token))
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] is True
        assert all("products" in cat for cat in data["data"])
        assert "pagination" in data

        electronics = next(c for c in data["data"] if c["name"] == "Electronics")
        assert len(electronics["products"]) == 1
        assert electronics["products"][0]["name"] == "Laptop"

    def test_get_categories_with_products_no_auth(self, client):
        response = client.get("/api/v1/categories/products")
        assert response.status_code == 401

    def test_get_categories_with_products_filter_by_name(
        self, client, seed_users, seed_products
    ):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get(
            "/api/v1/categories/products?name=elec", headers=auth_header(token)
        )
        data = response.get_json()

        assert response.status_code == 200
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Electronics"

    def test_get_products_by_category(self, client, seed_users, seed_products):
        token = get_auth_token(client, "buyer@test.com", "password123")

        electronics = seed_products[0].sub_category.category

        response = client.get(
            f"/api/v1/categories/{electronics.id}",
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] is True

        # nested shape: category -> sub_categories -> products
        category = data["data"]
        assert category["name"] == "Electronics"
        assert category["image"] == "https://cdn.example.com/categories/electronics.jpg"
        assert isinstance(category["sub_categories"], list)

        laptops = next(
            sub for sub in category["sub_categories"] if sub["name"] == "Laptops"
        )
        assert laptops["image"] == "https://cdn.example.com/sub-categories/laptops.jpg"
        assert len(laptops["products"]) == 1

        product = laptops["products"][0]
        assert product["name"] == "Laptop"
        assert set(product.keys()) == {"id", "image", "name", "price", "slug", "stock"}

    def test_get_categories_filter_by_name(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get(
            "/api/v1/categories/?name=elec", headers=auth_header(token)
        )
        data = response.get_json()

        assert response.status_code == 200
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Electronics"

    def test_get_categories_no_auth(self, client):
        response = client.get("/api/v1/categories/")
        assert response.status_code == 401


class TestCreateCategory:
    def test_create_category_success(self, client, seed_users):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.post(
            "/api/v1/categories/", json={"name": "Books"}, headers=auth_header(token)
        )
        data = response.get_json()

        assert response.status_code == 201
        assert data["data"]["name"] == "Books"

    def test_create_category_with_image(self, client, seed_users):
        token = get_auth_token(client, "seller@test.com", "password123")
        image_url = "https://cdn.example.com/categories/gadgets.jpg"

        response = client.post(
            "/api/v1/categories/",
            json={"name": "Gadgets", "image": image_url},
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 201
        assert data["data"]["name"] == "Gadgets"
        assert data["data"]["image"] == image_url

    def test_update_category_image(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "seller@test.com", "password123")
        category = seed_categories[0]
        new_image = "https://cdn.example.com/categories/electronics-v2.jpg"

        response = client.put(
            f"/api/v1/categories/{category.id}",
            json={"name": "Electronics", "image": new_image},
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["data"]["image"] == new_image

    def test_create_category_duplicate_name(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.post(
            "/api/v1/categories/",
            json={"name": "Electronics"},
            headers=auth_header(token),
        )

        assert response.status_code == 409
        assert response.get_json()["message"] == "category name already exists"

    def test_create_category_missing_name(self, client, seed_users):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.post(
            "/api/v1/categories/", json={"name": None}, headers=auth_header(token)
        )

        assert response.status_code == 422
        assert response.get_json()["message"] == "name cannot be empty"

    def test_create_category_empty_name(self, client, seed_users):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.post(
            "/api/v1/categories/", json={"name": ""}, headers=auth_header(token)
        )

        assert response.status_code == 422

    def test_create_category_buyer_forbidden(self, client, seed_users):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.post(
            "/api/v1/categories/", json={"name": "Hack"}, headers=auth_header(token)
        )

        assert response.status_code == 403


class TestGetCategory:
    def test_get_category_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "buyer@test.com", "password123")
        category = seed_categories[0]

        response = client.get(
            f"/api/v1/categories/{category.id}", headers=auth_header(token)
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["data"]["name"] == "Electronics"
        # nested shape and the new image column
        assert data["data"]["image"] == (
            "https://cdn.example.com/categories/electronics.jpg"
        )
        assert "sub_categories" in data["data"]
        assert isinstance(data["data"]["sub_categories"], list)

    def test_get_category_nested_sub_categories_with_products(
        self, client, seed_users, seed_products
    ):
        token = get_auth_token(client, "buyer@test.com", "password123")
        electronics = seed_products[0].sub_category.category

        response = client.get(
            f"/api/v1/categories/{electronics.id}", headers=auth_header(token)
        )
        data = response.get_json()

        assert response.status_code == 200
        laptops = next(
            sub for sub in data["data"]["sub_categories"] if sub["name"] == "Laptops"
        )
        assert len(laptops["products"]) == 1
        product = laptops["products"][0]
        assert set(product.keys()) == {"id", "image", "name", "price", "slug", "stock"}

    def test_get_category_not_found(self, client, seed_users):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = client.get("/api/v1/categories/9999", headers=auth_header(token))

        assert response.status_code == 404


class TestUpdateCategory:
    def test_update_category_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "seller@test.com", "password123")
        category = seed_categories[0]

        response = client.put(
            f"/api/v1/categories/{category.id}",
            json={"name": "Tech & Gadgets"},
            headers=auth_header(token),
        )
        data = response.get_json()

        assert response.status_code == 200
        assert data["data"]["name"] == "Tech & Gadgets"

    def test_update_category_duplicate_name(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "seller@test.com", "password123")
        category = seed_categories[0]

        response = client.put(
            f"/api/v1/categories/{category.id}",
            json={"name": "Clothing"},
            headers=auth_header(token),
        )

        assert response.status_code == 409
        assert response.get_json()["message"] == "category name already exists"

    def test_update_category_not_found(self, client, seed_users):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.put(
            "/api/v1/categories/9999",
            json={"name": "Ghost"},
            headers=auth_header(token),
        )

        assert response.status_code == 404

    def test_update_category_buyer_forbidden(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "buyer@test.com", "password123")
        category = seed_categories[0]

        response = client.put(
            f"/api/v1/categories/{category.id}",
            json={"name": "Hacked"},
            headers=auth_header(token),
        )

        assert response.status_code == 403


class TestDeleteCategory:
    def test_delete_category_success(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "seller@test.com", "password123")
        category = seed_categories[0]

        response = client.delete(
            f"/api/v1/categories/{category.id}", headers=auth_header(token)
        )

        assert response.status_code == 200
        assert response.get_json()["message"] == "success delete category"

    def test_delete_category_not_found(self, client, seed_users):
        token = get_auth_token(client, "seller@test.com", "password123")

        response = client.delete("/api/v1/categories/9999", headers=auth_header(token))

        assert response.status_code == 404

    def test_delete_category_buyer_forbidden(self, client, seed_users, seed_categories):
        token = get_auth_token(client, "buyer@test.com", "password123")
        category = seed_categories[0]

        response = client.delete(
            f"/api/v1/categories/{category.id}", headers=auth_header(token)
        )

        assert response.status_code == 403
