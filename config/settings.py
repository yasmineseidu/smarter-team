from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "smarter-team"
    app_env: str = "development"
    debug: bool = True
    secret_key: str

    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    # AI Services
    anthropic_api_key: str
    perplexity_api_key: str | None = None
    elevenlabs_api_key: str | None = None

    # Lead Generation
    instantly_api_key: str | None = None
    autobound_api_key: str | None = None
    icypeas_api_key: str | None = None
    findymail_api_key: str | None = None
    serper_api_key: str | None = None
    firecrawl_api_key: str | None = None

    # CRM & Project Management
    gohighlevel_api_key: str | None = None
    notion_api_key: str | None = None
    airtable_api_key: str | None = None
    clickup_api_key: str | None = None

    # Communication
    gmail_credentials_json: str | None = None
    cal_com_api_key: str | None = None

    # Payments
    stripe_api_key: str | None = None
    stripe_webhook_secret: str | None = None
    quickbooks_client_id: str | None = None
    quickbooks_client_secret: str | None = None

    # Documents
    pandadoc_api_key: str | None = None

    # Vector & Memory
    pinecone_api_key: str | None = None
    pinecone_environment: str | None = None
    zep_api_key: str | None = None

    # Voice
    retell_api_key: str | None = None

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
