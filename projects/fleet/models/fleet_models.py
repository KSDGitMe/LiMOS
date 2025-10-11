"""
Pydantic Models for Fleet Management API

Defines data validation models for vehicles, fuel events, maintenance, and repairs.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class FuelType(str, Enum):
    """Fuel type options."""
    GASOLINE = "Gasoline"
    DIESEL = "Diesel"
    E85 = "E85"
    BIODIESEL = "Biodiesel"
    DEF = "DEF"  # Diesel Exhaust Fluid


class SeverityLevel(str, Enum):
    """Repair severity levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# ============================================================================
# VEHICLE MODELS
# ============================================================================

class VehicleBase(BaseModel):
    """Base vehicle model with common fields."""
    vin: str = Field(..., description="Vehicle Identification Number")
    make: str = Field(..., description="Vehicle manufacturer")
    model: str = Field(..., description="Vehicle model")
    year: int = Field(..., ge=1900, le=2100, description="Model year")
    license_plate: str = Field(..., description="License plate number")
    color: Optional[str] = Field(None, description="Vehicle color")
    engine_type: Optional[str] = Field(None, description="Engine type/configuration")


class VehicleCreate(VehicleBase):
    """Model for creating a new vehicle."""
    current_mileage: int = Field(0, ge=0, description="Current odometer reading")


class Vehicle(VehicleBase):
    """Complete vehicle model with generated fields."""
    vehicle_id: str = Field(..., description="Unique vehicle identifier")
    current_mileage: int = Field(0, description="Current odometer reading")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# ============================================================================
# FUEL EVENT MODELS
# ============================================================================

class FuelEventBase(BaseModel):
    """Base fuel event model."""
    gallons: Decimal = Field(..., gt=0, description="Gallons of fuel")
    odometer_reading: int = Field(..., ge=0, description="Odometer reading at fill-up")
    fuel_type: FuelType = Field(FuelType.GASOLINE, description="Type of fuel")
    total_cost: Optional[Decimal] = Field(None, ge=0, description="Total cost of fuel")
    price_per_gallon: Optional[Decimal] = Field(None, ge=0, description="Price per gallon")
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")
    station_name: Optional[str] = Field(None, description="Fuel station name")
    receipt_image_path: Optional[str] = Field(None, description="Path to receipt image")
    is_consumable: bool = Field(False, description="Is this a consumable like DEF?")
    consumption_rate: Optional[Decimal] = Field(None, description="Consumption rate (MPG)")


class FuelEventCreate(FuelEventBase):
    """Model for creating a new fuel event."""
    vehicle_id: str = Field(..., description="Vehicle identifier")
    date_time: Optional[datetime] = Field(None, description="Event date/time (defaults to now)")


class FuelEvent(FuelEventBase):
    """Complete fuel event model."""
    fuel_id: str = Field(..., description="Unique fuel event identifier")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    date_time: datetime = Field(..., description="Event date/time")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# ============================================================================
# MAINTENANCE EVENT MODELS
# ============================================================================

class MaintenanceEventBase(BaseModel):
    """Base maintenance event model."""
    maintenance_type: str = Field(..., description="Type of maintenance (Oil Change, Tire Rotation, etc.)")
    description: str = Field(..., description="Detailed description of maintenance")
    cost: Decimal = Field(..., ge=0, description="Cost of maintenance")
    vendor: str = Field(..., description="Service vendor/provider")
    odometer_reading: Optional[int] = Field(None, ge=0, description="Odometer reading at service")
    next_service_due: Optional[int] = Field(None, ge=0, description="Next service due at mileage")
    parts_replaced: Optional[str] = Field(None, description="JSON array of parts replaced")


class MaintenanceEventCreate(MaintenanceEventBase):
    """Model for creating a new maintenance event."""
    vehicle_id: str = Field(..., description="Vehicle identifier")
    date: Optional[datetime] = Field(None, description="Service date (defaults to today)")


class MaintenanceEvent(MaintenanceEventBase):
    """Complete maintenance event model."""
    maintenance_id: str = Field(..., description="Unique maintenance event identifier")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    date: datetime = Field(..., description="Service date")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# ============================================================================
# REPAIR EVENT MODELS
# ============================================================================

class RepairEventBase(BaseModel):
    """Base repair event model."""
    repair_type: str = Field(..., description="Type of repair (Engine, Transmission, Brakes, etc.)")
    description: str = Field(..., description="Detailed description of repair")
    cost: Decimal = Field(..., ge=0, description="Cost of repair")
    vendor: str = Field(..., description="Repair vendor/shop")
    severity: SeverityLevel = Field(..., description="Severity level of repair")
    odometer_reading: Optional[int] = Field(None, ge=0, description="Odometer reading at repair")
    warranty_info: Optional[str] = Field(None, description="Warranty information")


class RepairEventCreate(RepairEventBase):
    """Model for creating a new repair event."""
    vehicle_id: str = Field(..., description="Vehicle identifier")
    date: Optional[datetime] = Field(None, description="Repair date (defaults to today)")


class RepairEvent(RepairEventBase):
    """Complete repair event model."""
    repair_id: str = Field(..., description="Unique repair event identifier")
    vehicle_id: str = Field(..., description="Vehicle identifier")
    date: datetime = Field(..., description="Repair date")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class VehicleSummary(BaseModel):
    """Vehicle summary with analytics."""
    vehicle: Vehicle
    total_fuel_cost: Decimal
    total_maintenance_cost: Decimal
    total_repair_cost: Decimal
    total_operating_cost: Decimal
    average_mpg: Optional[Decimal]
    fuel_event_count: int
    maintenance_event_count: int
    repair_event_count: int
    cost_per_mile: Optional[Decimal]


class FleetSummary(BaseModel):
    """Fleet-wide summary statistics."""
    total_vehicles: int
    total_fuel_events: int
    total_maintenance_events: int
    total_repair_events: int
    total_fuel_cost: Decimal
    total_maintenance_cost: Decimal
    total_repair_cost: Decimal
    total_operating_cost: Decimal
    average_fleet_mpg: Optional[Decimal]
