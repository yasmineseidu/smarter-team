"""Unit tests for BaseIntegrationClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.integrations.base import BaseIntegrationClient


class ConcreteIntegration(BaseIntegrationClient):
    """Concrete implementation for testing."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@pytest.fixture
def client():
    """Create a test integration client."""
    return ConcreteIntegration(
        name="test",
        base_url="https://api.example.com",
        api_key="test-api-key",
    )


class TestBaseIntegrationClientInitialization:
    """Tests for client initialization."""

    def test_client_has_base_url(self, client: ConcreteIntegration):
        """Client should have base URL set."""
        assert client.base_url == "https://api.example.com"

    def test_client_has_api_key(self, client: ConcreteIntegration):
        """Client should have API key set."""
        assert client.api_key == "test-api-key"

    def test_client_has_default_timeout(self, client: ConcreteIntegration):
        """Client should have default timeout."""
        assert client.timeout == 30.0

    def test_client_with_custom_timeout(self):
        """Client should accept custom timeout."""
        custom = ConcreteIntegration(
            name="custom",
            base_url="https://api.example.com",
            api_key="key",
            timeout=60.0,
        )
        assert custom.timeout == 60.0

    def test_client_has_rate_limit_attributes(self, client: ConcreteIntegration):
        """Client should have rate limit attributes."""
        assert hasattr(client, "rate_limit")
        assert hasattr(client, "rate_limit_remaining")


class TestHTTPMethods:
    """Tests for HTTP methods."""

    @pytest.mark.asyncio
    async def test_get_request(self, client: ConcreteIntegration):
        """GET request should work correctly."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock:
            mock.return_value = {"data": "test"}

            result = await client.get("/endpoint")

            mock.assert_called_once_with("GET", "/endpoint")
            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_get_with_params(self, client: ConcreteIntegration):
        """GET request should pass query params."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock:
            mock.return_value = {"data": "test"}

            await client.get("/endpoint", params={"page": 1, "limit": 10})

            mock.assert_called_once_with("GET", "/endpoint", params={"page": 1, "limit": 10})

    @pytest.mark.asyncio
    async def test_post_request(self, client: ConcreteIntegration):
        """POST request should work correctly."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock:
            mock.return_value = {"id": "123"}

            result = await client.post("/endpoint", json={"name": "test"})

            mock.assert_called_once_with("POST", "/endpoint", json={"name": "test"})
            assert result == {"id": "123"}

    @pytest.mark.asyncio
    async def test_put_request(self, client: ConcreteIntegration):
        """PUT request should work correctly."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock:
            mock.return_value = {"updated": True}

            result = await client.put("/endpoint/123", json={"name": "updated"})

            mock.assert_called_once_with("PUT", "/endpoint/123", json={"name": "updated"})
            assert result == {"updated": True}

    @pytest.mark.asyncio
    async def test_delete_request(self, client: ConcreteIntegration):
        """DELETE request should work correctly."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock:
            mock.return_value = {"deleted": True}

            result = await client.delete("/endpoint/123")

            mock.assert_called_once_with("DELETE", "/endpoint/123")
            assert result == {"deleted": True}


class TestHTTPClientSetup:
    """Tests for HTTP client configuration."""

    def test_client_property_creates_httpx_client(self, client: ConcreteIntegration):
        """Client property should create an httpx AsyncClient."""
        http_client = client.client
        assert isinstance(http_client, httpx.AsyncClient)

    def test_client_includes_auth_header(self, client: ConcreteIntegration):
        """Client should include Authorization header when API key is set."""
        http_client = client.client
        assert "Authorization" in http_client.headers
        assert http_client.headers["Authorization"] == "Bearer test-api-key"

    @pytest.mark.asyncio
    async def test_close_cleans_up_client(self, client: ConcreteIntegration):
        """Close should clean up the HTTP client."""
        _ = client.client  # Create the client
        assert client._client is not None

        await client.close()
        assert client._client is None


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_handles_http_error(self, client: ConcreteIntegration):
        """Should propagate HTTP errors."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock:
            mock.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )

            with pytest.raises(httpx.HTTPStatusError):
                await client.get("/nonexistent")

    @pytest.mark.asyncio
    async def test_handles_timeout_error(self, client: ConcreteIntegration):
        """Should propagate timeout errors."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock:
            mock.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(httpx.TimeoutException):
                await client.get("/slow-endpoint")

    @pytest.mark.asyncio
    async def test_handles_connection_error(self, client: ConcreteIntegration):
        """Should propagate connection errors."""
        with patch.object(client, "_request", new_callable=AsyncMock) as mock:
            mock.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(httpx.ConnectError):
                await client.get("/endpoint")


class TestRateLimiting:
    """Tests for rate limiting support."""

    def test_rate_limit_initially_none(self, client: ConcreteIntegration):
        """Rate limit should initially be None."""
        assert client.rate_limit is None
        assert client.rate_limit_remaining is None

    def test_rate_limit_can_be_set(self, client: ConcreteIntegration):
        """Rate limit values should be settable."""
        client.rate_limit = 1000
        client.rate_limit_remaining = 999

        assert client.rate_limit == 1000
        assert client.rate_limit_remaining == 999
