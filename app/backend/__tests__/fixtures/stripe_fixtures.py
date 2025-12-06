"""Test fixtures for Stripe integration tests."""

import hashlib
import hmac
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.integrations.stripe import StripeClient


@pytest.fixture
def stripe_api_key() -> str:
    """Test Stripe API key."""
    return "sk_test_abc123xyz"


@pytest.fixture
def stripe_webhook_secret() -> str:
    """Test Stripe webhook secret."""
    return "whsec_test_secret_123"


@pytest.fixture
def stripe_client(stripe_api_key: str) -> StripeClient:
    """Create a test Stripe client without webhook secret."""
    return StripeClient(api_key=stripe_api_key)


@pytest.fixture
def stripe_client_with_webhook(
    stripe_api_key: str,
    stripe_webhook_secret: str,
) -> StripeClient:
    """Create a test Stripe client with webhook secret."""
    return StripeClient(
        api_key=stripe_api_key,
        webhook_secret=stripe_webhook_secret,
    )


@pytest.fixture
def mock_customer_response() -> dict[str, Any]:
    """Mock Stripe customer response."""
    return {
        "id": "cus_test123",
        "object": "customer",
        "email": "test@example.com",
        "name": "Test User",
        "phone": "+1234567890",
        "description": "Test customer",
        "created": 1704067200,
        "livemode": False,
        "metadata": {"company": "Test Inc"},
        "currency": "usd",
    }


@pytest.fixture
def mock_payment_intent_response() -> dict[str, Any]:
    """Mock Stripe payment intent response."""
    return {
        "id": "pi_test123",
        "object": "payment_intent",
        "amount": 5000,
        "currency": "usd",
        "status": "requires_payment_method",
        "client_secret": "pi_test123_secret_xyz",
        "customer": "cus_test123",
        "description": "Test payment",
        "created": 1704067200,
        "livemode": False,
        "payment_method_types": ["card"],
        "metadata": {},
    }


@pytest.fixture
def mock_invoice_response() -> dict[str, Any]:
    """Mock Stripe invoice response."""
    return {
        "id": "inv_test123",
        "object": "invoice",
        "customer": "cus_test123",
        "amount_due": 5000,
        "amount_paid": 0,
        "currency": "usd",
        "status": "draft",
        "auto_advance": True,
        "collection_method": "charge_automatically",
        "description": "Test invoice",
        "created": 1704067200,
        "livemode": False,
        "lines": {
            "data": [
                {
                    "id": "il_test123",
                    "amount": 5000,
                    "description": "Test line item",
                }
            ],
            "has_more": False,
        },
        "metadata": {},
    }


@pytest.fixture
def mock_subscription_response() -> dict[str, Any]:
    """Mock Stripe subscription response."""
    return {
        "id": "sub_test123",
        "object": "subscription",
        "customer": "cus_test123",
        "status": "active",
        "current_period_start": 1704067200,
        "current_period_end": 1706745600,
        "trial_start": None,
        "trial_end": None,
        "cancel_at_period_end": False,
        "created": 1704067200,
        "livemode": False,
        "items": {
            "data": [
                {
                    "id": "si_test123",
                    "price": {
                        "id": "price_test123",
                        "product": "prod_test123",
                        "unit_amount": 2000,
                        "currency": "usd",
                        "recurring": {
                            "interval": "month",
                            "interval_count": 1,
                        },
                    },
                    "quantity": 1,
                }
            ],
        },
        "metadata": {},
    }


@pytest.fixture
def mock_invoice_item_response() -> dict[str, Any]:
    """Mock Stripe invoice item response."""
    return {
        "id": "ii_test123",
        "object": "invoiceitem",
        "customer": "cus_test123",
        "amount": 2500,
        "currency": "usd",
        "description": "Test item",
        "invoice": None,
        "date": 1704067200,
        "livemode": False,
        "metadata": {},
    }


@pytest.fixture
def mock_list_response() -> dict[str, Any]:
    """Mock Stripe list response."""
    return {
        "object": "list",
        "has_more": False,
        "data": [],
    }


@pytest.fixture
def mock_error_response() -> dict[str, Any]:
    """Mock Stripe error response."""
    return {
        "error": {
            "type": "invalid_request_error",
            "code": "resource_missing",
            "message": "No such customer: 'cus_invalid'",
            "param": "customer",
        }
    }


@pytest.fixture
def mock_card_error_response() -> dict[str, Any]:
    """Mock Stripe card error response."""
    return {
        "error": {
            "type": "card_error",
            "code": "card_declined",
            "message": "Your card was declined.",
            "decline_code": "generic_decline",
        }
    }


@pytest.fixture
def mock_rate_limit_error_response() -> dict[str, Any]:
    """Mock Stripe rate limit error response."""
    return {
        "error": {
            "type": "rate_limit_error",
            "message": "Too many requests",
        }
    }


@pytest.fixture
def mock_httpx_response_factory():
    """Factory for creating mock httpx responses."""

    def _create_response(
        status_code: int = 200,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> MagicMock:
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.headers = headers or {}
        return response

    return _create_response


@pytest.fixture
def valid_webhook_payload() -> bytes:
    """Valid webhook payload."""
    return b'{"type":"payment_intent.succeeded","data":{"object":{"id":"pi_test"}}}'


@pytest.fixture
def valid_webhook_signature(
    stripe_webhook_secret: str,
    valid_webhook_payload: bytes,
) -> str:
    """Create a valid webhook signature for the test payload."""
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{valid_webhook_payload.decode('utf-8')}"
    signature = hmac.new(
        stripe_webhook_secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


@pytest.fixture
def expired_webhook_signature(
    stripe_webhook_secret: str,
    valid_webhook_payload: bytes,
) -> str:
    """Create an expired webhook signature (old timestamp)."""
    timestamp = int(time.time()) - 600  # 10 minutes ago
    signed_payload = f"{timestamp}.{valid_webhook_payload.decode('utf-8')}"
    signature = hmac.new(
        stripe_webhook_secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


@pytest.fixture
def invalid_webhook_signature() -> str:
    """Invalid webhook signature."""
    return "t=1704067200,v1=invalid_signature_here"


@pytest.fixture
def mock_async_client():
    """Create a mock async HTTP client."""
    return AsyncMock(spec=httpx.AsyncClient)
