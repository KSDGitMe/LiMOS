"""Fleet Management Agents Module"""

try:
    # Try to import the official Agent SDK version first
    from .fleet_manager_agent import FleetManagerAgent
except ImportError:
    # Fall back to compatible version
    from .fleet_manager_agent_compatible import FleetManagerAgent

__all__ = ["FleetManagerAgent"]