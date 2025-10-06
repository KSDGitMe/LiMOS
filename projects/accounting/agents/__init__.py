"""
Accounting Agents

This package provides specialized agents for accounting and financial data processing,
including receipt processing, expense categorization, and financial analytics.
"""

from .receipt_agent import ReceiptAgent
from .factory import (
    create_receipt_agent,
    create_accounting_agent_suite,
    cleanup_accounting_agents,
    RECEIPT_AGENT_CONFIGS
)

__all__ = [
    # Core agents
    "ReceiptAgent",

    # Factory functions
    "create_receipt_agent",
    "create_accounting_agent_suite",
    "cleanup_accounting_agents",

    # Configurations
    "RECEIPT_AGENT_CONFIGS",
]