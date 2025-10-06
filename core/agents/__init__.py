"""
LiMOS Agent System

This package provides the complete agent framework for the LiMOS system,
including base agent classes, memory management, registry, and coordination.
"""

from .base import (
    BaseAgent,
    AgentCapability,
    AgentConfig,
    AgentContext,
    AgentMetrics,
    AgentStatus,
    EchoAgent,
    create_echo_agent,
    config_manager
)
from .memory import (
    AgentMemory,
    FileBackend,
    InMemoryBackend
)
from .registry import (
    AgentRegistry,
    agent_registry
)

__all__ = [
    # Core agent framework
    "BaseAgent",
    "AgentCapability",
    "AgentConfig",
    "AgentContext",
    "AgentMetrics",
    "AgentStatus",

    # Memory management
    "AgentMemory",
    "FileBackend",
    "InMemoryBackend",

    # Registry system
    "AgentRegistry",
    "agent_registry",

    # Configuration
    "config_manager",

    # Example implementations
    "EchoAgent",
    "create_echo_agent",
]