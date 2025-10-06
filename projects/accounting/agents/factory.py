"""
Agent Factory for Accounting Domain

This module provides factory functions for creating accounting-related agents
with proper configuration and initialization.
"""

import asyncio
from typing import Optional

from anthropic import Anthropic

from core.agents.base import AgentConfig, AgentCapability
from core.agents.base.config import config_manager
from core.agents.registry import agent_registry

from .receipt_agent import ReceiptAgent


async def create_receipt_agent(
    name: str = "ReceiptAgent",
    environment: str = "development",
    anthropic_client: Optional[Anthropic] = None,
    auto_register: bool = True,
    **config_overrides
) -> ReceiptAgent:
    """
    Factory function to create a configured ReceiptAgent.

    Args:
        name: Agent name
        environment: Environment configuration to use
        anthropic_client: Optional Anthropic client instance
        auto_register: Whether to automatically register with agent registry
        **config_overrides: Additional configuration parameters

    Returns:
        Configured and initialized ReceiptAgent instance
    """
    # Create configuration
    config = config_manager.create_agent_config(
        name=name,
        description="Specialized agent for processing receipt images and extracting structured data",
        capabilities=[
            AgentCapability.TEXT_PROCESSING,
            AgentCapability.IMAGE_ANALYSIS,
            AgentCapability.DOCUMENT_PARSING,
            AgentCapability.DATA_EXTRACTION,
            AgentCapability.API_INTEGRATION,
            AgentCapability.FILE_OPERATIONS
        ],
        environment=environment,
        max_turns=20,  # Receipt processing may need multiple iterations
        timeout_seconds=300,  # 5 minutes for complex receipts
        **config_overrides
    )

    # Create agent
    agent = ReceiptAgent(config, anthropic_client)

    # Initialize
    await agent.initialize()

    # Register with agent registry
    if auto_register:
        await agent_registry.register_agent(
            agent,
            tags={"accounting", "receipts", "image_processing"},
            metadata={
                "domain": "accounting",
                "type": "receipt_processor",
                "version": "1.0.0"
            }
        )

    return agent


async def create_accounting_agent_suite(
    environment: str = "development",
    anthropic_client: Optional[Anthropic] = None
) -> dict:
    """
    Create a suite of accounting agents.

    Args:
        environment: Environment configuration to use
        anthropic_client: Optional Anthropic client instance

    Returns:
        Dictionary of created agents
    """
    agents = {}

    # Create receipt agent
    agents['receipt_agent'] = await create_receipt_agent(
        name="AccountingReceiptAgent",
        environment=environment,
        anthropic_client=anthropic_client
    )

    # Future agents can be added here:
    # agents['expense_agent'] = await create_expense_agent(...)
    # agents['budget_agent'] = await create_budget_agent(...)
    # agents['tax_agent'] = await create_tax_agent(...)

    return agents


async def cleanup_accounting_agents(agents: dict) -> None:
    """
    Clean up all accounting agents.

    Args:
        agents: Dictionary of agents to clean up
    """
    cleanup_tasks = []
    for agent_name, agent in agents.items():
        cleanup_tasks.append(agent.cleanup())

    await asyncio.gather(*cleanup_tasks, return_exceptions=True)


# Pre-configured agent configurations for common use cases
RECEIPT_AGENT_CONFIGS = {
    "personal": {
        "name": "PersonalReceiptAgent",
        "description": "Receipt agent for personal expense tracking",
        "max_turns": 10,
        "timeout_seconds": 120
    },
    "business": {
        "name": "BusinessReceiptAgent",
        "description": "Receipt agent for business expense processing",
        "max_turns": 25,
        "timeout_seconds": 600,
        "debug": True
    },
    "high_volume": {
        "name": "HighVolumeReceiptAgent",
        "description": "Receipt agent optimized for high-volume processing",
        "max_turns": 15,
        "timeout_seconds": 180
    }
}