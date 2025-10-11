"""
Database Repositories for Fleet Management

Provides CRUD operations for all fleet management entities using raw SQL.
Each repository handles one entity type with full Create, Read, Update, Delete operations.
"""

import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json

from ..models.fleet_models import (
    Vehicle, VehicleCreate,
    FuelEvent, FuelEventCreate,
    MaintenanceEvent, MaintenanceEventCreate,
    RepairEvent, RepairEventCreate,
    VehicleSummary, FleetSummary
)


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert SQLite Row to dictionary."""
    return dict(row)


# ============================================================================
# VEHICLE REPOSITORY
# ============================================================================

class VehicleRepository:
    """Repository for vehicle CRUD operations."""

    @staticmethod
    def create(conn: sqlite3.Connection, vehicle: VehicleCreate) -> Vehicle:
        """Create a new vehicle."""
        vehicle_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vehicles (
                vehicle_id, vin, make, model, year, license_plate,
                color, engine_type, current_mileage, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vehicle_id, vehicle.vin, vehicle.make, vehicle.model, vehicle.year,
            vehicle.license_plate, vehicle.color, vehicle.engine_type,
            vehicle.current_mileage, created_at
        ))
        conn.commit()

        return VehicleRepository.get_by_id(conn, vehicle_id)

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, vehicle_id: str) -> Optional[Vehicle]:
        """Get vehicle by ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
        row = cursor.fetchone()

        if row:
            return Vehicle(**_row_to_dict(row))
        return None

    @staticmethod
    def get_all(conn: sqlite3.Connection, limit: int = 100, offset: int = 0) -> List[Vehicle]:
        """Get all vehicles with pagination."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM vehicles
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        return [Vehicle(**_row_to_dict(row)) for row in cursor.fetchall()]

    @staticmethod
    def update(conn: sqlite3.Connection, vehicle_id: str, vehicle: VehicleCreate) -> Optional[Vehicle]:
        """Update a vehicle."""
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE vehicles SET
                vin = ?, make = ?, model = ?, year = ?, license_plate = ?,
                color = ?, engine_type = ?, current_mileage = ?
            WHERE vehicle_id = ?
        """, (
            vehicle.vin, vehicle.make, vehicle.model, vehicle.year, vehicle.license_plate,
            vehicle.color, vehicle.engine_type, vehicle.current_mileage, vehicle_id
        ))
        conn.commit()

        if cursor.rowcount == 0:
            return None
        return VehicleRepository.get_by_id(conn, vehicle_id)

    @staticmethod
    def delete(conn: sqlite3.Connection, vehicle_id: str) -> bool:
        """Delete a vehicle."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
        conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def update_mileage(conn: sqlite3.Connection, vehicle_id: str, mileage: int) -> bool:
        """Update vehicle's current mileage."""
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE vehicles SET current_mileage = ? WHERE vehicle_id = ?
        """, (mileage, vehicle_id))
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# FUEL EVENT REPOSITORY
# ============================================================================

class FuelEventRepository:
    """Repository for fuel event CRUD operations."""

    @staticmethod
    def create(conn: sqlite3.Connection, fuel_event: FuelEventCreate) -> FuelEvent:
        """Create a new fuel event."""
        fuel_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        date_time = fuel_event.date_time.isoformat() if fuel_event.date_time else created_at

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO fuel_events (
                fuel_id, vehicle_id, gallons, odometer_reading, total_cost,
                price_per_gallon, fuel_type, is_consumable, consumption_rate,
                date_time, latitude, longitude, station_name, receipt_image_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fuel_id, fuel_event.vehicle_id, float(fuel_event.gallons), fuel_event.odometer_reading,
            float(fuel_event.total_cost) if fuel_event.total_cost else None,
            float(fuel_event.price_per_gallon) if fuel_event.price_per_gallon else None,
            fuel_event.fuel_type.value, fuel_event.is_consumable,
            float(fuel_event.consumption_rate) if fuel_event.consumption_rate else None,
            date_time, fuel_event.latitude, fuel_event.longitude,
            fuel_event.station_name, fuel_event.receipt_image_path, created_at
        ))
        conn.commit()

        # Update vehicle mileage
        VehicleRepository.update_mileage(conn, fuel_event.vehicle_id, fuel_event.odometer_reading)

        return FuelEventRepository.get_by_id(conn, fuel_id)

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, fuel_id: str) -> Optional[FuelEvent]:
        """Get fuel event by ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fuel_events WHERE fuel_id = ?", (fuel_id,))
        row = cursor.fetchone()

        if row:
            return FuelEvent(**_row_to_dict(row))
        return None

    @staticmethod
    def get_all(
        conn: sqlite3.Connection,
        vehicle_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FuelEvent]:
        """Get all fuel events with optional vehicle filter."""
        cursor = conn.cursor()

        if vehicle_id:
            cursor.execute("""
                SELECT * FROM fuel_events
                WHERE vehicle_id = ?
                ORDER BY date_time DESC
                LIMIT ? OFFSET ?
            """, (vehicle_id, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM fuel_events
                ORDER BY date_time DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        return [FuelEvent(**_row_to_dict(row)) for row in cursor.fetchall()]

    @staticmethod
    def update(conn: sqlite3.Connection, fuel_id: str, fuel_event: FuelEventCreate) -> Optional[FuelEvent]:
        """Update a fuel event."""
        cursor = conn.cursor()
        date_time = fuel_event.date_time.isoformat() if fuel_event.date_time else datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE fuel_events SET
                vehicle_id = ?, gallons = ?, odometer_reading = ?, total_cost = ?,
                price_per_gallon = ?, fuel_type = ?, is_consumable = ?, consumption_rate = ?,
                date_time = ?, latitude = ?, longitude = ?, station_name = ?, receipt_image_path = ?
            WHERE fuel_id = ?
        """, (
            fuel_event.vehicle_id, float(fuel_event.gallons), fuel_event.odometer_reading,
            float(fuel_event.total_cost) if fuel_event.total_cost else None,
            float(fuel_event.price_per_gallon) if fuel_event.price_per_gallon else None,
            fuel_event.fuel_type.value, fuel_event.is_consumable,
            float(fuel_event.consumption_rate) if fuel_event.consumption_rate else None,
            date_time, fuel_event.latitude, fuel_event.longitude,
            fuel_event.station_name, fuel_event.receipt_image_path, fuel_id
        ))
        conn.commit()

        if cursor.rowcount == 0:
            return None
        return FuelEventRepository.get_by_id(conn, fuel_id)

    @staticmethod
    def delete(conn: sqlite3.Connection, fuel_id: str) -> bool:
        """Delete a fuel event."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fuel_events WHERE fuel_id = ?", (fuel_id,))
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# MAINTENANCE EVENT REPOSITORY
# ============================================================================

class MaintenanceEventRepository:
    """Repository for maintenance event CRUD operations."""

    @staticmethod
    def create(conn: sqlite3.Connection, maintenance: MaintenanceEventCreate) -> MaintenanceEvent:
        """Create a new maintenance event."""
        maintenance_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        date = maintenance.date.isoformat() if maintenance.date else created_at

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO maintenance_events (
                maintenance_id, vehicle_id, date, maintenance_type, description,
                cost, vendor, odometer_reading, next_service_due, parts_replaced, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            maintenance_id, maintenance.vehicle_id, date, maintenance.maintenance_type,
            maintenance.description, float(maintenance.cost), maintenance.vendor,
            maintenance.odometer_reading, maintenance.next_service_due,
            maintenance.parts_replaced, created_at
        ))
        conn.commit()

        # Update vehicle mileage if provided
        if maintenance.odometer_reading:
            VehicleRepository.update_mileage(conn, maintenance.vehicle_id, maintenance.odometer_reading)

        return MaintenanceEventRepository.get_by_id(conn, maintenance_id)

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, maintenance_id: str) -> Optional[MaintenanceEvent]:
        """Get maintenance event by ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maintenance_events WHERE maintenance_id = ?", (maintenance_id,))
        row = cursor.fetchone()

        if row:
            return MaintenanceEvent(**_row_to_dict(row))
        return None

    @staticmethod
    def get_all(
        conn: sqlite3.Connection,
        vehicle_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MaintenanceEvent]:
        """Get all maintenance events with optional vehicle filter."""
        cursor = conn.cursor()

        if vehicle_id:
            cursor.execute("""
                SELECT * FROM maintenance_events
                WHERE vehicle_id = ?
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            """, (vehicle_id, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM maintenance_events
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        return [MaintenanceEvent(**_row_to_dict(row)) for row in cursor.fetchall()]

    @staticmethod
    def update(conn: sqlite3.Connection, maintenance_id: str, maintenance: MaintenanceEventCreate) -> Optional[MaintenanceEvent]:
        """Update a maintenance event."""
        cursor = conn.cursor()
        date = maintenance.date.isoformat() if maintenance.date else datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE maintenance_events SET
                vehicle_id = ?, date = ?, maintenance_type = ?, description = ?,
                cost = ?, vendor = ?, odometer_reading = ?, next_service_due = ?, parts_replaced = ?
            WHERE maintenance_id = ?
        """, (
            maintenance.vehicle_id, date, maintenance.maintenance_type, maintenance.description,
            float(maintenance.cost), maintenance.vendor, maintenance.odometer_reading,
            maintenance.next_service_due, maintenance.parts_replaced, maintenance_id
        ))
        conn.commit()

        if cursor.rowcount == 0:
            return None
        return MaintenanceEventRepository.get_by_id(conn, maintenance_id)

    @staticmethod
    def delete(conn: sqlite3.Connection, maintenance_id: str) -> bool:
        """Delete a maintenance event."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance_events WHERE maintenance_id = ?", (maintenance_id,))
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# REPAIR EVENT REPOSITORY
# ============================================================================

class RepairEventRepository:
    """Repository for repair event CRUD operations."""

    @staticmethod
    def create(conn: sqlite3.Connection, repair: RepairEventCreate) -> RepairEvent:
        """Create a new repair event."""
        repair_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        date = repair.date.isoformat() if repair.date else created_at

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO repair_events (
                repair_id, vehicle_id, date, repair_type, description,
                cost, vendor, odometer_reading, warranty_info, severity, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            repair_id, repair.vehicle_id, date, repair.repair_type, repair.description,
            float(repair.cost), repair.vendor, repair.odometer_reading,
            repair.warranty_info, repair.severity.value, created_at
        ))
        conn.commit()

        # Update vehicle mileage if provided
        if repair.odometer_reading:
            VehicleRepository.update_mileage(conn, repair.vehicle_id, repair.odometer_reading)

        return RepairEventRepository.get_by_id(conn, repair_id)

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, repair_id: str) -> Optional[RepairEvent]:
        """Get repair event by ID."""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repair_events WHERE repair_id = ?", (repair_id,))
        row = cursor.fetchone()

        if row:
            return RepairEvent(**_row_to_dict(row))
        return None

    @staticmethod
    def get_all(
        conn: sqlite3.Connection,
        vehicle_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RepairEvent]:
        """Get all repair events with optional vehicle filter."""
        cursor = conn.cursor()

        if vehicle_id:
            cursor.execute("""
                SELECT * FROM repair_events
                WHERE vehicle_id = ?
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            """, (vehicle_id, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM repair_events
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        return [RepairEvent(**_row_to_dict(row)) for row in cursor.fetchall()]

    @staticmethod
    def update(conn: sqlite3.Connection, repair_id: str, repair: RepairEventCreate) -> Optional[RepairEvent]:
        """Update a repair event."""
        cursor = conn.cursor()
        date = repair.date.isoformat() if repair.date else datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE repair_events SET
                vehicle_id = ?, date = ?, repair_type = ?, description = ?,
                cost = ?, vendor = ?, odometer_reading = ?, warranty_info = ?, severity = ?
            WHERE repair_id = ?
        """, (
            repair.vehicle_id, date, repair.repair_type, repair.description,
            float(repair.cost), repair.vendor, repair.odometer_reading,
            repair.warranty_info, repair.severity.value, repair_id
        ))
        conn.commit()

        if cursor.rowcount == 0:
            return None
        return RepairEventRepository.get_by_id(conn, repair_id)

    @staticmethod
    def delete(conn: sqlite3.Connection, repair_id: str) -> bool:
        """Delete a repair event."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM repair_events WHERE repair_id = ?", (repair_id,))
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# ANALYTICS REPOSITORY
# ============================================================================

class AnalyticsRepository:
    """Repository for analytics and reporting."""

    @staticmethod
    def get_vehicle_summary(conn: sqlite3.Connection, vehicle_id: str) -> Optional[VehicleSummary]:
        """Get comprehensive summary for a vehicle."""
        vehicle = VehicleRepository.get_by_id(conn, vehicle_id)
        if not vehicle:
            return None

        cursor = conn.cursor()

        # Get fuel costs and MPG
        cursor.execute("""
            SELECT
                COALESCE(SUM(total_cost), 0) as total_fuel_cost,
                COUNT(*) as fuel_count
            FROM fuel_events
            WHERE vehicle_id = ? AND is_consumable = 0
        """, (vehicle_id,))
        fuel_data = cursor.fetchone()

        # Calculate average MPG
        cursor.execute("""
            SELECT consumption_rate FROM fuel_events
            WHERE vehicle_id = ? AND consumption_rate IS NOT NULL AND is_consumable = 0
            ORDER BY date_time DESC
        """, (vehicle_id,))
        mpg_values = [row[0] for row in cursor.fetchall()]
        average_mpg = sum(mpg_values) / len(mpg_values) if mpg_values else None

        # Get maintenance costs
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0) as total, COUNT(*) as count
            FROM maintenance_events WHERE vehicle_id = ?
        """, (vehicle_id,))
        maint_data = cursor.fetchone()

        # Get repair costs
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0) as total, COUNT(*) as count
            FROM repair_events WHERE vehicle_id = ?
        """, (vehicle_id,))
        repair_data = cursor.fetchone()

        total_operating_cost = fuel_data[0] + maint_data[0] + repair_data[0]
        cost_per_mile = total_operating_cost / vehicle.current_mileage if vehicle.current_mileage > 0 else None

        return VehicleSummary(
            vehicle=vehicle,
            total_fuel_cost=fuel_data[0],
            total_maintenance_cost=maint_data[0],
            total_repair_cost=repair_data[0],
            total_operating_cost=total_operating_cost,
            average_mpg=average_mpg,
            fuel_event_count=fuel_data[1],
            maintenance_event_count=maint_data[1],
            repair_event_count=repair_data[1],
            cost_per_mile=cost_per_mile
        )

    @staticmethod
    def get_fleet_summary(conn: sqlite3.Connection) -> FleetSummary:
        """Get fleet-wide summary statistics."""
        cursor = conn.cursor()

        # Count vehicles
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        total_vehicles = cursor.fetchone()[0]

        # Fuel stats
        cursor.execute("""
            SELECT
                COUNT(*) as count,
                COALESCE(SUM(total_cost), 0) as total_cost
            FROM fuel_events WHERE is_consumable = 0
        """)
        fuel_data = cursor.fetchone()

        # Maintenance stats
        cursor.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(cost), 0) as total
            FROM maintenance_events
        """)
        maint_data = cursor.fetchone()

        # Repair stats
        cursor.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(cost), 0) as total
            FROM repair_events
        """)
        repair_data = cursor.fetchone()

        # Average fleet MPG
        cursor.execute("""
            SELECT consumption_rate FROM fuel_events
            WHERE consumption_rate IS NOT NULL AND is_consumable = 0
        """)
        mpg_values = [row[0] for row in cursor.fetchall()]
        average_fleet_mpg = sum(mpg_values) / len(mpg_values) if mpg_values else None

        return FleetSummary(
            total_vehicles=total_vehicles,
            total_fuel_events=fuel_data[0],
            total_maintenance_events=maint_data[0],
            total_repair_events=repair_data[0],
            total_fuel_cost=fuel_data[1],
            total_maintenance_cost=maint_data[1],
            total_repair_cost=repair_data[1],
            total_operating_cost=fuel_data[1] + maint_data[1] + repair_data[1],
            average_fleet_mpg=average_fleet_mpg
        )
