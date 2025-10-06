"""
Agent Registry System

This package provides agent registration, discovery, and lifecycle
management capabilities for the LiMOS multi-agent system.
"""

from .registry import (
    AgentRegistration,
    AgentRegistry,
    agent_registry
)

__all__ = [
    "AgentRegistration",
    "AgentRegistry",
    "agent_registry",
]