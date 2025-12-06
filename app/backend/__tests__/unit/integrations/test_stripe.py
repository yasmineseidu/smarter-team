"""Unit tests for Stripe integration client."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.integrations.stripe import StripeAPIError, StripeClient

# Import fixtures
pytest_plugins = ["__tests__.fixtures.stripe_fixtures"]


class TestStripeClientInitialization:
    """Tests for StripeClient initialization."""

    def test_has_correct_name(self, stripe_client: StripeClient) -> None:
        """Client should have 'stripe' as name."""
        assert stripe_client.config.name == "stripe"

    def test_has_correct_base_url(self, stripe_client: StripeClient) -> None:
        """Client should have Stripe API base URL."""
        assert stripe_client.base_url == "https://api.stripe.com/v1"

    def test_has_api_key(self, stripe_api_key: str, stripe_client: StripeClient) -> None:
        """Client should have API key set."""
        assert stripe_client.api_key == stripe_api_key

    def test_has_default_timeout(self, stripe_client: StripeClient) -> None:
        """Client should have default 30s timeout."""
        assert stripe_client.timeout == 30.0

    def test_has_default_max_retries(self, stripe_client: StripeClient) -> None:
        """Client should have default 3 max retries."""
        assert stripe_client.max_retries == 3

    def test_has_default_retry_delay(self, stripe_client: StripeClient) -> None:
        """Client should have default 1.0s retry delay."""
        assert stripe_client.retry_delay == 1.0

    def test_webhook_secret_is_none_by_default(self, stripe_client: StripeClient) -> None:
        """Webhook secret should be None when not provided."""
        assert stripe_client.webhook_secret is None

    def test_webhook_secret_can_be_set(
        self,
        stripe_client_with_webhook: StripeClient,
        stripe_webhook_secret: str,
    ) -> None:
        """Webhook secret should be set when provided."""
        assert stripe_client_with_webhook.webhook_secret == stripe_webhook_secret

    def test_custom_max_retries(self, stripe_api_key: str) -> None:
        """Client should accept custom max_retries."""
        client = StripeClient(api_key=stripe_api_key, max_retries=5)
        assert client.max_retries == 5

    def test_custom_retry_delay(self, stripe_api_key: str) -> None:
        """Client should accept custom retry_delay."""
        client = StripeClient(api_key=stripe_api_key, retry_delay=2.0)
        assert client.retry_delay == 2.0


class TestStripeClientHTTPSetup:
    """Tests for HTTP client configuration."""

    def test_client_uses_basic_auth(self, stripe_client: StripeClient) -> None:
        """Client should use basic auth with API key."""
        http_client = stripe_client.client
        assert http_client.auth is not None

    def test_client_has_stripe_version_header(self, stripe_client: StripeClient) -> None:
        """Client should include Stripe-Version header."""
        http_client = stripe_client.client
        assert "Stripe-Version" in http_client.headers

    def test_client_has_form_content_type(self, stripe_client: StripeClient) -> None:
        """Client should use form-encoded content type."""
        http_client = stripe_client.client
        assert "application/x-www-form-urlencoded" in http_client.headers.get("Content-Type", "")

    @pytest.mark.asyncio
    async def test_close_cleans_up_client(self, stripe_client: StripeClient) -> None:
        """Close should clean up the HTTP client."""
        _ = stripe_client.client  # Create the client
        assert stripe_client._client is not None

        await stripe_client.close()
        assert stripe_client._client is None


class TestCreateCustomer:
    """Tests for create_customer method."""

    @pytest.mark.asyncio
    async def test_creates_customer_successfully(
        self,
        stripe_client: StripeClient,
        mock_customer_response: dict[str, Any],
    ) -> None:
        """Should create customer with email."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_customer_response

            result = await stripe_client.create_customer(email="test@example.com")

            mock.assert_called_once()
            call_args = mock.call_args
            assert call_args[0] == ("POST", "/customers")
            assert call_args[1]["data"]["email"] == "test@example.com"
            assert result["id"] == "cus_test123"

    @pytest.mark.asyncio
    async def test_creates_customer_with_all_fields(
        self,
        stripe_client: StripeClient,
        mock_customer_response: dict[str, Any],
    ) -> None:
        """Should create customer with all optional fields."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_customer_response

            await stripe_client.create_customer(
                email="test@example.com",
                name="Test User",
                phone="+1234567890",
                description="Test customer",
                metadata={"company": "Test Inc"},
            )

            call_args = mock.call_args
            data = call_args[1]["data"]
            assert data["email"] == "test@example.com"
            assert data["name"] == "Test User"
            assert data["phone"] == "+1234567890"
            assert data["description"] == "Test customer"
            assert data["metadata[company]"] == "Test Inc"


class TestGetCustomer:
    """Tests for get_customer method."""

    @pytest.mark.asyncio
    async def test_retrieves_customer(
        self,
        stripe_client: StripeClient,
        mock_customer_response: dict[str, Any],
    ) -> None:
        """Should retrieve customer by ID."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_customer_response

            result = await stripe_client.get_customer("cus_test123")

            mock.assert_called_once_with("GET", "/customers/cus_test123")
            assert result["id"] == "cus_test123"


class TestUpdateCustomer:
    """Tests for update_customer method."""

    @pytest.mark.asyncio
    async def test_updates_customer(
        self,
        stripe_client: StripeClient,
        mock_customer_response: dict[str, Any],
    ) -> None:
        """Should update customer fields."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_customer_response

            await stripe_client.update_customer(
                customer_id="cus_test123",
                email="new@example.com",
                name="New Name",
            )

            call_args = mock.call_args
            assert call_args[0] == ("POST", "/customers/cus_test123")
            data = call_args[1]["data"]
            assert data["email"] == "new@example.com"
            assert data["name"] == "New Name"


class TestCreatePaymentIntent:
    """Tests for create_payment_intent method."""

    @pytest.mark.asyncio
    async def test_creates_payment_intent(
        self,
        stripe_client: StripeClient,
        mock_payment_intent_response: dict[str, Any],
    ) -> None:
        """Should create payment intent with amount and currency."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_payment_intent_response

            result = await stripe_client.create_payment_intent(amount=5000, currency="usd")

            mock.assert_called_once()
            call_args = mock.call_args
            assert call_args[0] == ("POST", "/payment_intents")
            data = call_args[1]["data"]
            assert data["amount"] == 5000
            assert data["currency"] == "usd"
            assert result["id"] == "pi_test123"

    @pytest.mark.asyncio
    async def test_creates_payment_intent_with_customer(
        self,
        stripe_client: StripeClient,
        mock_payment_intent_response: dict[str, Any],
    ) -> None:
        """Should include customer ID when provided."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_payment_intent_response

            await stripe_client.create_payment_intent(
                amount=5000,
                customer_id="cus_test123",
            )

            data = mock.call_args[1]["data"]
            assert data["customer"] == "cus_test123"

    @pytest.mark.asyncio
    async def test_creates_payment_intent_with_payment_methods(
        self,
        stripe_client: StripeClient,
        mock_payment_intent_response: dict[str, Any],
    ) -> None:
        """Should include payment method types."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_payment_intent_response

            await stripe_client.create_payment_intent(
                amount=5000,
                payment_method_types=["card", "bank_transfer"],
            )

            data = mock.call_args[1]["data"]
            assert data["payment_method_types[0]"] == "card"
            assert data["payment_method_types[1]"] == "bank_transfer"


class TestGetPaymentIntent:
    """Tests for get_payment_intent method."""

    @pytest.mark.asyncio
    async def test_retrieves_payment_intent(
        self,
        stripe_client: StripeClient,
        mock_payment_intent_response: dict[str, Any],
    ) -> None:
        """Should retrieve payment intent by ID."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_payment_intent_response

            result = await stripe_client.get_payment_intent("pi_test123")

            mock.assert_called_once_with("GET", "/payment_intents/pi_test123")
            assert result["id"] == "pi_test123"


class TestCancelPaymentIntent:
    """Tests for cancel_payment_intent method."""

    @pytest.mark.asyncio
    async def test_cancels_payment_intent(
        self,
        stripe_client: StripeClient,
        mock_payment_intent_response: dict[str, Any],
    ) -> None:
        """Should cancel payment intent."""
        mock_payment_intent_response["status"] = "canceled"
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_payment_intent_response

            result = await stripe_client.cancel_payment_intent("pi_test123")

            mock.assert_called_once_with("POST", "/payment_intents/pi_test123/cancel")
            assert result["status"] == "canceled"


class TestCreateInvoice:
    """Tests for create_invoice method."""

    @pytest.mark.asyncio
    async def test_creates_invoice(
        self,
        stripe_client: StripeClient,
        mock_invoice_response: dict[str, Any],
    ) -> None:
        """Should create invoice for customer."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_invoice_response

            result = await stripe_client.create_invoice(customer_id="cus_test123")

            mock.assert_called_once()
            call_args = mock.call_args
            assert call_args[0] == ("POST", "/invoices")
            data = call_args[1]["data"]
            assert data["customer"] == "cus_test123"
            assert result["id"] == "inv_test123"

    @pytest.mark.asyncio
    async def test_creates_invoice_with_options(
        self,
        stripe_client: StripeClient,
        mock_invoice_response: dict[str, Any],
    ) -> None:
        """Should create invoice with all options."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_invoice_response

            await stripe_client.create_invoice(
                customer_id="cus_test123",
                auto_advance=False,
                collection_method="send_invoice",
                description="Monthly services",
            )

            data = mock.call_args[1]["data"]
            assert data["auto_advance"] == "false"
            assert data["collection_method"] == "send_invoice"
            assert data["description"] == "Monthly services"


class TestGetInvoice:
    """Tests for get_invoice method."""

    @pytest.mark.asyncio
    async def test_retrieves_invoice(
        self,
        stripe_client: StripeClient,
        mock_invoice_response: dict[str, Any],
    ) -> None:
        """Should retrieve invoice by ID."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_invoice_response

            result = await stripe_client.get_invoice("inv_test123")

            mock.assert_called_once_with("GET", "/invoices/inv_test123")
            assert result["id"] == "inv_test123"


class TestFinalizeInvoice:
    """Tests for finalize_invoice method."""

    @pytest.mark.asyncio
    async def test_finalizes_invoice(
        self,
        stripe_client: StripeClient,
        mock_invoice_response: dict[str, Any],
    ) -> None:
        """Should finalize invoice."""
        mock_invoice_response["status"] = "open"
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_invoice_response

            result = await stripe_client.finalize_invoice("inv_test123")

            mock.assert_called_once_with("POST", "/invoices/inv_test123/finalize")
            assert result["status"] == "open"


class TestPayInvoice:
    """Tests for pay_invoice method."""

    @pytest.mark.asyncio
    async def test_pays_invoice(
        self,
        stripe_client: StripeClient,
        mock_invoice_response: dict[str, Any],
    ) -> None:
        """Should pay invoice."""
        mock_invoice_response["status"] = "paid"
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_invoice_response

            result = await stripe_client.pay_invoice("inv_test123")

            mock.assert_called_once_with("POST", "/invoices/inv_test123/pay")
            assert result["status"] == "paid"


class TestVoidInvoice:
    """Tests for void_invoice method."""

    @pytest.mark.asyncio
    async def test_voids_invoice(
        self,
        stripe_client: StripeClient,
        mock_invoice_response: dict[str, Any],
    ) -> None:
        """Should void invoice."""
        mock_invoice_response["status"] = "void"
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_invoice_response

            result = await stripe_client.void_invoice("inv_test123")

            mock.assert_called_once_with("POST", "/invoices/inv_test123/void")
            assert result["status"] == "void"


class TestCreateSubscription:
    """Tests for create_subscription method."""

    @pytest.mark.asyncio
    async def test_creates_subscription(
        self,
        stripe_client: StripeClient,
        mock_subscription_response: dict[str, Any],
    ) -> None:
        """Should create subscription."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_subscription_response

            result = await stripe_client.create_subscription(
                customer_id="cus_test123",
                price_id="price_test123",
            )

            mock.assert_called_once()
            call_args = mock.call_args
            assert call_args[0] == ("POST", "/subscriptions")
            data = call_args[1]["data"]
            assert data["customer"] == "cus_test123"
            assert data["items[0][price]"] == "price_test123"
            assert result["id"] == "sub_test123"

    @pytest.mark.asyncio
    async def test_creates_subscription_with_trial(
        self,
        stripe_client: StripeClient,
        mock_subscription_response: dict[str, Any],
    ) -> None:
        """Should create subscription with trial period."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_subscription_response

            await stripe_client.create_subscription(
                customer_id="cus_test123",
                price_id="price_test123",
                trial_period_days=14,
            )

            data = mock.call_args[1]["data"]
            assert data["trial_period_days"] == 14


class TestGetSubscription:
    """Tests for get_subscription method."""

    @pytest.mark.asyncio
    async def test_retrieves_subscription(
        self,
        stripe_client: StripeClient,
        mock_subscription_response: dict[str, Any],
    ) -> None:
        """Should retrieve subscription by ID."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_subscription_response

            result = await stripe_client.get_subscription("sub_test123")

            mock.assert_called_once_with("GET", "/subscriptions/sub_test123")
            assert result["id"] == "sub_test123"


class TestCancelSubscription:
    """Tests for cancel_subscription method."""

    @pytest.mark.asyncio
    async def test_cancels_subscription_immediately(
        self,
        stripe_client: StripeClient,
        mock_subscription_response: dict[str, Any],
    ) -> None:
        """Should cancel subscription immediately."""
        mock_subscription_response["status"] = "canceled"
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_subscription_response

            result = await stripe_client.cancel_subscription("sub_test123")

            mock.assert_called_once_with("DELETE", "/subscriptions/sub_test123")
            assert result["status"] == "canceled"

    @pytest.mark.asyncio
    async def test_cancels_subscription_at_period_end(
        self,
        stripe_client: StripeClient,
        mock_subscription_response: dict[str, Any],
    ) -> None:
        """Should cancel subscription at period end."""
        mock_subscription_response["cancel_at_period_end"] = True
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_subscription_response

            result = await stripe_client.cancel_subscription(
                "sub_test123",
                at_period_end=True,
            )

            mock.assert_called_once_with(
                "POST",
                "/subscriptions/sub_test123",
                data={"cancel_at_period_end": "true"},
            )
            assert result["cancel_at_period_end"] is True


class TestCreateInvoiceItem:
    """Tests for create_invoice_item method."""

    @pytest.mark.asyncio
    async def test_creates_invoice_item(
        self,
        stripe_client: StripeClient,
        mock_invoice_item_response: dict[str, Any],
    ) -> None:
        """Should create invoice item."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_invoice_item_response

            result = await stripe_client.create_invoice_item(
                customer_id="cus_test123",
                amount=2500,
                description="Test item",
            )

            mock.assert_called_once()
            data = mock.call_args[1]["data"]
            assert data["customer"] == "cus_test123"
            assert data["amount"] == 2500
            assert data["description"] == "Test item"
            assert result["id"] == "ii_test123"


class TestListInvoices:
    """Tests for list_invoices method."""

    @pytest.mark.asyncio
    async def test_lists_invoices(
        self,
        stripe_client: StripeClient,
        mock_list_response: dict[str, Any],
    ) -> None:
        """Should list invoices."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_list_response

            result = await stripe_client.list_invoices()

            mock.assert_called_once_with("GET", "/invoices", params={"limit": 10})
            assert result["object"] == "list"

    @pytest.mark.asyncio
    async def test_lists_invoices_with_filters(
        self,
        stripe_client: StripeClient,
        mock_list_response: dict[str, Any],
    ) -> None:
        """Should list invoices with filters."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_list_response

            await stripe_client.list_invoices(
                customer_id="cus_test123",
                status="paid",
                limit=25,
            )

            mock.assert_called_once_with(
                "GET",
                "/invoices",
                params={
                    "limit": 25,
                    "customer": "cus_test123",
                    "status": "paid",
                },
            )


class TestListSubscriptions:
    """Tests for list_subscriptions method."""

    @pytest.mark.asyncio
    async def test_lists_subscriptions(
        self,
        stripe_client: StripeClient,
        mock_list_response: dict[str, Any],
    ) -> None:
        """Should list subscriptions."""
        with patch.object(
            stripe_client,
            "_request_with_retry",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_list_response

            result = await stripe_client.list_subscriptions()

            mock.assert_called_once_with("GET", "/subscriptions", params={"limit": 10})
            assert result["object"] == "list"


class TestWebhookSignatureVerification:
    """Tests for verify_webhook_signature method."""

    def test_verifies_valid_signature(
        self,
        stripe_client_with_webhook: StripeClient,
        valid_webhook_payload: bytes,
        valid_webhook_signature: str,
    ) -> None:
        """Should return True for valid signature."""
        result = stripe_client_with_webhook.verify_webhook_signature(
            payload=valid_webhook_payload,
            signature=valid_webhook_signature,
        )
        assert result is True

    def test_rejects_invalid_signature(
        self,
        stripe_client_with_webhook: StripeClient,
        valid_webhook_payload: bytes,
        invalid_webhook_signature: str,
    ) -> None:
        """Should return False for invalid signature."""
        result = stripe_client_with_webhook.verify_webhook_signature(
            payload=valid_webhook_payload,
            signature=invalid_webhook_signature,
        )
        assert result is False

    def test_rejects_expired_signature(
        self,
        stripe_client_with_webhook: StripeClient,
        valid_webhook_payload: bytes,
        expired_webhook_signature: str,
    ) -> None:
        """Should return False for expired timestamp."""
        result = stripe_client_with_webhook.verify_webhook_signature(
            payload=valid_webhook_payload,
            signature=expired_webhook_signature,
        )
        assert result is False

    def test_rejects_missing_timestamp(
        self,
        stripe_client_with_webhook: StripeClient,
        valid_webhook_payload: bytes,
    ) -> None:
        """Should return False for missing timestamp."""
        result = stripe_client_with_webhook.verify_webhook_signature(
            payload=valid_webhook_payload,
            signature="v1=somesignature",
        )
        assert result is False

    def test_raises_without_webhook_secret(
        self,
        stripe_client: StripeClient,
        valid_webhook_payload: bytes,
        valid_webhook_signature: str,
    ) -> None:
        """Should raise ValueError when webhook secret not configured."""
        with pytest.raises(ValueError, match="Webhook secret not configured"):
            stripe_client.verify_webhook_signature(
                payload=valid_webhook_payload,
                signature=valid_webhook_signature,
            )

    def test_handles_invalid_timestamp_format(
        self,
        stripe_client_with_webhook: StripeClient,
        valid_webhook_payload: bytes,
    ) -> None:
        """Should return False for invalid timestamp format."""
        result = stripe_client_with_webhook.verify_webhook_signature(
            payload=valid_webhook_payload,
            signature="t=invalid,v1=somesignature",
        )
        assert result is False


class TestRetryLogic:
    """Tests for retry logic in _request_with_retry."""

    @pytest.mark.asyncio
    async def test_retries_on_timeout(
        self,
        mock_customer_response: dict[str, Any],
    ) -> None:
        """Should retry on timeout and eventually succeed."""
        # Create a client with minimal retry delay for testing
        client = StripeClient(api_key="test", max_retries=2, retry_delay=0.01)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_customer_response
        mock_response.headers = {}

        call_count = 0

        async def mock_request(*_args: Any, **_kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("Timeout")
            return mock_response

        # Create a mock httpx client and set it on the internal _client attribute
        mock_http_client = MagicMock(spec=httpx.AsyncClient)
        mock_http_client.request = mock_request
        client._client = mock_http_client

        result = await client._request_with_retry("POST", "/customers", data={})

        assert call_count == 2
        assert result["id"] == "cus_test123"

        client._client = None  # Clean up

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit(
        self,
        mock_customer_response: dict[str, Any],
    ) -> None:
        """Should retry on 429 rate limit."""
        client = StripeClient(api_key="test", max_retries=2, retry_delay=0.01)

        call_count = 0

        def create_response(status_code: int) -> MagicMock:
            response = MagicMock()
            response.status_code = status_code
            response.headers = {}
            if status_code == 200:
                response.json.return_value = mock_customer_response
            else:
                response.json.return_value = {"error": {"message": "Rate limited"}}
            return response

        async def mock_request(*_args: Any, **_kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return create_response(429)
            return create_response(200)

        mock_http_client = MagicMock(spec=httpx.AsyncClient)
        mock_http_client.request = mock_request
        client._client = mock_http_client

        result = await client._request_with_retry("POST", "/customers", data={})

        assert call_count == 2
        assert result["id"] == "cus_test123"

        client._client = None

    @pytest.mark.asyncio
    async def test_fails_after_max_retries(self, stripe_api_key: str) -> None:
        """Should fail after exhausting retries."""
        client = StripeClient(api_key=stripe_api_key, max_retries=2, retry_delay=0.01)

        async def mock_request(*_args: Any, **_kwargs: Any) -> None:
            raise httpx.TimeoutException("Timeout")

        mock_http_client = MagicMock(spec=httpx.AsyncClient)
        mock_http_client.request = mock_request
        client._client = mock_http_client

        with pytest.raises(StripeAPIError) as exc_info:
            await client._request_with_retry("POST", "/customers", data={})

        assert "timeout" in exc_info.value.message.lower()

        client._client = None


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_handles_api_error(
        self,
        stripe_client: StripeClient,
        mock_error_response: dict[str, Any],
    ) -> None:
        """Should raise StripeAPIError on API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = mock_error_response
        mock_response.headers = {}

        async def mock_request(*_args: Any, **_kwargs: Any) -> MagicMock:
            return mock_response

        mock_http_client = MagicMock(spec=httpx.AsyncClient)
        mock_http_client.request = mock_request
        stripe_client._client = mock_http_client

        with pytest.raises(StripeAPIError) as exc_info:
            await stripe_client._request_with_retry("GET", "/customers/invalid")

        error = exc_info.value
        assert error.status_code == 404
        assert error.error_type == "invalid_request_error"
        assert error.error_code == "resource_missing"
        assert "No such customer" in error.message

        stripe_client._client = None

    @pytest.mark.asyncio
    async def test_handles_card_error(
        self,
        stripe_client: StripeClient,
        mock_card_error_response: dict[str, Any],
    ) -> None:
        """Should handle card errors."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.json.return_value = mock_card_error_response
        mock_response.headers = {}

        async def mock_request(*_args: Any, **_kwargs: Any) -> MagicMock:
            return mock_response

        mock_http_client = MagicMock(spec=httpx.AsyncClient)
        mock_http_client.request = mock_request
        stripe_client._client = mock_http_client

        with pytest.raises(StripeAPIError) as exc_info:
            await stripe_client._request_with_retry("POST", "/charges")

        error = exc_info.value
        assert error.error_type == "card_error"
        assert error.error_code == "card_declined"

        stripe_client._client = None

    @pytest.mark.asyncio
    async def test_handles_connection_error(
        self,
        stripe_api_key: str,
    ) -> None:
        """Should raise StripeAPIError on connection errors."""
        client = StripeClient(api_key=stripe_api_key, max_retries=0)

        async def mock_request(*_args: Any, **_kwargs: Any) -> None:
            raise httpx.ConnectError("Connection refused")

        mock_http_client = MagicMock(spec=httpx.AsyncClient)
        mock_http_client.request = mock_request
        client._client = mock_http_client

        with pytest.raises(StripeAPIError) as exc_info:
            await client._request_with_retry("POST", "/customers")

        assert "Connection error" in exc_info.value.message

        client._client = None


class TestStripeAPIError:
    """Tests for StripeAPIError exception."""

    def test_error_with_message_only(self) -> None:
        """Error should work with just message."""
        error = StripeAPIError(message="Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code is None

    def test_error_with_all_fields(self) -> None:
        """Error should include all fields in string."""
        error = StripeAPIError(
            message="Test error",
            status_code=400,
            error_type="invalid_request_error",
            error_code="parameter_missing",
        )
        error_str = str(error)
        assert "Test error" in error_str
        assert "invalid_request_error" in error_str
        assert "parameter_missing" in error_str
        assert "400" in error_str


class TestRateLimitTracking:
    """Tests for rate limit tracking."""

    @pytest.mark.asyncio
    async def test_tracks_rate_limit_headers(
        self,
        stripe_client: StripeClient,
        mock_customer_response: dict[str, Any],
    ) -> None:
        """Should track rate limit from headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_customer_response
        mock_response.headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "99",
        }

        async def mock_request(*_args: Any, **_kwargs: Any) -> MagicMock:
            return mock_response

        mock_http_client = MagicMock(spec=httpx.AsyncClient)
        mock_http_client.request = mock_request
        stripe_client._client = mock_http_client

        await stripe_client._request_with_retry("POST", "/customers", data={})

        assert stripe_client.rate_limit == 100
        assert stripe_client.rate_limit_remaining == 99

        stripe_client._client = None
