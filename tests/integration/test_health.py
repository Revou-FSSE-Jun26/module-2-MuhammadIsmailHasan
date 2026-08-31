class TestHealthCheck:

    def test_health_ok(self, client):
        response = client.get('/api/v1/health')
        data = response.get_json()

        assert response.status_code == 200
        assert data['status'] is True
        assert data['message'] == 'healthy'
        assert data['data']['database'] == 'up'

    def test_health_no_auth_required(self, client):
        response = client.get('/api/v1/health')
        assert response.status_code == 200
