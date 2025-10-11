"""
Fleet Management Module for LiMOS

This module provides comprehensive fleet management capabilities including:
- Vehicle tracking and information management
- Fuel event logging with multi-modal input support
- Maintenance and repair event tracking
- Insurance record management
- Cost calculations and analytics
- Accounting system integration
"""

__version__ = "1.0.0"

# Agents are lazy-loaded to avoid importing heavy dependencies
# Import them explicitly when needed:
# from projects.fleet.agents.fleet_manager_agent import FleetManagerAgent

__all__ = ["__version__"]