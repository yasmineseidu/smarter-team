import logging
import sys
from config.settings import settings


def setup_logging():
    level = logging.DEBUG if settings.debug else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Keep agent logs verbose
    logging.getLogger("agents").setLevel(logging.DEBUG)
    logging.getLogger("tasks").setLevel(logging.DEBUG)
    logging.getLogger("webhooks").setLevel(logging.DEBUG)


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get a logger specific to an agent."""
    return logging.getLogger(f"agents.{agent_name}")


def get_task_logger(task_name: str) -> logging.Logger:
    """Get a logger specific to a Celery task."""
    return logging.getLogger(f"tasks.{task_name}")


def get_webhook_logger(webhook_name: str) -> logging.Logger:
    """Get a logger specific to a webhook handler."""
    return logging.getLogger(f"webhooks.{webhook_name}")
