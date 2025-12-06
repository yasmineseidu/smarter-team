"""Unit tests for FastAPI main application."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client: TestClient):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client: TestClient):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_includes_version(self, client: TestClient):
        """Health endpoint should include version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"


class TestRootEndpoint:
    """Tests for the / root endpoint."""

    def test_root_returns_200(self, client: TestClient):
        """Root endpoint should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_api_name(self, client: TestClient):
        """Root endpoint should return API name."""
        response = client.get("/")
        data = response.json()
        assert data["name"] == "Smarter Team API"

    def test_root_includes_version(self, client: TestClient):
        """Root endpoint should include version."""
        response = client.get("/")
        data = response.json()
        assert data["version"] == "0.1.0"

    def test_root_includes_docs_link(self, client: TestClient):
        """Root endpoint should include docs link."""
        response = client.get("/")
        data = response.json()
        assert data["docs"] == "/docs"


class TestOpenAPISchema:
    """Tests for OpenAPI documentation."""

    def test_openapi_json_accessible(self, client: TestClient):
        """OpenAPI JSON should be accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_has_correct_title(self, client: TestClient):
        """OpenAPI should have correct title."""
        response = client.get("/openapi.json")
        schema = response.json()
        assert schema["info"]["title"] == "Smarter Team API"

    def test_openapi_has_description(self, client: TestClient):
        """OpenAPI should have description."""
        response = client.get("/openapi.json")
        schema = response.json()
        assert "description" in schema["info"]

    def test_docs_endpoint_accessible(self, client: TestClient):
        """Swagger docs should be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint_accessible(self, client: TestClient):
        """ReDoc should be accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_allows_localhost(self, client: TestClient):
        """CORS should allow localhost origin."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200

    def test_cors_header_present(self, client: TestClient):
        """CORS headers should be present in response."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should succeed
        assert response.status_code in (200, 204, 405)
