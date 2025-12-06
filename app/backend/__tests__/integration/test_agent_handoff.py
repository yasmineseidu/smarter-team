"""Integration tests for agent handoff workflow."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.base_agent import BaseAgent


class LeadGenAgent(BaseAgent):
    """Mock lead generation agent for testing."""

    @property
    def system_prompt(self) -> str:
        return "You are a lead generation agent."

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        return {"status": "lead_qualified", "lead_id": task.get("lead_id")}


class SalesAgent(BaseAgent):
    """Mock sales agent for testing."""

    @property
    def system_prompt(self) -> str:
        return "You are a sales agent."

    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        return {"status": "deal_created", "deal_id": f"deal-{task.get('lead_id')}"}


@pytest.fixture
def lead_gen_agent():
    """Create a lead generation agent."""
    return LeadGenAgent(
        name="lead_generation",
        description="Generates and qualifies leads",
    )


@pytest.fixture
def sales_agent():
    """Create a sales agent."""
    return SalesAgent(
        name="sales",
        description="Handles sales process",
    )


class TestAgentHandoffWorkflow:
    """Integration tests for agent-to-agent handoff."""

    @pytest.mark.asyncio
    async def test_lead_to_sales_handoff(
        self, lead_gen_agent: LeadGenAgent, sales_agent: SalesAgent
    ):
        """Test handoff from lead generation to sales."""
        with patch("src.tasks.orchestration_tasks.agent_handoff") as mock_task:
            mock_task.delay.return_value = MagicMock(id="handoff-task-123")

            # 1. Lead gen agent qualifies a lead
            lead_result = await lead_gen_agent.process_task({"lead_id": "lead-001"})
            assert lead_result["status"] == "lead_qualified"

            # 2. Hand off to sales agent
            task_id = await lead_gen_agent.handoff_to(
                target_agent="sales",
                payload={
                    "lead_id": lead_result["lead_id"],
                    "qualification_status": "qualified",
                },
                priority="high",
            )

            # 3. Verify handoff was created
            assert task_id == "handoff-task-123"
            mock_task.delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_handoff_with_context_preservation(self, lead_gen_agent: LeadGenAgent):
        """Test that context is preserved in handoff."""
        with patch("src.tasks.orchestration_tasks.agent_handoff") as mock_task:
            mock_task.delay.return_value = MagicMock(id="context-task-456")

            context = {
                "lead_id": "lead-002",
                "source": "website",
                "score": 85,
                "notes": "High-value prospect from enterprise segment",
                "previous_interactions": ["email_opened", "demo_requested"],
            }

            await lead_gen_agent.handoff_to(
                target_agent="sales",
                payload=context,
                priority="critical",
            )

            # Verify context was passed correctly
            call_args = mock_task.delay.call_args[1]
            assert call_args["payload"] == context
            assert call_args["priority"] == "critical"

    @pytest.mark.asyncio
    async def test_priority_levels_in_handoff(self, lead_gen_agent: LeadGenAgent):
        """Test different priority levels in handoffs."""
        priorities = ["critical", "high", "normal", "low"]

        with patch("src.tasks.orchestration_tasks.agent_handoff") as mock_task:
            mock_task.delay.return_value = MagicMock(id="priority-task")

            for priority in priorities:
                await lead_gen_agent.handoff_to(
                    target_agent="sales",
                    payload={"test": True},
                    priority=priority,
                )

                call_args = mock_task.delay.call_args[1]
                assert call_args["priority"] == priority


class TestAgentMemoryIntegration:
    """Integration tests for agent memory across handoffs."""

    @pytest.mark.asyncio
    async def test_memory_context_retrieval(self, lead_gen_agent: LeadGenAgent):
        """Test retrieving memory context for a session."""
        expected_context = {
            "facts": [
                "Client prefers email communication",
                "Budget is $50,000-$100,000",
            ],
            "entities": ["John Smith", "Acme Corp"],
            "sentiment": "positive",
        }

        with patch.object(
            lead_gen_agent, "get_memory_context", new_callable=AsyncMock
        ) as mock_memory:
            mock_memory.return_value = expected_context

            context = await lead_gen_agent.get_memory_context("session-abc123")

            assert context == expected_context
            assert "facts" in context
            assert len(context["facts"]) == 2

    @pytest.mark.asyncio
    async def test_memory_storage_and_retrieval_flow(self, lead_gen_agent: LeadGenAgent):
        """Test storing and retrieving memory."""
        with (
            patch.object(lead_gen_agent, "store_memory", new_callable=AsyncMock) as mock_store,
            patch.object(lead_gen_agent, "get_memory_context", new_callable=AsyncMock) as mock_get,
        ):
            # Store a fact
            await lead_gen_agent.store_memory(
                session_id="session-xyz",
                fact="Client mentioned Q1 budget deadline",
                metadata={"source": "call", "confidence": 0.95},
            )

            mock_store.assert_called_once()

            # Retrieve context
            mock_get.return_value = {"facts": ["Client mentioned Q1 budget deadline"]}
            context = await lead_gen_agent.get_memory_context("session-xyz")

            assert "Client mentioned Q1 budget deadline" in context["facts"]


class TestMultiAgentWorkflow:
    """Integration tests for multi-agent workflows."""

    @pytest.mark.asyncio
    async def test_full_lead_to_deal_workflow(
        self, lead_gen_agent: LeadGenAgent, sales_agent: SalesAgent
    ):
        """Test complete workflow from lead to deal."""
        with patch("src.tasks.orchestration_tasks.agent_handoff") as mock_task:
            mock_task.delay.return_value = MagicMock(id="workflow-task-789")

            # Phase 1: Lead Generation
            lead_result = await lead_gen_agent.process_task(
                {
                    "lead_id": "lead-100",
                    "source": "inbound",
                    "company": "Tech Corp",
                }
            )
            assert lead_result["status"] == "lead_qualified"

            # Phase 2: Handoff to Sales
            handoff_id = await lead_gen_agent.handoff_to(
                target_agent="sales",
                payload={
                    "lead_id": lead_result["lead_id"],
                    "qualified": True,
                    "score": 90,
                },
                priority="high",
            )
            assert handoff_id is not None

            # Phase 3: Sales Processing (simulated)
            sales_result = await sales_agent.process_task(
                {
                    "lead_id": "lead-100",
                    "action": "create_deal",
                }
            )
            assert sales_result["status"] == "deal_created"
            assert "deal_id" in sales_result

    @pytest.mark.asyncio
    async def test_agent_logging_during_workflow(self, lead_gen_agent: LeadGenAgent):
        """Test that actions are logged during workflow."""
        # Log action (currently a stub, but should not raise)
        lead_gen_agent.log_action(
            action="lead_qualified",
            details={
                "lead_id": "lead-200",
                "score": 85,
                "timestamp": "2024-12-05T10:00:00Z",
            },
        )

        # Process task and log
        result = await lead_gen_agent.process_task({"lead_id": "lead-200"})
        lead_gen_agent.log_action(
            action="task_completed",
            details={"result": result},
        )

        # No exceptions means success
        assert True
