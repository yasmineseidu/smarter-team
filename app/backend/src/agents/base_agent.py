"""Base agent class for all Smarter Team agents."""

from abc import ABC, abstractmethod
from typing import Any

from src.config import get_agent_logger


class BaseAgent(ABC):
    """
    Base class for all Smarter Team agents.

    Provides common functionality for agent memory, logging,
    tool registration, and handoff protocols.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize the base agent.

        Args:
            name: Unique identifier for this agent type
            description: Human-readable description of the agent
        """
        self.name = name
        self.description = description
        self.logger = get_agent_logger(name)
        self._tools: list[dict] = []

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    async def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """
        Process an incoming task.

        Args:
            task: Task payload with type and parameters

        Returns:
            Result of task processing
        """
        pass

    def register_tool(
        self, tool: callable, name: str | None = None, description: str | None = None
    ) -> None:
        """
        Register a tool for this agent.

        Args:
            tool: The callable tool function
            name: Optional name for the tool
            description: Optional description of what the tool does
        """
        self._tools.append(
            {
                "function": tool,
                "name": name or getattr(tool, "__name__", "unknown"),
                "description": description or "",
            }
        )

    @property
    def tools(self) -> list[dict]:
        """Get all registered tools."""
        return self._tools

    async def handoff_to(
        self,
        target_agent: str,
        payload: dict[str, Any],
        priority: str = "normal",
    ) -> str:
        """
        Hand off a task to another agent.

        Args:
            target_agent: Name of the agent to hand off to
            payload: Data to pass to the target agent
            priority: Task priority (critical, high, normal, low)

        Returns:
            Task ID for tracking
        """
        from src.tasks.orchestration_tasks import agent_handoff

        self.logger.info(
            f"Handing off to {target_agent}",
            extra={"payload_keys": list(payload.keys()), "priority": priority},
        )

        task = agent_handoff.delay(
            from_agent=self.name,
            to_agent=target_agent,
            payload=payload,
            priority=priority,
        )

        return task.id

    def log_action(
        self,
        action: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an agent action for audit trail.

        Args:
            action: Action type (e.g., "lead.qualified", "email.sent")
            details: Additional details about the action
        """
        self.logger.info(
            f"Action: {action}",
            extra={"agent": self.name, "details": details or {}},
        )
        # TODO: Write to audit_log table

    async def get_memory_context(self, session_id: str) -> dict[str, Any]:
        """
        Retrieve memory context from Zep.

        Args:
            session_id: Session identifier (e.g., client_id, lead_id)

        Returns:
            Memory context including facts and recent messages
        """
        # TODO: Implement Zep memory retrieval
        return {"facts": [], "recent_messages": []}

    async def store_memory(
        self,
        session_id: str,
        fact: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Store a fact in long-term memory.

        Args:
            session_id: Session identifier
            fact: Fact to remember
            metadata: Additional metadata
        """
        # TODO: Implement Zep memory storage
        self.logger.debug(f"Storing memory: {fact[:50]}...")
