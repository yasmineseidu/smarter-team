"""Reusable fixtures for integration testing."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""

    def _create_response(
        status_code: int = 200,
        json_data: dict | None = None,
        headers: dict | None = None,
    ):
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.headers = headers or {}
        response.is_success = 200 <= status_code < 300
        response.raise_for_status = MagicMock()
        if status_code >= 400:
            response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Error", request=MagicMock(), response=response
            )
        return response

    return _create_response


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx async client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def mock_instantly_response():
    """Create mock Instantly.ai API response."""
    return {
        "campaign_id": "camp_123",
        "leads": [
            {
                "id": "lead_001",
                "email": "prospect@example.com",
                "status": "active",
                "opened": True,
                "clicked": False,
            }
        ],
        "stats": {
            "sent": 100,
            "opened": 45,
            "replied": 12,
        },
    }


@pytest.fixture
def mock_gohighlevel_response():
    """Create mock GoHighLevel API response."""
    return {
        "contact": {
            "id": "contact_abc",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "tags": ["qualified", "enterprise"],
        },
        "pipeline": {
            "id": "pipe_xyz",
            "stage": "qualified",
        },
    }


@pytest.fixture
def mock_stripe_response():
    """Create mock Stripe API response."""
    return {
        "id": "inv_123",
        "object": "invoice",
        "amount_due": 5000,
        "currency": "usd",
        "status": "open",
        "customer": "cus_abc",
        "lines": {
            "data": [
                {
                    "description": "Consulting Services",
                    "amount": 5000,
                }
            ]
        },
    }


@pytest.fixture
def mock_pinecone_response():
    """Create mock Pinecone API response."""
    return {
        "matches": [
            {
                "id": "vec_001",
                "score": 0.95,
                "metadata": {"text": "Relevant document content"},
            },
            {
                "id": "vec_002",
                "score": 0.87,
                "metadata": {"text": "Another relevant document"},
            },
        ],
        "namespace": "default",
    }


@pytest.fixture
def mock_anthropic_client():
    """Create mock Anthropic client."""
    client = MagicMock()
    client.messages.create = AsyncMock(
        return_value=MagicMock(
            id="msg_123",
            content=[{"type": "text", "text": "Claude response"}],
            model="claude-3-5-sonnet-20241022",
            stop_reason="end_turn",
            usage={"input_tokens": 100, "output_tokens": 50},
        )
    )
    return client


@pytest.fixture
def mock_rate_limit_headers():
    """Create mock rate limit headers."""
    return {
        "X-RateLimit-Limit": "1000",
        "X-RateLimit-Remaining": "999",
        "X-RateLimit-Reset": "1704067200",
    }


@pytest.fixture
def mock_webhook_payload():
    """Create mock webhook payload."""
    return {
        "event": "lead.created",
        "timestamp": "2024-12-05T10:00:00Z",
        "data": {
            "id": "lead_new",
            "email": "new@example.com",
            "source": "instantly",
        },
        "signature": "sha256=abc123...",
    }


@pytest.fixture
def mock_database_session():
    """Create mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_celery_worker():
    """Create mock Celery worker context."""
    worker = MagicMock()
    worker.request.id = "task-id-abc123"
    worker.request.retries = 0
    worker.max_retries = 3
    worker.retry = MagicMock(side_effect=Exception("Retry triggered"))
    return worker


@pytest.fixture
def integration_test_env():
    """Set up environment for integration tests."""
    import os

    # Store original values
    original_env = {}
    test_vars = {
        "REDIS_URL": "redis://localhost:6379/1",
        "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
        "ANTHROPIC_API_KEY": "sk-ant-test-key",
        "SECRET_KEY": "test-secret-key",
    }

    for key, value in test_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_vars

    # Restore original values
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
