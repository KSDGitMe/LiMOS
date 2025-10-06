"""
Base Agent System

This package provides the foundational components for the LiMOS agent system,
including the BaseAgent class, configuration management, and core utilities.
"""

from .agent import (
    AgentCapability,
    AgentConfig,
    AgentContext,
    AgentMetrics,
    AgentStatus,
    BaseAgent
)
from .config import (
    AgentConfigLoader,
    ConfigManager,
    EnvironmentConfig,
    config_manager
)
from .example_agent import EchoAgent, create_echo_agent

__all__ = [
    # Core agent classes
    "BaseAgent",
    "AgentConfig",
    "AgentContext",
    "AgentMetrics",
    "AgentStatus",
    "AgentCapability",

    # Configuration management
    "AgentConfigLoader",
    "ConfigManager",
    "EnvironmentConfig",
    "config_manager",

    # Example implementations
    "EchoAgent",
    "create_echo_agent",
]