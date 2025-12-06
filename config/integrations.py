from dataclasses import dataclass
from config.settings import settings


@dataclass
class Integration:
    name: str
    base_url: str
    api_key: str | None
    rate_limit: int  # requests per minute
    timeout: int = 30  # seconds


INTEGRATIONS = {
    # AI/LLM Services
    "anthropic": Integration(
        name="Anthropic Claude",
        base_url="https://api.anthropic.com",
        api_key=settings.anthropic_api_key,
        rate_limit=60,
    ),
    "perplexity": Integration(
        name="Perplexity",
        base_url="https://api.perplexity.ai",
        api_key=settings.perplexity_api_key,
        rate_limit=60,
    ),
    "elevenlabs": Integration(
        name="ElevenLabs",
        base_url="https://api.elevenlabs.io",
        api_key=settings.elevenlabs_api_key,
        rate_limit=60,
    ),
    # Lead Generation
    "instantly": Integration(
        name="Instantly.ai",
        base_url="https://api.instantly.ai/api/v1",
        api_key=settings.instantly_api_key,
        rate_limit=60,
    ),
    "autobound": Integration(
        name="Autobound",
        base_url="https://api.autobound.ai",
        api_key=settings.autobound_api_key,
        rate_limit=30,
    ),
    "icypeas": Integration(
        name="Icypeas",
        base_url="https://app.icypeas.com/api",
        api_key=settings.icypeas_api_key,
        rate_limit=100,
    ),
    "findymail": Integration(
        name="Findymail",
        base_url="https://app.findymail.com/api",
        api_key=settings.findymail_api_key,
        rate_limit=100,
    ),
    "serper": Integration(
        name="Serper",
        base_url="https://google.serper.dev",
        api_key=settings.serper_api_key,
        rate_limit=100,
    ),
    "firecrawl": Integration(
        name="Firecrawl",
        base_url="https://api.firecrawl.dev",
        api_key=settings.firecrawl_api_key,
        rate_limit=60,
    ),
    # CRM & Project Management
    "gohighlevel": Integration(
        name="GoHighLevel",
        base_url="https://rest.gohighlevel.com",
        api_key=settings.gohighlevel_api_key,
        rate_limit=100,
    ),
    "notion": Integration(
        name="Notion",
        base_url="https://api.notion.com/v1",
        api_key=settings.notion_api_key,
        rate_limit=3,  # Notion has strict rate limits
    ),
    "airtable": Integration(
        name="Airtable",
        base_url="https://api.airtable.com/v0",
        api_key=settings.airtable_api_key,
        rate_limit=5,  # 5 requests per second
    ),
    "clickup": Integration(
        name="ClickUp",
        base_url="https://api.clickup.com/api/v2",
        api_key=settings.clickup_api_key,
        rate_limit=100,
    ),
    # Payments
    "stripe": Integration(
        name="Stripe",
        base_url="https://api.stripe.com/v1",
        api_key=settings.stripe_api_key,
        rate_limit=100,
    ),
    # Documents
    "pandadoc": Integration(
        name="PandaDoc",
        base_url="https://api.pandadoc.com/public/v1",
        api_key=settings.pandadoc_api_key,
        rate_limit=60,
    ),
    # Voice
    "retell": Integration(
        name="Retell AI",
        base_url="https://api.retellai.com",
        api_key=settings.retell_api_key,
        rate_limit=60,
    ),
    # Vector & Memory
    "pinecone": Integration(
        name="Pinecone",
        base_url="https://api.pinecone.io",
        api_key=settings.pinecone_api_key,
        rate_limit=100,
    ),
    "zep": Integration(
        name="Zep",
        base_url="https://api.getzep.com",
        api_key=settings.zep_api_key,
        rate_limit=100,
    ),
}
