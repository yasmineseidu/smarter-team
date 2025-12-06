"""Pytest fixtures for Smarter Team tests."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from src.main import app

    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("config.redis.redis_client") as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_claude():
    """Mock Claude/Anthropic API."""
    with patch("anthropic.Anthropic") as mock:
        mock_response = AsyncMock()
        mock_response.content = [{"type": "text", "text": "Mock response"}]
        mock.return_value.messages.create = AsyncMock(return_value=mock_response)
        yield mock


@pytest.fixture
def mock_pinecone():
    """Mock Pinecone client."""
    with patch("pinecone.Pinecone") as mock:
        mock_index = AsyncMock()
        mock_index.query.return_value = {"matches": []}
        mock_index.upsert.return_value = {"upserted_count": 1}
        mock.return_value.Index.return_value = mock_index
        yield mock
