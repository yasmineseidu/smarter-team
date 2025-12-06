"""Integration tests for health and API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client for integration tests."""
    return TestClient(app)


class TestHealthAPIIntegration:
    """Integration tests for health endpoints."""

    def test_full_health_check_flow(self, client: TestClient):
        """Test complete health check workflow."""
        # 1. Check health endpoint
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()

        # 2. Verify health status
        assert health_data["status"] == "healthy"
        assert health_data["version"] == "0.1.0"

        # 3. Check root endpoint
        root_response = client.get("/")
        assert root_response.status_code == 200
        root_data = root_response.json()

        # 4. Verify API info matches health version
        assert root_data["version"] == health_data["version"]

    def test_api_documentation_flow(self, client: TestClient):
        """Test API documentation is properly configured."""
        # 1. Check OpenAPI schema
        schema_response = client.get("/openapi.json")
        assert schema_response.status_code == 200
        schema = schema_response.json()

        # 2. Verify schema structure
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == "Smarter Team API"

        # 3. Verify health endpoint is documented
        assert "/health" in schema["paths"]
        assert "/" in schema["paths"]

        # 4. Check Swagger UI
        docs_response = client.get("/docs")
        assert docs_response.status_code == 200

        # 5. Check ReDoc
        redoc_response = client.get("/redoc")
        assert redoc_response.status_code == 200

    def test_error_handling_integration(self, client: TestClient):
        """Test error handling across the API."""
        # 1. Request non-existent endpoint
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

        # 2. Verify error response format
        error_data = response.json()
        assert "detail" in error_data

    def test_cors_integration(self, client: TestClient):
        """Test CORS is properly configured."""
        # 1. Simulate CORS preflight
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should not fail
        assert response.status_code in (200, 204, 405)

        # 2. Regular request with origin
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200


class TestAPIVersioning:
    """Tests for API versioning."""

    def test_version_consistency(self, client: TestClient):
        """All version references should be consistent."""
        # Get version from multiple sources
        health_version = client.get("/health").json()["version"]
        root_version = client.get("/").json()["version"]
        schema_version = client.get("/openapi.json").json()["info"]["version"]

        # All should match
        assert health_version == root_version == schema_version


class TestAPIResilience:
    """Tests for API resilience and edge cases."""

    def test_handles_large_headers(self, client: TestClient):
        """API should handle requests with large headers."""
        large_header = "x" * 1000
        response = client.get(
            "/health",
            headers={"X-Custom-Header": large_header},
        )
        assert response.status_code == 200

    def test_handles_special_characters_in_path(self, client: TestClient):
        """API should handle special characters safely."""
        # URL-encoded special characters
        response = client.get("/health?test=%20%26%3D")
        assert response.status_code == 200

    def test_concurrent_requests(self, client: TestClient):
        """API should handle concurrent requests."""
        import concurrent.futures

        def make_request():
            return client.get("/health").status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        assert all(status == 200 for status in results)
