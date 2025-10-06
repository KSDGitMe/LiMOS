#!/usr/bin/env python3
"""
Fleet Management Agent - Compatible Version

This is a forward-compatible implementation that demonstrates the Fleet Management Agent
functionality using the current Anthropic SDK structure. It's designed to be easily
migrated to the Claude 2.0 Agent SDK when available.

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


# Tool decorator simulation (will use @agent.tool when SDK is available)
def tool(func: Callable) -> Callable:
    """
    Tool decorator simulation for Claude 2.0 Agent SDK compatibility.

    This will be replaced with the official @agent.tool decorator when
    the Claude 2.0 Agent SDK is released.
    """
    func._is_tool = True
    func._tool_name = func.__name__
    return func


# Agent base class simulation (will inherit from anthropic.agents.Agent)
class BaseAgent:
    """
    Base agent class simulation for Claude 2.0 Agent SDK compatibility.

    This will be replaced with anthropic.agents.Agent when the SDK is released.
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
    gallons: Decimal = Field(..., gt=0, description="Gallons of fuel")
    odometer_reading: int = Field(..., ge=0, description="Current odometer reading")
    total_cost: Optional[Decimal] = Field(None, description="Total cost of fuel")
    price_per_gallon: Optional[Decimal] = Field(None, description="Price per gallon")
    fuel_type: str = Field(default="Gasoline", description="Type of fuel")
    date_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    station_name: Optional[str] = Field(None, description="Gas station name")
    receipt_image_path: Optional[str] = Field(None, description="Path to receipt image")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __context):
        """Calculate missing cost fields after model initialization."""
        if self.total_cost is None and self.price_per_gallon is not None and self.gallons:
            self.total_cost = self.price_per_gallon * self.gallons
        elif self.price_per_gallon is None and self.total_cost is not None and self.gallons:
            self.price_per_gallon = self.total_cost / self.gallons


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
                    INSERT INTO vehicles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vehicle.vehicle_id, vehicle.vin, vehicle.make, vehicle.model,
                    vehicle.year, vehicle.license_plate, vehicle.color,
                    vehicle.engine_type, vehicle.created_at.isoformat()
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
                    INSERT INTO fuel_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fuel_event.fuel_id, fuel_event.vehicle_id, float(fuel_event.gallons),
                    fuel_event.odometer_reading,
                    float(fuel_event.total_cost) if fuel_event.total_cost else None,
                    float(fuel_event.price_per_gallon) if fuel_event.price_per_gallon else None,
                    fuel_event.fuel_type, fuel_event.date_time.isoformat(),
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

                # Fuel costs
                cursor.execute("""
                    SELECT SUM(total_cost) FROM fuel_events WHERE vehicle_id = ? AND total_cost IS NOT NULL
                """, (vehicle_id,))
                fuel_cost = cursor.fetchone()[0]
                if fuel_cost:
                    costs['fuel'] = float(fuel_cost)

                # Maintenance costs
                cursor.execute("""
                    SELECT SUM(cost) FROM maintenance_events WHERE vehicle_id = ?
                """, (vehicle_id,))
                maintenance_cost = cursor.fetchone()[0]
                if maintenance_cost:
                    costs['maintenance'] = float(maintenance_cost)

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
                        engine_type=row[7], created_at=datetime.fromisoformat(row[8])
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
        receipt_image_path: Optional[str] = None
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
                receipt_image_path=receipt_image_path
            )

            # Save to database
            if self.database.add_fuel_event(fuel_event):
                # Calculate metrics
                fuel_efficiency = self.database.get_vehicle_fuel_efficiency(vehicle_id)
                total_costs = self.database.get_vehicle_total_costs(vehicle_id)

                # Prepare accounting notification
                accounting_data = ExpenseData(
                    expense_id=fuel_event.fuel_id,
                    vehicle_id=vehicle_id,
                    expense_type="fuel",
                    amount=fuel_event.total_cost or Decimal('0'),
                    date=fuel_event.date_time,
                    vendor=station_name,
                    description=f"Fuel purchase: {gallons} gallons of {fuel_type}",
                    category="Vehicle Fuel"
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