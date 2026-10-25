import io

import pytest

from app.integrations import s3
from tests.conftest import get_auth_token, auth_header

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64


@pytest.fixture
def fake_s3(monkeypatch):
    calls = {"uploaded": [], "deleted": []}
    monkeypatch.setattr(s3, "is_configured", lambda: True)
    monkeypatch.setattr(
        s3, "upload", lambda stream, key, content_type: calls["uploaded"].append(key) or key
    )
    monkeypatch.setattr(s3, "delete", lambda key: calls["deleted"].append(key))
    return calls


def _post(client, url, token, content=JPEG, name="a.jpg"):
    return client.post(
        url,
        data={"file": (io.BytesIO(content), name)},
        content_type="multipart/form-data",
        headers=auth_header(token),
    )


class TestCategoryImageUpload:
    def test_admin_uploads_and_response_has_url(self, client, seed_users, seed_categories, fake_s3):
        token = get_auth_token(client, "admin@test.com", "password123")
        cat = seed_categories[0]

        response = _post(client, f"/api/v1/categories/{cat.id}/image", token)
        data = response.get_json()["data"]

        assert response.status_code == 200
        assert data["image"].endswith(fake_s3["uploaded"][0])
        assert fake_s3["uploaded"][0].startswith(f"categories/{cat.id}/")

    def test_replacing_removes_old_managed_object(self, client, db, seed_users, seed_categories, fake_s3):
        token = get_auth_token(client, "admin@test.com", "password123")
        cat = seed_categories[0]
        cat.image = f"categories/{cat.id}/old.jpg"
        db.session.commit()

        _post(client, f"/api/v1/categories/{cat.id}/image", token)

        assert fake_s3["deleted"] == [f"categories/{cat.id}/old.jpg"]

    def test_external_url_is_not_deleted(self, client, seed_users, seed_categories, fake_s3):
        token = get_auth_token(client, "admin@test.com", "password123")
        cat = seed_categories[0]

        _post(client, f"/api/v1/categories/{cat.id}/image", token)

        assert fake_s3["deleted"] == []

    def test_buyer_forbidden(self, client, seed_users, seed_categories, fake_s3):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = _post(client, f"/api/v1/categories/{seed_categories[0].id}/image", token)

        assert response.status_code == 403

    def test_not_found(self, client, seed_users, fake_s3):
        token = get_auth_token(client, "admin@test.com", "password123")

        assert _post(client, "/api/v1/categories/9999/image", token).status_code == 404

    def test_invalid_file_rejected(self, client, seed_users, seed_categories, fake_s3):
        token = get_auth_token(client, "admin@test.com", "password123")

        response = _post(
            client, f"/api/v1/categories/{seed_categories[0].id}/image", token,
            content=b"not an image", name="a.txt",
        )

        assert response.status_code == 422
        assert fake_s3["uploaded"] == []

    def test_storage_not_configured(self, client, monkeypatch, seed_users, seed_categories):
        monkeypatch.setattr(s3, "is_configured", lambda: False)
        token = get_auth_token(client, "admin@test.com", "password123")

        response = _post(client, f"/api/v1/categories/{seed_categories[0].id}/image", token)

        assert response.status_code == 503


class TestSubCategoryImageUpload:
    def test_admin_uploads(self, client, seed_users, seed_sub_categories, fake_s3):
        token = get_auth_token(client, "admin@test.com", "password123")
        sub = seed_sub_categories[0]

        response = _post(client, f"/api/v1/sub-categories/{sub.id}/image", token)

        assert response.status_code == 200
        assert fake_s3["uploaded"][0].startswith(f"sub-categories/{sub.id}/")
        assert response.get_json()["data"]["image"].endswith(fake_s3["uploaded"][0])

    def test_buyer_forbidden(self, client, seed_users, seed_sub_categories, fake_s3):
        token = get_auth_token(client, "buyer@test.com", "password123")

        response = _post(client, f"/api/v1/sub-categories/{seed_sub_categories[0].id}/image", token)

        assert response.status_code == 403

    def test_not_found(self, client, seed_users, fake_s3):
        token = get_auth_token(client, "admin@test.com", "password123")

        assert _post(client, "/api/v1/sub-categories/9999/image", token).status_code == 404
