from dataclasses import dataclass


@dataclass
class WebhookConfig:
    name: str
    path: str
    secret_env_key: str | None = None
    verify_signature: bool = True


WEBHOOKS = {
    # Email & Lead Generation
    "instantly": WebhookConfig(
        name="Instantly.ai",
        path="/webhooks/instantly",
        secret_env_key="INSTANTLY_WEBHOOK_SECRET",
    ),
    "gohighlevel": WebhookConfig(
        name="GoHighLevel",
        path="/webhooks/gohighlevel",
        secret_env_key="GHL_WEBHOOK_SECRET",
    ),
    # Payments
    "stripe": WebhookConfig(
        name="Stripe",
        path="/webhooks/stripe",
        secret_env_key="STRIPE_WEBHOOK_SECRET",
    ),
    # Communication
    "gmail": WebhookConfig(
        name="Gmail",
        path="/webhooks/gmail",
        secret_env_key=None,  # Uses OAuth verification
        verify_signature=False,
    ),
    "cal_com": WebhookConfig(
        name="Cal.com",
        path="/webhooks/calcom",
        secret_env_key="CALCOM_WEBHOOK_SECRET",
    ),
    # Project Management
    "clickup": WebhookConfig(
        name="ClickUp",
        path="/webhooks/clickup",
        secret_env_key="CLICKUP_WEBHOOK_SECRET",
    ),
    "notion": WebhookConfig(
        name="Notion",
        path="/webhooks/notion",
        secret_env_key=None,
        verify_signature=False,
    ),
    # Voice
    "retell": WebhookConfig(
        name="Retell AI",
        path="/webhooks/retell",
        secret_env_key="RETELL_WEBHOOK_SECRET",
    ),
}
