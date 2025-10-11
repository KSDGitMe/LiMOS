"""Fleet Management Models"""

from .fleet_models import (
    # Enums
    FuelType,
    SeverityLevel,
    # Vehicle models
    Vehicle,
    VehicleCreate,
    VehicleBase,
    # Fuel event models
    FuelEvent,
    FuelEventCreate,
    FuelEventBase,
    # Maintenance event models
    MaintenanceEvent,
    MaintenanceEventCreate,
    MaintenanceEventBase,
    # Repair event models
    RepairEvent,
    RepairEventCreate,
    RepairEventBase,
    # Analytics models
    VehicleSummary,
    FleetSummary,
)

__all__ = [
    "FuelType",
    "SeverityLevel",
    "Vehicle",
    "VehicleCreate",
    "VehicleBase",
    "FuelEvent",
    "FuelEventCreate",
    "FuelEventBase",
    "MaintenanceEvent",
    "MaintenanceEventCreate",
    "MaintenanceEventBase",
    "RepairEvent",
    "RepairEventCreate",
    "RepairEventBase",
    "VehicleSummary",
    "FleetSummary",
]
