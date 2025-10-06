"""
Base Agent Class for LiMOS Multi-Agent System

This module provides the foundational BaseAgent class that all domain-specific
agents inherit from. It defines the core interface and common functionality
for agent lifecycle management, configuration, and execution.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field
from anthropic import Anthropic


class AgentStatus(str, Enum):
    """Agent execution status states."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"
    STOPPED = "stopped"


class AgentCapability(str, Enum):
    """Agent capability types."""
    TEXT_PROCESSING = "text_processing"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_PARSING = "document_parsing"
    DATA_EXTRACTION = "data_extraction"
    API_INTEGRATION = "api_integration"
    FILE_OPERATIONS = "file_operations"
    WEB_SCRAPING = "web_scraping"
    DATABASE_OPERATIONS = "database_operations"


class AgentConfig(BaseModel):
    """Agent configuration model."""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    version: str = "1.0.0"
    capabilities: List[AgentCapability] = Field(default_factory=list)
    max_turns: int = 10
    timeout_seconds: int = 300
    permission_mode: str = "ask"  # "ask", "acceptEdits", "reject"
    system_prompt: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    environment: str = "development"
    debug: bool = False


class AgentMetrics(BaseModel):
    """Agent execution metrics."""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    last_execution: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentContext(BaseModel):
    """Agent execution context."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all LiMOS agents.

    This class provides the foundational interface and common functionality
    that all domain-specific agents must implement. It handles agent lifecycle,
    configuration, metrics, and provides a standardized execution framework.
    """

    def __init__(self, config: AgentConfig, anthropic_client: Optional[Anthropic] = None):
        """
        Initialize the base agent.

        Args:
            config: Agent configuration
            anthropic_client: Optional Anthropic client instance
        """
        self.config = config
        self.status = AgentStatus.IDLE
        self.metrics = AgentMetrics()
        self.context: Optional[AgentContext] = None
        self.anthropic_client = anthropic_client
        self._initialized = False

        # Agent memory and state
        self._memory: Dict[str, Any] = {}
        self._context_history: List[AgentContext] = []

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate agent configuration."""
        if not self.config.name:
            raise ValueError("Agent name is required")

        if self.config.max_turns <= 0:
            raise ValueError("max_turns must be positive")

        if self.config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @property
    def agent_id(self) -> str:
        """Get the agent's unique identifier."""
        return self.config.agent_id

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self.config.name

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized

    @property
    def memory(self) -> Dict[str, Any]:
        """Get agent memory (read-only view)."""
        return self._memory.copy()

    async def initialize(self) -> None:
        """
        Initialize the agent.

        This method sets up the agent for execution, including any required
        resources, connections, or state preparation.
        """
        if self._initialized:
            return

        self.status = AgentStatus.INITIALIZING

        try:
            # Initialize Anthropic client if not provided
            if not self.anthropic_client:
                self.anthropic_client = Anthropic()

            # Perform agent-specific initialization
            await self._initialize()

            self._initialized = True
            self.status = AgentStatus.IDLE

        except Exception as e:
            self.status = AgentStatus.ERROR
            raise RuntimeError(f"Failed to initialize agent {self.name}: {str(e)}")

    @abstractmethod
    async def _initialize(self) -> None:
        """
        Agent-specific initialization logic.

        Subclasses must implement this method to perform any custom
        initialization required for their specific functionality.
        """
        pass

    async def execute(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute the agent with given input data.

        Args:
            input_data: Input data for agent processing
            **kwargs: Additional execution parameters

        Returns:
            Dict containing execution results

        Raises:
            RuntimeError: If agent is not initialized or execution fails
        """
        if not self._initialized:
            await self.initialize()

        # Create execution context
        context = AgentContext(
            input_data=input_data,
            metadata=kwargs,
            start_time=datetime.utcnow()
        )
        self.context = context
        self.status = AgentStatus.RUNNING

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute(input_data, **kwargs),
                timeout=self.config.timeout_seconds
            )

            # Update context and metrics
            context.output_data = result
            context.end_time = datetime.utcnow()
            self._update_metrics(success=True, context=context)
            self.status = AgentStatus.IDLE

            # Store context in history
            self._context_history.append(context)

            return result

        except asyncio.TimeoutError:
            error_msg = f"Agent execution timed out after {self.config.timeout_seconds} seconds"
            context.error_message = error_msg
            context.end_time = datetime.utcnow()
            self._update_metrics(success=False, context=context)
            self.status = AgentStatus.ERROR
            raise TimeoutError(error_msg)

        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            context.error_message = error_msg
            context.end_time = datetime.utcnow()
            self._update_metrics(success=False, context=context)
            self.status = AgentStatus.ERROR
            raise RuntimeError(error_msg)

    @abstractmethod
    async def _execute(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Agent-specific execution logic.

        Subclasses must implement this method to define their core functionality.

        Args:
            input_data: Input data for processing
            **kwargs: Additional execution parameters

        Returns:
            Dict containing execution results
        """
        pass

    def _update_metrics(self, success: bool, context: AgentContext) -> None:
        """Update agent execution metrics."""
        self.metrics.total_executions += 1
        self.metrics.last_execution = datetime.utcnow()

        if success:
            self.metrics.successful_executions += 1
        else:
            self.metrics.failed_executions += 1

        # Calculate execution time if available
        if context.start_time and context.end_time:
            execution_time = (context.end_time - context.start_time).total_seconds()

            # Update average execution time
            total_successful = self.metrics.successful_executions
            if total_successful > 0:
                current_avg = self.metrics.average_execution_time
                self.metrics.average_execution_time = (
                    (current_avg * (total_successful - 1) + execution_time) / total_successful
                )

        self.metrics.updated_at = datetime.utcnow()

    def set_memory(self, key: str, value: Any) -> None:
        """Set a value in agent memory."""
        self._memory[key] = value

    def get_memory(self, key: str, default: Any = None) -> Any:
        """Get a value from agent memory."""
        return self._memory.get(key, default)

    def clear_memory(self) -> None:
        """Clear agent memory."""
        self._memory.clear()

    def get_context_history(self, limit: Optional[int] = None) -> List[AgentContext]:
        """
        Get agent execution context history.

        Args:
            limit: Maximum number of contexts to return (most recent first)

        Returns:
            List of agent contexts
        """
        history = list(reversed(self._context_history))
        if limit:
            history = history[:limit]
        return history

    async def cleanup(self) -> None:
        """
        Cleanup agent resources.

        This method should be called when the agent is no longer needed
        to properly clean up any resources, connections, or state.
        """
        try:
            await self._cleanup()
            self.status = AgentStatus.STOPPED
            self._initialized = False
        except Exception as e:
            self.status = AgentStatus.ERROR
            raise RuntimeError(f"Failed to cleanup agent {self.name}: {str(e)}")

    async def _cleanup(self) -> None:
        """
        Agent-specific cleanup logic.

        Subclasses can override this method to perform custom cleanup.
        """
        pass

    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive agent status information."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status,
            "initialized": self._initialized,
            "config": self.config.model_dump(),
            "metrics": self.metrics.model_dump(),
            "current_context": self.context.model_dump() if self.context else None,
            "memory_keys": list(self._memory.keys()),
            "context_history_count": len(self._context_history)
        }

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id={self.agent_id}, name={self.name}, status={self.status})"