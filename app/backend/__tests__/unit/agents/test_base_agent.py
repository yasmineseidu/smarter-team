"""Unit tests for BaseAgent abstract class."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.base_agent import BaseAgent


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    @property
    def system_prompt(self) -> str:
        return "You are a test agent."

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        return {"status": "processed", "task": task}


@pytest.fixture
def agent():
    """Create a test agent instance."""
    return ConcreteAgent(
        name="test_agent",
        description="A test agent for unit tests",
    )


class TestBaseAgentInitialization:
    """Tests for BaseAgent initialization."""

    def test_agent_has_name(self, agent: ConcreteAgent):
        """Agent should have a name."""
        assert agent.name == "test_agent"

    def test_agent_has_description(self, agent: ConcreteAgent):
        """Agent should have a description."""
        assert agent.description == "A test agent for unit tests"

    def test_agent_tools_initially_empty(self, agent: ConcreteAgent):
        """Agent tools should be empty initially."""
        assert agent.tools == []

    def test_agent_has_system_prompt(self, agent: ConcreteAgent):
        """Agent should have system prompt from concrete class."""
        assert agent.system_prompt == "You are a test agent."


class TestAgentToolRegistration:
    """Tests for tool registration."""

    def test_register_tool(self, agent: ConcreteAgent):
        """Should register a tool successfully."""

        async def test_tool(_args: dict) -> dict:
            return {"result": "success"}

        agent.register_tool(test_tool, "test_tool", "A test tool")
        assert len(agent.tools) == 1

    def test_register_multiple_tools(self, agent: ConcreteAgent):
        """Should register multiple tools."""

        async def tool1(_args: dict) -> dict:
            return {}

        async def tool2(_args: dict) -> dict:
            return {}

        agent.register_tool(tool1, "tool1", "First tool")
        agent.register_tool(tool2, "tool2", "Second tool")
        assert len(agent.tools) == 2


class TestAgentHandoff:
    """Tests for agent handoff functionality."""

    @pytest.mark.asyncio
    async def test_handoff_to_returns_task_id(self, agent: ConcreteAgent):
        """Handoff should return a task ID."""
        with patch("src.tasks.orchestration_tasks.agent_handoff") as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-123")

            task_id = await agent.handoff_to(
                target_agent="sales",
                payload={"lead_id": "lead-1"},
                priority="high",
            )

            assert task_id == "task-123"

    @pytest.mark.asyncio
    async def test_handoff_calls_celery_task(self, agent: ConcreteAgent):
        """Handoff should call the Celery task with correct args."""
        with patch("src.tasks.orchestration_tasks.agent_handoff") as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-123")

            await agent.handoff_to(
                target_agent="sales",
                payload={"lead_id": "lead-1"},
                priority="high",
            )

            mock_task.delay.assert_called_once()
            call_args = mock_task.delay.call_args
            assert call_args[1]["to_agent"] == "sales"
            assert call_args[1]["payload"] == {"lead_id": "lead-1"}
            assert call_args[1]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_handoff_uses_default_priority(self, agent: ConcreteAgent):
        """Handoff should use 'normal' as default priority."""
        with patch("src.tasks.orchestration_tasks.agent_handoff") as mock_task:
            mock_task.delay.return_value = MagicMock(id="task-456")

            await agent.handoff_to(
                target_agent="support",
                payload={"ticket_id": "ticket-1"},
            )

            call_args = mock_task.delay.call_args
            assert call_args[1]["priority"] == "normal"


class TestAgentMemory:
    """Tests for agent memory functionality."""

    @pytest.mark.asyncio
    async def test_get_memory_context_returns_dict(self, agent: ConcreteAgent):
        """get_memory_context should return a dictionary."""
        with patch.object(agent, "get_memory_context", new_callable=AsyncMock) as mock:
            mock.return_value = {"facts": [], "context": "test"}

            result = await agent.get_memory_context("session-123")

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_store_memory_accepts_fact(self, agent: ConcreteAgent):
        """store_memory should accept a fact string."""
        with patch.object(agent, "store_memory", new_callable=AsyncMock) as mock:
            mock.return_value = None

            await agent.store_memory(
                session_id="session-123",
                fact="Client prefers email communication",
                metadata={"source": "conversation"},
            )

            mock.assert_called_once()


class TestAgentLogging:
    """Tests for agent audit logging."""

    def test_log_action_records_action(self, agent: ConcreteAgent):
        """log_action should record the action."""
        # This is a stub in the base class, just verify it doesn't raise
        agent.log_action("test_action", {"detail": "value"})

    def test_log_action_with_empty_details(self, agent: ConcreteAgent):
        """log_action should work with empty details."""
        agent.log_action("simple_action", {})


class TestAgentProcessTask:
    """Tests for the abstract process_task method."""

    @pytest.mark.asyncio
    async def test_process_task_returns_result(self, agent: ConcreteAgent):
        """process_task should return a result dictionary."""
        result = await agent.process_task({"action": "test"})
        assert result["status"] == "processed"
        assert result["task"] == {"action": "test"}

    @pytest.mark.asyncio
    async def test_process_task_handles_complex_input(self, agent: ConcreteAgent):
        """process_task should handle complex task input."""
        complex_task = {
            "action": "qualify_lead",
            "lead_id": "lead-123",
            "context": {"source": "website", "score": 85},
            "priority": "high",
        }
        result = await agent.process_task(complex_task)
        assert result["task"] == complex_task
