"""Configuration module for Smarter Team backend."""

import logging
import os
from dataclasses import dataclass


def get_agent_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for an agent.

    Args:
        name: Logger name (e.g., "lead_generation", "integration.instantly")

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"smarter_team.{name}")

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


@dataclass
class Integration:
    """Configuration for an external integration."""

    name: str
    base_url: str
    api_key: str | None = None
    timeout: float = 30.0


# Environment configuration
class Settings:
    """Application settings loaded from environment."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./smarter_team.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()
