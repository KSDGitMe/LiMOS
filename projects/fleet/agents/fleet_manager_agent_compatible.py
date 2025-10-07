#!/usr/bin/env python3
"""
Fleet Management Agent - Standalone Compatible Version

This is a standalone implementation that demonstrates the Fleet Management Agent
functionality using the current Anthropic SDK structure without requiring the LiMOS
BaseAgent framework. This version can run independently.

Features:
- Vehicle details management (VIN, make, model, year, license plate)
- Insurance records tracking
- Maintenance and repair logs
- Fuel events with multi-modal input support
- Automatic cost calculations
- Accounting notifications
- SQLite database persistence
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
import logging

# Current SDK imports (will be replaced with anthropic.agents when available)
from anthropic import Anthropic
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Tool decorator for method discovery
def tool(func: Callable) -> Callable:
    """
    Tool decorator for method discovery.

    Marks methods as agent tools for auto-discovery and invocation.
    """
    func._is_tool = True
    func._tool_name = func.__name__
    return func


# Simple agent base class for standalone usage
class BaseAgent:
    """
    Simple base agent class for standalone usage.

    Provides tool discovery and basic agent structure without requiring
    external frameworks.
    """

    def __init__(self, name: str = "Agent", api_key: Optional[str] = None):
        self.name = name
        self.client = Anthropic(api_key=api_key) if api_key else None
        self.tools = self._discover_tools()

    def _discover_tools(self) -> Dict[str, Callable]:
        """Discover all methods decorated with @tool."""
        tools = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, '_is_tool'):
                tools[attr._tool_name] = attr
        return tools

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())


# Data Models (same as before)
class Vehicle(BaseModel):
    """Vehicle information model."""
    vehicle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vin: str = Field(..., description="Vehicle Identification Number")
    make: str = Field(..., description="Vehicle manufacturer")
    model: str = Field(..., description="Vehicle model")
    year: int = Field(..., ge=1900, le=2030, description="Model year")
    license_plate: str = Field(..., description="License plate number")
    color: Optional[str] = None
    engine_type: Optional[str] = None
    current_mileage: int = Field(default=0, description="Current vehicle mileage")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InsuranceRecord(BaseModel):
    """Insurance record model."""
    insurance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str = Field(..., description="Related vehicle ID")
    policy_number: str = Field(..., description="Insurance policy number")
    provider: str = Field(..., description="Insurance provider name")
    coverage_type: str = Field(..., description="Type of coverage")
    expiration_date: datetime = Field(..., description="Policy expiration date")
    premium_amount: Optional[Decimal] = None
    deductible: Optional[Decimal] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FuelEvent(BaseModel):
    """Fuel event record model with multi-modal support."""
    fuel_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str = Field(..., description="Related vehicle ID")
    gallons: Decimal = Field(..., gt=0, description="Gallons of fuel/consumable")
    odometer_reading: int = Field(..., ge=0, description="Current odometer reading")
    total_cost: Optional[Decimal] = Field(None, description="Total cost")
    price_per_gallon: Optional[Decimal] = Field(None, description="Price per gallon")
    fuel_type: str = Field(default="Gasoline", description="Type of fuel/consumable (Gasoline, Diesel, DEF)")
    is_consumable: bool = Field(default=False, description="True for maintenance consumables (DEF), False for fuel")
    consumption_rate: Optional[Decimal] = Field(None, description="Reserved for future non-MPG consumables")
    date_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    station_name: Optional[str] = Field(None, description="Station/supplier name")
    receipt_image_path: Optional[str] = Field(None, description="Path to receipt image")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __context):
        """Calculate missing cost fields and handle consumable types after model initialization."""
        # Calculate cost fields
        if self.total_cost is None and self.price_per_gallon is not None and self.gallons:
            self.total_cost = self.price_per_gallon * self.gallons
        elif self.price_per_gallon is None and self.total_cost is not None and self.gallons:
            self.price_per_gallon = self.total_cost / self.gallons

        # Determine if this is a non-fuel consumable (like DEF)
        fuel_type_upper = self.fuel_type.upper()

        if fuel_type_upper == "DEF":
            # DEF is a maintenance consumable tracked in MPG (like fuel) but categorized as maintenance
            self.is_consumable = True
            self.consumption_rate = None  # DEF efficiency calculated via MPG like fuel
        elif fuel_type_upper in ["GASOLINE", "DIESEL", "E85", "BIODIESEL"]:
            # These are actual fuels - tracked via MPG, categorized as fuel costs
            self.is_consumable = False
            self.consumption_rate = None  # Fuel efficiency calculated via MPG
        else:
            # Unknown type - default to fuel
            self.is_consumable = False
            self.consumption_rate = None


class MaintenanceEvent(BaseModel):
    """Maintenance event record model."""
    maintenance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str = Field(..., description="Related vehicle ID")
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    maintenance_type: str = Field(..., description="Type of maintenance")
    description: str = Field(..., description="Maintenance description")
    cost: Decimal = Field(..., ge=0, description="Maintenance cost")
    vendor: str = Field(..., description="Service provider")
    odometer_reading: Optional[int] = Field(None, ge=0, description="Odometer at service")
    next_service_due: Optional[int] = Field(None, description="Next service odometer")
    parts_replaced: Optional[List[str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RepairEvent(BaseModel):
    """Repair event record model."""
    repair_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str = Field(..., description="Related vehicle ID")
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    repair_type: str = Field(..., description="Type of repair")
    description: str = Field(..., description="Repair description")
    cost: Decimal = Field(..., ge=0, description="Repair cost")
    vendor: str = Field(..., description="Repair shop")
    odometer_reading: Optional[int] = Field(None, ge=0, description="Odometer at repair")
    warranty_info: Optional[str] = Field(None, description="Warranty information")
    severity: str = Field(default="Medium", description="Repair severity")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExpenseData(BaseModel):
    """Data model for accounting notifications."""
    expense_id: str
    vehicle_id: str
    expense_type: str  # 'fuel', 'maintenance', 'repair'
    amount: Decimal
    date: datetime
    vendor: Optional[str] = None
    description: str
    category: str
    tax_deductible: bool = True


class FleetDatabase:
    """Database manager for fleet records using SQLite."""

    def __init__(self, db_path: str = "fleet_management.db"):
        """Initialize database connection and create tables."""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Vehicles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    vehicle_id TEXT PRIMARY KEY,
                    vin TEXT UNIQUE NOT NULL,
                    make TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    license_plate TEXT NOT NULL,
                    color TEXT,
                    engine_type TEXT,
                    current_mileage INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Fuel events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fuel_events (
                    fuel_id TEXT PRIMARY KEY,
                    vehicle_id TEXT NOT NULL,
                    gallons DECIMAL NOT NULL,
                    odometer_reading INTEGER NOT NULL,
                    total_cost DECIMAL,
                    price_per_gallon DECIMAL,
                    fuel_type TEXT NOT NULL,
                    is_consumable BOOLEAN DEFAULT FALSE,
                    consumption_rate DECIMAL,
                    date_time TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    station_name TEXT,
                    receipt_image_path TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id)
                )
            """)

            # Maintenance events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_events (
                    maintenance_id TEXT PRIMARY KEY,
                    vehicle_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    maintenance_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    cost DECIMAL NOT NULL,
                    vendor TEXT NOT NULL,
                    odometer_reading INTEGER,
                    next_service_due INTEGER,
                    parts_replaced TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id)
                )
            """)

            # Repair events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repair_events (
                    repair_id TEXT PRIMARY KEY,
                    vehicle_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    repair_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    cost DECIMAL NOT NULL,
                    vendor TEXT NOT NULL,
                    odometer_reading INTEGER,
                    warranty_info TEXT,
                    severity TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id)
                )
            """)

            conn.commit()
            logger.info("Database initialized successfully")

    def add_vehicle(self, vehicle: Vehicle) -> bool:
        """Add a new vehicle to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO vehicles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vehicle.vehicle_id, vehicle.vin, vehicle.make, vehicle.model,
                    vehicle.year, vehicle.license_plate, vehicle.color,
                    vehicle.engine_type, 0, vehicle.created_at.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding vehicle: {e}")
            return False

    def add_fuel_event(self, fuel_event: FuelEvent) -> bool:
        """Add a fuel event to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO fuel_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fuel_event.fuel_id, fuel_event.vehicle_id, float(fuel_event.gallons),
                    fuel_event.odometer_reading,
                    float(fuel_event.total_cost) if fuel_event.total_cost else None,
                    float(fuel_event.price_per_gallon) if fuel_event.price_per_gallon else None,
                    fuel_event.fuel_type, fuel_event.is_consumable,
                    float(fuel_event.consumption_rate) if fuel_event.consumption_rate else None,
                    fuel_event.date_time.isoformat(),
                    fuel_event.latitude, fuel_event.longitude, fuel_event.station_name,
                    fuel_event.receipt_image_path, fuel_event.created_at.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding fuel event: {e}")
            return False

    def add_maintenance_event(self, maintenance_event: MaintenanceEvent) -> bool:
        """Add a maintenance event to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO maintenance_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    maintenance_event.maintenance_id, maintenance_event.vehicle_id,
                    maintenance_event.date.isoformat(), maintenance_event.maintenance_type,
                    maintenance_event.description, float(maintenance_event.cost),
                    maintenance_event.vendor, maintenance_event.odometer_reading,
                    maintenance_event.next_service_due,
                    json.dumps(maintenance_event.parts_replaced) if maintenance_event.parts_replaced else None,
                    maintenance_event.created_at.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding maintenance event: {e}")
            return False

    def add_repair_event(self, repair_event: RepairEvent) -> bool:
        """Add a repair event to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO repair_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    repair_event.repair_id, repair_event.vehicle_id,
                    repair_event.date.isoformat(), repair_event.repair_type,
                    repair_event.description, float(repair_event.cost),
                    repair_event.vendor, repair_event.odometer_reading,
                    repair_event.warranty_info, repair_event.severity,
                    repair_event.created_at.isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding repair event: {e}")
            return False

    def get_vehicle_fuel_efficiency(self, vehicle_id: str) -> Optional[float]:
        """Calculate average fuel efficiency for a vehicle."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT odometer_reading, gallons
                    FROM fuel_events
                    WHERE vehicle_id = ?
                    ORDER BY odometer_reading
                """, (vehicle_id,))

                records = cursor.fetchall()
                if len(records) < 2:
                    return None

                total_miles = records[-1][0] - records[0][0]
                total_gallons = sum(record[1] for record in records)

                if total_gallons > 0:
                    return total_miles / total_gallons
                return None
        except Exception as e:
            logger.error(f"Error calculating fuel efficiency: {e}")
            return None

    def get_vehicle_total_costs(self, vehicle_id: str) -> Dict[str, float]:
        """Get total costs by category for a vehicle."""
        costs = {'fuel': 0.0, 'maintenance': 0.0, 'repair': 0.0}

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Fuel costs (all actual fuels: gasoline, diesel, etc.)
                cursor.execute("""
                    SELECT SUM(total_cost) FROM fuel_events
                    WHERE vehicle_id = ? AND total_cost IS NOT NULL AND (is_consumable = FALSE OR is_consumable IS NULL)
                """, (vehicle_id,))
                fuel_cost = cursor.fetchone()[0]
                if fuel_cost:
                    costs['fuel'] = float(fuel_cost)

                # Maintenance costs (including regular maintenance)
                cursor.execute("""
                    SELECT SUM(cost) FROM maintenance_events WHERE vehicle_id = ?
                """, (vehicle_id,))
                maintenance_cost = cursor.fetchone()[0]
                maintenance_total = float(maintenance_cost) if maintenance_cost else 0.0

                # Non-fuel consumables like DEF (categorized as maintenance)
                cursor.execute("""
                    SELECT SUM(total_cost) FROM fuel_events
                    WHERE vehicle_id = ? AND total_cost IS NOT NULL AND is_consumable = TRUE
                """, (vehicle_id,))
                consumable_cost = cursor.fetchone()[0]
                consumable_total = float(consumable_cost) if consumable_cost else 0.0

                costs['maintenance'] = maintenance_total + consumable_total

                # Repair costs
                cursor.execute("""
                    SELECT SUM(cost) FROM repair_events WHERE vehicle_id = ?
                """, (vehicle_id,))
                repair_cost = cursor.fetchone()[0]
                if repair_cost:
                    costs['repair'] = float(repair_cost)

        except Exception as e:
            logger.error(f"Error calculating total costs: {e}")

        return costs

    def update_vehicle_mileage(self, vehicle_id: str, current_mileage: int) -> bool:
        """Update a vehicle's current mileage."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE vehicles SET current_mileage = ? WHERE vehicle_id = ?
                """, (current_mileage, vehicle_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating vehicle mileage: {e}")
            return False

    def get_mpg_since_last_fuel(self, vehicle_id: str, fuel_event_id: str) -> Optional[Dict[str, Any]]:
        """Calculate MPG since the last fuel event for a specific fuel event."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get current fuel event
                cursor.execute("""
                    SELECT odometer_reading, gallons, created_at
                    FROM fuel_events
                    WHERE fuel_id = ? AND vehicle_id = ?
                """, (fuel_event_id, vehicle_id))
                current_event = cursor.fetchone()

                if not current_event:
                    return None

                current_odometer, current_gallons, current_time = current_event

                # Get previous fuel event
                cursor.execute("""
                    SELECT odometer_reading, gallons
                    FROM fuel_events
                    WHERE vehicle_id = ? AND created_at < ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (vehicle_id, current_time))
                previous_event = cursor.fetchone()

                if not previous_event:
                    return None

                previous_odometer, previous_gallons = previous_event
                miles_driven = current_odometer - previous_odometer

                if previous_gallons > 0 and miles_driven > 0:
                    mpg = miles_driven / previous_gallons
                    return {
                        "mpg_since_last": mpg,
                        "miles_driven": miles_driven,
                        "gallons_used": previous_gallons,
                        "previous_odometer": previous_odometer,
                        "current_odometer": current_odometer
                    }
                return None
        except Exception as e:
            logger.error(f"Error calculating MPG since last fuel: {e}")
            return None

    def get_running_mpg(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Calculate running average MPG for a vehicle across all fuel events."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT odometer_reading, gallons
                    FROM fuel_events
                    WHERE vehicle_id = ?
                    ORDER BY odometer_reading
                """, (vehicle_id,))
                events = cursor.fetchall()

                if len(events) < 2:
                    return None

                first_odometer = events[0][0]
                last_odometer = events[-1][0]
                total_miles = last_odometer - first_odometer
                total_gallons = sum(event[1] for event in events[:-1])  # Exclude last event gallons

                if total_gallons > 0 and total_miles > 0:
                    running_mpg = total_miles / total_gallons
                    return {
                        "running_mpg": running_mpg,
                        "total_miles": total_miles,
                        "total_gallons": total_gallons,
                        "event_count": len(events),
                        "first_odometer": first_odometer,
                        "last_odometer": last_odometer
                    }
                return None
        except Exception as e:
            logger.error(f"Error calculating running MPG: {e}")
            return None

    def get_vehicle_fuel_events(self, vehicle_id: str) -> List[Dict[str, Any]]:
        """Get all fuel events for a vehicle ordered by odometer reading."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT fuel_id, gallons, odometer_reading, total_cost, price_per_gallon,
                           fuel_type, is_consumable, consumption_rate, date_time, latitude,
                           longitude, station_name, receipt_image_path, created_at
                    FROM fuel_events
                    WHERE vehicle_id = ?
                    ORDER BY odometer_reading
                """, (vehicle_id,))

                events = []
                for row in cursor.fetchall():
                    events.append({
                        'fuel_id': row[0],
                        'gallons': row[1],
                        'odometer_reading': row[2],
                        'total_cost': row[3],
                        'price_per_gallon': row[4],
                        'fuel_type': row[5],
                        'is_consumable': bool(row[6]),
                        'consumption_rate': row[7],
                        'date_time': row[8],
                        'latitude': row[9],
                        'longitude': row[10],
                        'station_name': row[11],
                        'receipt_image_path': row[12],
                        'created_at': row[13]
                    })
                return events
        except Exception as e:
            logger.error(f"Error getting vehicle fuel events: {e}")
            return []


class FleetManagerAgent(BaseAgent):
    """
    Fleet Management Agent - Compatible Implementation

    This agent manages vehicle operational records including fuel events,
    maintenance, repairs, and insurance tracking with automatic cost
    calculations and accounting notifications.
    """

    def __init__(self, name: str = "FleetManagerAgent", **kwargs):
        """Initialize the Fleet Manager Agent."""
        super().__init__(name=name, **kwargs)
        self.database = FleetDatabase()
        self.vehicles: Dict[str, Vehicle] = {}
        self.load_vehicles()
        logger.info(f"FleetManagerAgent '{name}' initialized")

    def load_vehicles(self):
        """Load existing vehicles from database."""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM vehicles")
                rows = cursor.fetchall()

                for row in rows:
                    vehicle = Vehicle(
                        vehicle_id=row[0], vin=row[1], make=row[2], model=row[3],
                        year=row[4], license_plate=row[5], color=row[6],
                        engine_type=row[7], created_at=datetime.fromisoformat(row[8]),
                        current_mileage=row[9] if len(row) > 9 and row[9] is not None else 0
                    )
                    self.vehicles[vehicle.vehicle_id] = vehicle

                logger.info(f"Loaded {len(self.vehicles)} vehicles from database")
        except Exception as e:
            logger.error(f"Error loading vehicles: {e}")

    @tool
    def add_vehicle(
        self,
        vin: str,
        make: str,
        model: str,
        year: int,
        license_plate: str,
        color: Optional[str] = None,
        engine_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a new vehicle to the fleet."""
        try:
            vehicle = Vehicle(
                vin=vin, make=make, model=model, year=year,
                license_plate=license_plate, color=color, engine_type=engine_type
            )

            if self.database.add_vehicle(vehicle):
                self.vehicles[vehicle.vehicle_id] = vehicle
                logger.info(f"Added vehicle: {make} {model} ({vin})")
                return {
                    "success": True,
                    "vehicle_id": vehicle.vehicle_id,
                    "message": f"Vehicle {make} {model} added successfully"
                }
            else:
                return {"success": False, "message": "Failed to add vehicle to database"}

        except Exception as e:
            logger.error(f"Error adding vehicle: {e}")
            return {"success": False, "message": str(e)}

    @tool
    def log_fuel_event(
        self,
        vehicle_id: str,
        gallons: float,
        odometer_reading: int,
        fuel_type: str = "Gasoline",
        total_cost: Optional[float] = None,
        price_per_gallon: Optional[float] = None,
        station_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        receipt_image_path: Optional[str] = None,
        consumption_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """Log a fuel event for a vehicle with multi-modal input support."""
        try:
            # Validate vehicle exists
            if vehicle_id not in self.vehicles:
                return {"success": False, "message": "Vehicle not found"}

            # Create fuel event
            fuel_event = FuelEvent(
                vehicle_id=vehicle_id,
                gallons=Decimal(str(gallons)),
                odometer_reading=odometer_reading,
                fuel_type=fuel_type,
                total_cost=Decimal(str(total_cost)) if total_cost else None,
                price_per_gallon=Decimal(str(price_per_gallon)) if price_per_gallon else None,
                station_name=station_name,
                latitude=latitude,
                longitude=longitude,
                receipt_image_path=receipt_image_path,
                consumption_rate=Decimal(str(consumption_rate)) if consumption_rate else None
            )

            # Save to database
            if self.database.add_fuel_event(fuel_event):
                # Calculate metrics
                fuel_efficiency = self.database.get_vehicle_fuel_efficiency(vehicle_id)
                total_costs = self.database.get_vehicle_total_costs(vehicle_id)

                # Prepare accounting notification
                if fuel_event.is_consumable:
                    # Non-fuel consumables like DEF are categorized as maintenance
                    expense_type = "maintenance"
                    category = "Vehicle Maintenance"
                    description = f"Consumable: {gallons} gallons of {fuel_type}"
                else:
                    # Regular fuels (gasoline, diesel, etc.)
                    expense_type = "fuel"
                    category = "Vehicle Fuel"
                    description = f"Fuel purchase: {gallons} gallons of {fuel_type}"

                accounting_data = ExpenseData(
                    expense_id=fuel_event.fuel_id,
                    vehicle_id=vehicle_id,
                    expense_type=expense_type,
                    amount=fuel_event.total_cost or Decimal('0'),
                    date=fuel_event.date_time,
                    vendor=station_name,
                    description=description,
                    category=category
                )

                # Notify accounting
                accounting_result = self.notify_accounting(accounting_data.model_dump())

                logger.info(f"Logged fuel event: {gallons} gallons for vehicle {vehicle_id}")

                return {
                    "success": True,
                    "fuel_id": fuel_event.fuel_id,
                    "calculations": {
                        "total_cost": float(fuel_event.total_cost) if fuel_event.total_cost else None,
                        "price_per_gallon": float(fuel_event.price_per_gallon) if fuel_event.price_per_gallon else None,
                        "fuel_efficiency_mpg": fuel_efficiency,
                        "total_fuel_costs": total_costs['fuel']
                    },
                    "accounting_notification": accounting_result,
                    "message": "Fuel event logged successfully"
                }
            else:
                return {"success": False, "message": "Failed to save fuel event"}

        except Exception as e:
            logger.error(f"Error logging fuel event: {e}")
            return {"success": False, "message": str(e)}

    @tool
    def log_maintenance_event(
        self,
        vehicle_id: str,
        maintenance_type: str,
        description: str,
        cost: float,
        vendor: str,
        odometer_reading: Optional[int] = None,
        next_service_due: Optional[int] = None,
        parts_replaced: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Log a maintenance event for a vehicle."""
        try:
            # Validate vehicle exists
            if vehicle_id not in self.vehicles:
                return {"success": False, "message": "Vehicle not found"}

            # Create maintenance event
            maintenance_event = MaintenanceEvent(
                vehicle_id=vehicle_id,
                maintenance_type=maintenance_type,
                description=description,
                cost=Decimal(str(cost)),
                vendor=vendor,
                odometer_reading=odometer_reading,
                next_service_due=next_service_due,
                parts_replaced=parts_replaced or []
            )

            # Save to database
            if self.database.add_maintenance_event(maintenance_event):
                # Calculate cost per mile if odometer available
                cost_per_mile = None
                if odometer_reading:
                    cost_per_mile = float(cost) / max(odometer_reading, 1)

                # Prepare accounting notification
                accounting_data = ExpenseData(
                    expense_id=maintenance_event.maintenance_id,
                    vehicle_id=vehicle_id,
                    expense_type="maintenance",
                    amount=maintenance_event.cost,
                    date=maintenance_event.date,
                    vendor=vendor,
                    description=f"Maintenance: {maintenance_type} - {description}",
                    category="Vehicle Maintenance"
                )

                # Notify accounting
                accounting_result = self.notify_accounting(accounting_data.model_dump())

                logger.info(f"Logged maintenance event: {maintenance_type} for vehicle {vehicle_id}")

                return {
                    "success": True,
                    "maintenance_id": maintenance_event.maintenance_id,
                    "calculations": {
                        "cost_per_mile": cost_per_mile,
                        "total_maintenance_costs": self.database.get_vehicle_total_costs(vehicle_id)['maintenance']
                    },
                    "accounting_notification": accounting_result,
                    "message": "Maintenance event logged successfully"
                }
            else:
                return {"success": False, "message": "Failed to save maintenance event"}

        except Exception as e:
            logger.error(f"Error logging maintenance event: {e}")
            return {"success": False, "message": str(e)}

    @tool
    def log_repair_event(
        self,
        vehicle_id: str,
        repair_type: str,
        description: str,
        cost: float,
        vendor: str,
        odometer_reading: Optional[int] = None,
        warranty_info: Optional[str] = None,
        severity: str = "Medium"
    ) -> Dict[str, Any]:
        """Log a repair event for a vehicle."""
        try:
            # Validate vehicle exists
            if vehicle_id not in self.vehicles:
                return {"success": False, "message": "Vehicle not found"}

            # Create repair event
            repair_event = RepairEvent(
                vehicle_id=vehicle_id,
                repair_type=repair_type,
                description=description,
                cost=Decimal(str(cost)),
                vendor=vendor,
                odometer_reading=odometer_reading,
                warranty_info=warranty_info,
                severity=severity
            )

            # Save to database
            if self.database.add_repair_event(repair_event):
                # Calculate metrics
                total_costs = self.database.get_vehicle_total_costs(vehicle_id)

                # Prepare accounting notification
                accounting_data = ExpenseData(
                    expense_id=repair_event.repair_id,
                    vehicle_id=vehicle_id,
                    expense_type="repair",
                    amount=repair_event.cost,
                    date=repair_event.date,
                    vendor=vendor,
                    description=f"Repair: {repair_type} - {description}",
                    category="Vehicle Repairs"
                )

                # Notify accounting
                accounting_result = self.notify_accounting(accounting_data.model_dump())

                logger.info(f"Logged repair event: {repair_type} for vehicle {vehicle_id}")

                return {
                    "success": True,
                    "repair_id": repair_event.repair_id,
                    "calculations": {
                        "total_repair_costs": total_costs['repair'],
                        "total_vehicle_costs": sum(total_costs.values()),
                        "severity": severity
                    },
                    "accounting_notification": accounting_result,
                    "message": "Repair event logged successfully"
                }
            else:
                return {"success": False, "message": "Failed to save repair event"}

        except Exception as e:
            logger.error(f"Error logging repair event: {e}")
            return {"success": False, "message": str(e)}

    @tool
    def notify_accounting(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Notify the Accounting Agent of a new expense (stub function)."""
        try:
            notification_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()

            # Log the notification
            logger.info(f"Accounting notification sent: {expense_data['expense_type']} expense of ${expense_data['amount']}")

            # Simulate processing
            processed_data = {
                "notification_id": notification_id,
                "timestamp": timestamp,
                "status": "processed",
                "expense_id": expense_data["expense_id"],
                "amount": float(expense_data["amount"]),
                "category": expense_data["category"],
                "tax_deductible": expense_data.get("tax_deductible", True),
                "processing_notes": "Expense categorized and added to fleet management account"
            }

            return {
                "success": True,
                "notification_id": notification_id,
                "status": "sent",
                "processed_data": processed_data,
                "message": "Accounting notification sent successfully"
            }

        except Exception as e:
            logger.error(f"Error sending accounting notification: {e}")
            return {
                "success": False,
                "message": f"Failed to notify accounting: {str(e)}"
            }

    @tool
    def update_vehicle_mileage(self, vehicle_id: str, current_mileage: int) -> Dict[str, Any]:
        """Update a vehicle's current mileage."""
        try:
            if vehicle_id not in self.vehicles:
                return {"success": False, "message": "Vehicle not found"}

            # Update vehicle mileage in database
            success = self.database.update_vehicle_mileage(vehicle_id, current_mileage)

            if success:
                # Update in-memory vehicle object
                self.vehicles[vehicle_id].current_mileage = current_mileage
                logger.info(f"Updated vehicle {vehicle_id} mileage to {current_mileage}")

                return {
                    "success": True,
                    "vehicle_id": vehicle_id,
                    "current_mileage": current_mileage,
                    "message": "Vehicle mileage updated successfully"
                }
            else:
                return {"success": False, "message": "Failed to update vehicle mileage"}

        except Exception as e:
            logger.error(f"Error updating vehicle mileage: {e}")
            return {"success": False, "message": str(e)}

    @tool
    def calculate_mpg_since_last_fuel(self, vehicle_id: str, fuel_event_id: str) -> Dict[str, Any]:
        """Calculate MPG since the last fuel event for a specific fuel event."""
        try:
            if vehicle_id not in self.vehicles:
                return {"success": False, "message": "Vehicle not found"}

            mpg_data = self.database.get_mpg_since_last_fuel(vehicle_id, fuel_event_id)

            if mpg_data:
                return {
                    "success": True,
                    "vehicle_id": vehicle_id,
                    "fuel_event_id": fuel_event_id,
                    "mpg_since_last": mpg_data["mpg_since_last"],
                    "miles_driven": mpg_data["miles_driven"],
                    "gallons_used": mpg_data["gallons_used"],
                    "previous_odometer": mpg_data["previous_odometer"],
                    "current_odometer": mpg_data["current_odometer"],
                    "message": "MPG calculation completed"
                }
            else:
                return {
                    "success": False,
                    "message": "Insufficient data for MPG calculation (need previous fuel event)"
                }

        except Exception as e:
            logger.error(f"Error calculating MPG since last fuel: {e}")
            return {"success": False, "message": str(e)}

    @tool
    def calculate_running_mpg(self, vehicle_id: str) -> Dict[str, Any]:
        """Calculate running average MPG for a vehicle across all fuel events."""
        try:
            if vehicle_id not in self.vehicles:
                return {"success": False, "message": "Vehicle not found"}

            running_mpg_data = self.database.get_running_mpg(vehicle_id)

            if running_mpg_data:
                return {
                    "success": True,
                    "vehicle_id": vehicle_id,
                    "running_average_mpg": running_mpg_data["running_mpg"],
                    "total_miles_driven": running_mpg_data["total_miles"],
                    "total_gallons_used": running_mpg_data["total_gallons"],
                    "fuel_events_count": running_mpg_data["event_count"],
                    "odometer_range": {
                        "first": running_mpg_data["first_odometer"],
                        "last": running_mpg_data["last_odometer"]
                    },
                    "message": "Running MPG calculation completed"
                }
            else:
                return {
                    "success": False,
                    "message": "Insufficient data for running MPG calculation (need multiple fuel events)"
                }

        except Exception as e:
            logger.error(f"Error calculating running MPG: {e}")
            return {"success": False, "message": str(e)}

    @tool
    def get_vehicle_summary(self, vehicle_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of a vehicle's records."""
        try:
            if vehicle_id not in self.vehicles:
                return {"success": False, "message": "Vehicle not found"}

            vehicle = self.vehicles[vehicle_id]
            costs = self.database.get_vehicle_total_costs(vehicle_id)
            fuel_efficiency = self.database.get_vehicle_fuel_efficiency(vehicle_id)

            return {
                "success": True,
                "vehicle": {
                    "vehicle_id": vehicle.vehicle_id,
                    "vin": vehicle.vin,
                    "make": vehicle.make,
                    "model": vehicle.model,
                    "year": vehicle.year,
                    "license_plate": vehicle.license_plate
                },
                "costs": costs,
                "fuel_efficiency_mpg": fuel_efficiency,
                "total_operating_costs": sum(costs.values())
            }

        except Exception as e:
            logger.error(f"Error getting vehicle summary: {e}")
            return {"success": False, "message": str(e)}


def main():
    """
    Example main script demonstrating Fleet Manager Agent functionality.
    """
    print("🚛 Fleet Manager Agent Demo (Compatible Version)")
    print("=" * 60)

    # Initialize the agent
    try:
        agent = FleetManagerAgent(name="DemoFleetManager")
        print("✅ Fleet Manager Agent initialized successfully")
        print(f"   Available tools: {', '.join(agent.get_available_tools())}")
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        return

    # Add a sample vehicle
    print("\n📋 Adding sample vehicle...")
    vehicle_result = agent.add_vehicle(
        vin="1HGCM82633A123456",
        make="Honda",
        model="Civic",
        year=2020,
        license_plate="ABC-1234",
        color="Blue",
        engine_type="4-Cylinder"
    )

    if vehicle_result["success"]:
        vehicle_id = vehicle_result["vehicle_id"]
        print(f"✅ Vehicle added: {vehicle_id}")
    else:
        print(f"❌ Failed to add vehicle: {vehicle_result['message']}")
        return

    # Log a fuel event
    print("\n⛽ Logging fuel event...")
    fuel_result = agent.log_fuel_event(
        vehicle_id=vehicle_id,
        gallons=12.5,
        odometer_reading=45000,
        fuel_type="Gasoline",
        price_per_gallon=3.25,
        station_name="Shell Station",
        latitude=40.7128,
        longitude=-74.0060
    )

    if fuel_result["success"]:
        print(f"✅ Fuel event logged: {fuel_result['fuel_id']}")
        if fuel_result['calculations']['total_cost']:
            print(f"   Total cost: ${fuel_result['calculations']['total_cost']:.2f}")
        else:
            print("   Total cost: Not calculated")
        print(f"   Accounting notification: {fuel_result['accounting_notification']['notification_id']}")
    else:
        print(f"❌ Failed to log fuel event: {fuel_result['message']}")

    # Log a maintenance event
    print("\n🔧 Logging maintenance event...")
    maintenance_result = agent.log_maintenance_event(
        vehicle_id=vehicle_id,
        maintenance_type="Oil Change",
        description="Regular oil change and filter replacement",
        cost=45.99,
        vendor="Quick Lube Plus",
        odometer_reading=45000,
        next_service_due=48000,
        parts_replaced=["Oil Filter", "Engine Oil"]
    )

    if maintenance_result["success"]:
        print(f"✅ Maintenance event logged: {maintenance_result['maintenance_id']}")
        print(f"   Total maintenance costs: ${maintenance_result['calculations']['total_maintenance_costs']:.2f}")
        print(f"   Accounting notification: {maintenance_result['accounting_notification']['notification_id']}")
    else:
        print(f"❌ Failed to log maintenance event: {maintenance_result['message']}")

    # Log a repair event
    print("\n🛠️ Logging repair event...")
    repair_result = agent.log_repair_event(
        vehicle_id=vehicle_id,
        repair_type="Brake Repair",
        description="Replaced front brake pads and rotors",
        cost=285.50,
        vendor="AutoCare Center",
        odometer_reading=45000,
        warranty_info="12 months or 12,000 miles",
        severity="Medium"
    )

    if repair_result["success"]:
        print(f"✅ Repair event logged: {repair_result['repair_id']}")
        print(f"   Total vehicle costs: ${repair_result['calculations']['total_vehicle_costs']:.2f}")
        print(f"   Accounting notification: {repair_result['accounting_notification']['notification_id']}")
    else:
        print(f"❌ Failed to log repair event: {repair_result['message']}")

    # Get vehicle summary
    print("\n📊 Vehicle Summary...")
    summary_result = agent.get_vehicle_summary(vehicle_id)

    if summary_result["success"]:
        summary = summary_result
        print(f"Vehicle: {summary['vehicle']['year']} {summary['vehicle']['make']} {summary['vehicle']['model']}")
        print(f"VIN: {summary['vehicle']['vin']}")
        print(f"License Plate: {summary['vehicle']['license_plate']}")
        print(f"Total Operating Costs: ${summary['total_operating_costs']:.2f}")
        print(f"  - Fuel: ${summary['costs']['fuel']:.2f}")
        print(f"  - Maintenance: ${summary['costs']['maintenance']:.2f}")
        print(f"  - Repairs: ${summary['costs']['repair']:.2f}")
        if summary['fuel_efficiency_mpg']:
            print(f"Fuel Efficiency: {summary['fuel_efficiency_mpg']:.1f} MPG")
    else:
        print(f"❌ Failed to get vehicle summary: {summary_result['message']}")

    print("\n🎉 Fleet Manager Agent demo completed!")
    print("\nDatabase Records Created:")
    print("- 1 Vehicle record")
    print("- 1 Fuel event with GPS coordinates")
    print("- 1 Maintenance event with parts tracking")
    print("- 1 Repair event with warranty info")
    print("- 3 Accounting notifications sent")
    print("\n💾 All data persisted to SQLite database: fleet_management.db")


if __name__ == "__main__":
    main()