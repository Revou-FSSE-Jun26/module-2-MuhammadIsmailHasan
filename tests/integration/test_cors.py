import pytest

from app import create_app

ALLOWED = "http://localhost:5173"
BLOCKED = "https://evil.example.com"


def create_app_with_origins(origins):
    import config.development as dev

    original = dev.DevelopmentConfig.CORS_ORIGINS
    dev.DevelopmentConfig.CORS_ORIGINS = origins
    try:
        return create_app("development")
    finally:
        dev.DevelopmentConfig.CORS_ORIGINS = original


@pytest.fixture
def cors_client():
    return create_app_with_origins([ALLOWED]).test_client()


class TestCors:
    def test_allowed_origin_gets_header(self, cors_client):
        response = cors_client.get("/api/v1/health", headers={"Origin": ALLOWED})

        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == ALLOWED

    def test_blocked_origin_gets_no_header(self, cors_client):
        response = cors_client.get("/api/v1/health", headers={"Origin": BLOCKED})

        assert "Access-Control-Allow-Origin" not in response.headers

    def test_preflight_allows_authorization_header(self, cors_client):
        response = cors_client.options(
            "/api/v1/products/",
            headers={
                "Origin": ALLOWED,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == ALLOWED
        allowed = response.headers["Access-Control-Allow-Headers"].lower()
        assert "authorization" in allowed
        assert "content-type" in allowed
        assert "POST" in response.headers["Access-Control-Allow-Methods"]

    def test_error_response_still_carries_header(self, cors_client):
        response = cors_client.post(
            "/api/v1/products/", json={}, headers={"Origin": ALLOWED}
        )

        assert response.status_code >= 400
        assert response.headers["Access-Control-Allow-Origin"] == ALLOWED

    def test_empty_origin_list_blocks_everything(self):
        client = create_app_with_origins([]).test_client()

        response = client.get("/api/v1/health", headers={"Origin": ALLOWED})

        assert "Access-Control-Allow-Origin" not in response.headers

    def test_no_wildcard_ever_returned(self, cors_client):
        response = cors_client.get("/api/v1/health", headers={"Origin": ALLOWED})

        assert response.headers["Access-Control-Allow-Origin"] != "*"
