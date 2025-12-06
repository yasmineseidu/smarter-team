"""Reusable fixtures for agent testing."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.base_agent import BaseAgent


class MockAgent(BaseAgent):
    """Mock agent for testing purposes."""

    def __init__(
        self,
        name: str = "mock_agent",
        description: str = "A mock agent for testing",
        mock_response: dict[str, Any] | None = None,
    ):
        super().__init__(name=name, description=description)
        self._mock_response = mock_response or {"status": "success"}

    @property
    def system_prompt(self) -> str:
        return f"You are {self.name}, a mock agent for testing."

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        return {**self._mock_response, "processed_task": task}


@pytest.fixture
def mock_agent():
    """Create a basic mock agent."""
    return MockAgent()


@pytest.fixture
def mock_lead_gen_agent():
    """Create a mock lead generation agent."""
    return MockAgent(
        name="lead_generation",
        description="Generates and qualifies leads",
        mock_response={"status": "qualified", "score": 85},
    )


@pytest.fixture
def mock_sales_agent():
    """Create a mock sales agent."""
    return MockAgent(
        name="sales",
        description="Handles sales process",
        mock_response={"status": "deal_created", "deal_value": 50000},
    )


@pytest.fixture
def mock_support_agent():
    """Create a mock support agent."""
    return MockAgent(
        name="support",
        description="Handles customer support",
        mock_response={"status": "resolved", "satisfaction": "high"},
    )


@pytest.fixture
def mock_celery_task():
    """Create a mock Celery task."""
    mock = MagicMock()
    mock.delay.return_value = MagicMock(
        id="mock-task-id-12345",
        status="PENDING",
    )
    return mock


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    mock.expire.return_value = True
    return mock


@pytest.fixture
def mock_claude_response():
    """Create a mock Claude API response."""
    return {
        "id": "msg_mock123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Mock response from Claude"}],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }


@pytest.fixture
def mock_zep_memory():
    """Create mock Zep memory context."""
    return {
        "facts": [
            "Client prefers email communication",
            "Budget is $50,000-$100,000",
            "Decision timeline is Q1 2025",
        ],
        "entities": [
            {"name": "John Smith", "type": "person", "role": "decision_maker"},
            {"name": "Acme Corp", "type": "organization"},
        ],
        "summary": "Qualified enterprise lead with strong buying signals",
        "sentiment": "positive",
    }


@pytest.fixture
def sample_lead_data():
    """Create sample lead data for testing."""
    return {
        "id": "lead-test-001",
        "email": "john@example.com",
        "company": "Test Corp",
        "name": "John Doe",
        "source": "website",
        "score": 75,
        "status": "new",
        "created_at": "2024-12-05T10:00:00Z",
    }


@pytest.fixture
def sample_task_payload():
    """Create sample task payload for handoffs."""
    return {
        "action": "qualify_lead",
        "lead_id": "lead-test-001",
        "context": {
            "source": "inbound",
            "previous_agent": "lead_generation",
            "priority": "high",
        },
        "metadata": {
            "timestamp": "2024-12-05T10:00:00Z",
            "correlation_id": "corr-12345",
        },
    }
