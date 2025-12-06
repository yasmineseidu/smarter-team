"""
Stripe integration client for payment processing.

This module provides an async client for interacting with the Stripe API,
supporting customer management, payment intents, invoices, and subscriptions.

Example:
    >>> import os
    >>> client = StripeClient(api_key=os.environ["STRIPE_API_KEY"])
    >>> customer = await client.create_customer(email="user@example.com")
    >>> print(customer["id"])
    cus_...

Note:
    Stripe API uses form-encoded requests (not JSON), so this client
    uses the `data` parameter for POST requests rather than `json`.
"""

import asyncio
import hashlib
import hmac
import time
from typing import Any

import httpx

from src.config import get_agent_logger
from src.integrations.base import BaseIntegrationClient


class StripeAPIError(Exception):
    """
    Exception raised for Stripe API errors.

    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code from the API response.
        error_type: Stripe error type (e.g., 'card_error', 'invalid_request_error').
        error_code: Stripe error code (e.g., 'card_declined').
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_type: str | None = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.error_type:
            parts.append(f"type={self.error_type}")
        if self.error_code:
            parts.append(f"code={self.error_code}")
        if self.status_code:
            parts.append(f"status={self.status_code}")
        return " | ".join(parts)


class StripeClient(BaseIntegrationClient):
    """
    Async client for Stripe API.

    Provides methods for payment processing including customer management,
    payment intents, invoices, and subscriptions with webhook signature
    verification.

    Example:
        >>> client = StripeClient(api_key="sk_test_...")
        >>> customer = await client.create_customer(
        ...     email="user@example.com",
        ...     name="John Doe"
        ... )
        >>> print(customer["id"])
        cus_...

    Attributes:
        webhook_secret: Secret for verifying webhook signatures.
        max_retries: Maximum number of retry attempts for transient errors.
        retry_delay: Base delay between retries in seconds.
    """

    # Stripe API uses form-encoded data, not JSON
    STRIPE_API_VERSION = "2024-12-18.acacia"

    # Retryable HTTP status codes
    RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

    def __init__(
        self,
        api_key: str,
        webhook_secret: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """
        Initialize the Stripe client.

        Args:
            api_key: Stripe API secret key (starts with sk_test_ or sk_live_).
            webhook_secret: Secret for webhook signature verification.
            max_retries: Maximum retry attempts for transient errors (default: 3).
            retry_delay: Base delay between retries in seconds (default: 1.0).

        Example:
            >>> client = StripeClient(
            ...     api_key=os.environ["STRIPE_API_KEY"],
            ...     webhook_secret=os.environ.get("STRIPE_WEBHOOK_SECRET"),
            ... )
        """
        super().__init__(
            name="stripe",
            base_url="https://api.stripe.com/v1",
            api_key=api_key,
            timeout=30.0,
        )
        self.webhook_secret = webhook_secret
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = get_agent_logger("integration.stripe")
        self.logger.info("Initialized Stripe client")

    @property
    def client(self) -> httpx.AsyncClient:
        """
        Get or create the HTTP client with Stripe-specific headers.

        Stripe uses Basic auth with the API key as username and empty password.

        Returns:
            Configured httpx AsyncClient instance.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=(self.api_key or "", ""),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Stripe-Version": self.STRIPE_API_VERSION,
                },
                timeout=self.timeout,
            )
        return self._client

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make an HTTP request with retry logic for transient errors.

        Implements exponential backoff for retryable errors.

        Args:
            method: HTTP method (GET, POST, DELETE).
            endpoint: API endpoint path.
            **kwargs: Additional request parameters.

        Returns:
            Response data as dictionary.

        Raises:
            StripeAPIError: On API errors after all retries exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"{method} {endpoint} (attempt {attempt + 1})")
                response = await self.client.request(method, endpoint, **kwargs)

                # Handle rate limiting
                if "X-RateLimit-Limit" in response.headers:
                    self.rate_limit = int(response.headers["X-RateLimit-Limit"])
                if "X-RateLimit-Remaining" in response.headers:
                    self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])

                # Check for retryable status codes and retry if attempts remain
                if (
                    response.status_code in self.RETRYABLE_STATUS_CODES
                    and attempt < self.max_retries
                ):
                    delay = self.retry_delay * (2**attempt)
                    self.logger.warning(
                        f"Retryable error {response.status_code}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue

                # Parse response
                data: dict[str, Any] = response.json()

                # Handle Stripe errors
                if response.status_code >= 400:
                    error_data = data.get("error", {})
                    raise StripeAPIError(
                        message=error_data.get("message", "Unknown Stripe error"),
                        status_code=response.status_code,
                        error_type=error_data.get("type"),
                        error_code=error_data.get("code"),
                    )

                return data

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2**attempt)
                    self.logger.warning(
                        f"Timeout error, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue
                self.logger.error(f"Request timeout after {self.max_retries + 1} attempts")
                raise StripeAPIError(
                    message=f"Request timeout: {e}",
                    status_code=408,
                ) from e

            except httpx.ConnectError as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2**attempt)
                    self.logger.warning(
                        f"Connection error, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue
                self.logger.error(f"Connection failed after {self.max_retries + 1} attempts")
                raise StripeAPIError(
                    message=f"Connection error: {e}",
                ) from e

            except StripeAPIError:
                raise

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                raise StripeAPIError(message=str(e)) from e

        # Should not reach here, but handle it anyway
        raise StripeAPIError(
            message=f"Request failed after {self.max_retries + 1} attempts: {last_error}"
        )

    async def create_customer(
        self,
        email: str,
        name: str | None = None,
        phone: str | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a new Stripe customer.

        Args:
            email: Customer's email address.
            name: Customer's full name.
            phone: Customer's phone number.
            description: Description of the customer.
            metadata: Set of key-value pairs for storing additional info.
            **kwargs: Additional Stripe customer parameters.

        Returns:
            Created customer object.

        Raises:
            StripeAPIError: If customer creation fails.

        Example:
            >>> customer = await client.create_customer(
            ...     email="john@example.com",
            ...     name="John Doe",
            ...     metadata={"company": "Acme Inc"}
            ... )
            >>> print(customer["id"])
            cus_...
        """
        data: dict[str, Any] = {"email": email}

        if name:
            data["name"] = name
        if phone:
            data["phone"] = phone
        if description:
            data["description"] = description
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        data.update(kwargs)

        self.logger.info(f"Creating customer: {email}")
        return await self._request_with_retry("POST", "/customers", data=data)

    async def get_customer(self, customer_id: str) -> dict[str, Any]:
        """
        Retrieve a customer by ID.

        Args:
            customer_id: The Stripe customer ID.

        Returns:
            Customer object.

        Raises:
            StripeAPIError: If customer retrieval fails.

        Example:
            >>> customer = await client.get_customer("cus_abc123")
            >>> print(customer["email"])
            john@example.com
        """
        self.logger.info(f"Retrieving customer: {customer_id}")
        return await self._request_with_retry("GET", f"/customers/{customer_id}")

    async def update_customer(
        self,
        customer_id: str,
        email: str | None = None,
        name: str | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Update an existing customer.

        Args:
            customer_id: The Stripe customer ID.
            email: New email address.
            name: New customer name.
            metadata: Updated metadata.
            **kwargs: Additional update parameters.

        Returns:
            Updated customer object.

        Raises:
            StripeAPIError: If update fails.
        """
        data: dict[str, Any] = {}

        if email:
            data["email"] = email
        if name:
            data["name"] = name
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        data.update(kwargs)

        self.logger.info(f"Updating customer: {customer_id}")
        return await self._request_with_retry("POST", f"/customers/{customer_id}", data=data)

    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: str | None = None,
        payment_method_types: list[str] | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a payment intent.

        Args:
            amount: Amount in cents (e.g., 1000 for $10.00).
            currency: Three-letter ISO currency code (default: 'usd').
            customer_id: Customer ID to associate with the payment.
            payment_method_types: Allowed payment method types (default: ['card']).
            description: Payment description.
            metadata: Additional metadata.
            **kwargs: Additional payment intent parameters.

        Returns:
            Created PaymentIntent object.

        Raises:
            StripeAPIError: If payment intent creation fails.

        Example:
            >>> payment = await client.create_payment_intent(
            ...     amount=5000,  # $50.00
            ...     currency="usd",
            ...     customer_id="cus_abc123",
            ...     description="Consulting services"
            ... )
            >>> print(payment["client_secret"])
            pi_..._secret_...
        """
        data: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
        }

        # Default payment method types
        method_types = payment_method_types or ["card"]
        for i, method in enumerate(method_types):
            data[f"payment_method_types[{i}]"] = method

        if customer_id:
            data["customer"] = customer_id
        if description:
            data["description"] = description
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        data.update(kwargs)

        self.logger.info(f"Creating payment intent: {amount} {currency}")
        return await self._request_with_retry("POST", "/payment_intents", data=data)

    async def get_payment_intent(self, payment_intent_id: str) -> dict[str, Any]:
        """
        Retrieve a payment intent by ID.

        Args:
            payment_intent_id: The payment intent ID.

        Returns:
            PaymentIntent object.

        Raises:
            StripeAPIError: If retrieval fails.
        """
        self.logger.info(f"Retrieving payment intent: {payment_intent_id}")
        return await self._request_with_retry("GET", f"/payment_intents/{payment_intent_id}")

    async def cancel_payment_intent(self, payment_intent_id: str) -> dict[str, Any]:
        """
        Cancel a payment intent.

        Args:
            payment_intent_id: The payment intent ID to cancel.

        Returns:
            Cancelled PaymentIntent object.

        Raises:
            StripeAPIError: If cancellation fails.
        """
        self.logger.info(f"Cancelling payment intent: {payment_intent_id}")
        return await self._request_with_retry(
            "POST", f"/payment_intents/{payment_intent_id}/cancel"
        )

    async def create_invoice(
        self,
        customer_id: str,
        auto_advance: bool = True,
        collection_method: str = "charge_automatically",
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create an invoice for a customer.

        Note: Invoices require invoice items to be added separately before
        finalizing, or you can use auto_advance=True with line items.

        Args:
            customer_id: Customer ID to invoice.
            auto_advance: Auto-finalize and charge (default: True).
            collection_method: How to collect payment ('charge_automatically' or 'send_invoice').
            description: Invoice description.
            metadata: Additional metadata.
            **kwargs: Additional invoice parameters.

        Returns:
            Created Invoice object.

        Raises:
            StripeAPIError: If invoice creation fails.

        Example:
            >>> invoice = await client.create_invoice(
            ...     customer_id="cus_abc123",
            ...     description="Monthly consulting services"
            ... )
            >>> print(invoice["id"])
            inv_...
        """
        data: dict[str, Any] = {
            "customer": customer_id,
            "auto_advance": "true" if auto_advance else "false",
            "collection_method": collection_method,
        }

        if description:
            data["description"] = description
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        data.update(kwargs)

        self.logger.info(f"Creating invoice for customer: {customer_id}")
        return await self._request_with_retry("POST", "/invoices", data=data)

    async def get_invoice(self, invoice_id: str) -> dict[str, Any]:
        """
        Retrieve an invoice by ID.

        Args:
            invoice_id: The invoice ID.

        Returns:
            Invoice object.

        Raises:
            StripeAPIError: If retrieval fails.
        """
        self.logger.info(f"Retrieving invoice: {invoice_id}")
        return await self._request_with_retry("GET", f"/invoices/{invoice_id}")

    async def finalize_invoice(self, invoice_id: str) -> dict[str, Any]:
        """
        Finalize a draft invoice.

        Args:
            invoice_id: The invoice ID to finalize.

        Returns:
            Finalized Invoice object.

        Raises:
            StripeAPIError: If finalization fails.
        """
        self.logger.info(f"Finalizing invoice: {invoice_id}")
        return await self._request_with_retry("POST", f"/invoices/{invoice_id}/finalize")

    async def pay_invoice(self, invoice_id: str) -> dict[str, Any]:
        """
        Pay an invoice.

        Args:
            invoice_id: The invoice ID to pay.

        Returns:
            Paid Invoice object.

        Raises:
            StripeAPIError: If payment fails.
        """
        self.logger.info(f"Paying invoice: {invoice_id}")
        return await self._request_with_retry("POST", f"/invoices/{invoice_id}/pay")

    async def void_invoice(self, invoice_id: str) -> dict[str, Any]:
        """
        Void an invoice.

        Args:
            invoice_id: The invoice ID to void.

        Returns:
            Voided Invoice object.

        Raises:
            StripeAPIError: If voiding fails.
        """
        self.logger.info(f"Voiding invoice: {invoice_id}")
        return await self._request_with_retry("POST", f"/invoices/{invoice_id}/void")

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        quantity: int = 1,
        trial_period_days: int | None = None,
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create a subscription for a customer.

        Args:
            customer_id: Customer ID to subscribe.
            price_id: Price ID for the subscription item.
            quantity: Number of units (default: 1).
            trial_period_days: Number of trial days.
            metadata: Additional metadata.
            **kwargs: Additional subscription parameters.

        Returns:
            Created Subscription object.

        Raises:
            StripeAPIError: If subscription creation fails.

        Example:
            >>> subscription = await client.create_subscription(
            ...     customer_id="cus_abc123",
            ...     price_id="price_xyz789",
            ...     trial_period_days=14
            ... )
            >>> print(subscription["id"])
            sub_...
        """
        data: dict[str, Any] = {
            "customer": customer_id,
            "items[0][price]": price_id,
            "items[0][quantity]": quantity,
        }

        if trial_period_days is not None:
            data["trial_period_days"] = trial_period_days
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        data.update(kwargs)

        self.logger.info(f"Creating subscription for customer: {customer_id}")
        return await self._request_with_retry("POST", "/subscriptions", data=data)

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """
        Retrieve a subscription by ID.

        Args:
            subscription_id: The subscription ID.

        Returns:
            Subscription object.

        Raises:
            StripeAPIError: If retrieval fails.
        """
        self.logger.info(f"Retrieving subscription: {subscription_id}")
        return await self._request_with_retry("GET", f"/subscriptions/{subscription_id}")

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = False,
    ) -> dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: The subscription ID to cancel.
            at_period_end: If True, cancel at end of billing period.

        Returns:
            Cancelled Subscription object.

        Raises:
            StripeAPIError: If cancellation fails.
        """
        self.logger.info(f"Cancelling subscription: {subscription_id}")

        if at_period_end:
            # Update subscription to cancel at period end
            return await self._request_with_retry(
                "POST",
                f"/subscriptions/{subscription_id}",
                data={"cancel_at_period_end": "true"},
            )

        # Immediate cancellation
        return await self._request_with_retry("DELETE", f"/subscriptions/{subscription_id}")

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        tolerance: int = 300,
    ) -> bool:
        """
        Verify a Stripe webhook signature.

        Uses HMAC-SHA256 to verify the webhook payload matches the signature
        sent by Stripe.

        Args:
            payload: Raw request body bytes.
            signature: Stripe-Signature header value.
            tolerance: Maximum age of event in seconds (default: 300).

        Returns:
            True if signature is valid, False otherwise.

        Raises:
            ValueError: If webhook_secret is not configured.

        Example:
            >>> is_valid = client.verify_webhook_signature(
            ...     payload=request.body,
            ...     signature=request.headers["Stripe-Signature"]
            ... )
            >>> if not is_valid:
            ...     raise HTTPException(status_code=400, detail="Invalid signature")
        """
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")

        # Parse signature header
        # Format: t=timestamp,v1=signature[,v1=signature...]
        parts = dict(part.split("=", 1) for part in signature.split(",") if "=" in part)

        timestamp_str = parts.get("t")
        if not timestamp_str:
            self.logger.warning("Missing timestamp in webhook signature")
            return False

        try:
            timestamp = int(timestamp_str)
        except ValueError:
            self.logger.warning("Invalid timestamp in webhook signature")
            return False

        # Check timestamp tolerance
        current_time = int(time.time())
        if abs(current_time - timestamp) > tolerance:
            self.logger.warning(f"Webhook timestamp outside tolerance: {current_time - timestamp}s")
            return False

        # Get all v1 signatures (Stripe may include multiple)
        signatures = [parts[k] for k in parts if k.startswith("v1")] or [parts.get("v1", "")]

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Compare signatures (constant-time comparison)
        for sig in signatures:
            if hmac.compare_digest(expected_signature, sig):
                self.logger.debug("Webhook signature verified")
                return True

        self.logger.warning("Webhook signature verification failed")
        return False

    async def create_invoice_item(
        self,
        customer_id: str,
        amount: int,
        currency: str = "usd",
        description: str | None = None,
        invoice_id: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create an invoice item.

        Args:
            customer_id: Customer ID.
            amount: Amount in cents.
            currency: Three-letter ISO currency code.
            description: Item description.
            invoice_id: Optional invoice ID to add item to.
            **kwargs: Additional parameters.

        Returns:
            Created InvoiceItem object.

        Raises:
            StripeAPIError: If creation fails.
        """
        data: dict[str, Any] = {
            "customer": customer_id,
            "amount": amount,
            "currency": currency,
        }

        if description:
            data["description"] = description
        if invoice_id:
            data["invoice"] = invoice_id

        data.update(kwargs)

        self.logger.info(f"Creating invoice item: {amount} {currency}")
        return await self._request_with_retry("POST", "/invoiceitems", data=data)

    async def list_invoices(
        self,
        customer_id: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        List invoices.

        Args:
            customer_id: Filter by customer.
            status: Filter by status ('draft', 'open', 'paid', 'uncollectible', 'void').
            limit: Maximum number of results (1-100, default: 10).

        Returns:
            List response with invoices.

        Raises:
            StripeAPIError: If listing fails.
        """
        params: dict[str, Any] = {"limit": limit}

        if customer_id:
            params["customer"] = customer_id
        if status:
            params["status"] = status

        self.logger.info("Listing invoices")
        return await self._request_with_retry("GET", "/invoices", params=params)

    async def list_subscriptions(
        self,
        customer_id: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        List subscriptions.

        Args:
            customer_id: Filter by customer.
            status: Filter by status ('active', 'past_due', 'canceled', etc.).
            limit: Maximum number of results (1-100, default: 10).

        Returns:
            List response with subscriptions.

        Raises:
            StripeAPIError: If listing fails.
        """
        params: dict[str, Any] = {"limit": limit}

        if customer_id:
            params["customer"] = customer_id
        if status:
            params["status"] = status

        self.logger.info("Listing subscriptions")
        return await self._request_with_retry("GET", "/subscriptions", params=params)
