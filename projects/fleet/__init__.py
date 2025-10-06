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

from .agents.fleet_manager_agent import FleetManagerAgent, FleetDatabase
from .models.fleet_models import Vehicle, FuelEvent, MaintenanceEvent, RepairEvent, InsuranceRecord

__version__ = "1.0.0"
__all__ = [
    "FleetManagerAgent",
    "FleetDatabase",
    "Vehicle",
    "FuelEvent",
    "MaintenanceEvent",
    "RepairEvent",
    "InsuranceRecord"
]