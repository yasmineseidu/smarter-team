"""Base integration client with common functionality."""

from abc import ABC
from typing import Any

import httpx

from src.config import Integration, get_agent_logger


class BaseIntegrationClient(ABC):
    """
    Base class for all integration clients.

    Provides common HTTP client setup, rate limiting,
    error handling, and retry logic.
    """

    def __init__(
        self,
        config: Integration | None = None,
        *,
        name: str = "unknown",
        base_url: str = "",
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the integration client.

        Args:
            config: Integration configuration (optional if using kwargs)
            name: Integration name (used if config not provided)
            base_url: Base URL for API (used if config not provided)
            api_key: API key for authentication (used if config not provided)
            timeout: Request timeout in seconds (used if config not provided)
        """
        if config is not None:
            self.config = config
        else:
            self.config = Integration(
                name=name,
                base_url=base_url,
                api_key=api_key,
                timeout=timeout,
            )

        # Expose config properties directly for easier access
        self.base_url = self.config.base_url
        self.api_key = self.config.api_key
        self.timeout = self.config.timeout

        # Rate limiting support
        self.rate_limit: int | None = None
        self.rate_limit_remaining: int | None = None

        self.logger = get_agent_logger(f"integration.{self.config.name}")
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=self.config.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make an HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: On HTTP errors
        """
        self.logger.debug(f"{method} {endpoint}")

        response = await self.client.request(method, endpoint, **kwargs)
        response.raise_for_status()

        return response.json()

    async def get(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a PUT request."""
        return await self._request("PUT", endpoint, **kwargs)

    async def patch(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a PATCH request."""
        return await self._request("PATCH", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self._request("DELETE", endpoint, **kwargs)
