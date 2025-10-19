"""
Fleet Management Module Router

All fleet endpoints prefixed with /api/fleet/*
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
import sqlite3

# Import models from fleet module
from projects.fleet.models import (
    Vehicle, VehicleCreate,
    FuelEvent, FuelEventCreate,
    MaintenanceEvent, MaintenanceEventCreate,
    RepairEvent, RepairEventCreate,
    Vendor, VendorCreate,
    VehicleSummary, FleetSummary
)

# Import database from fleet module
from projects.fleet.database import (
    get_db_connection,
    VehicleRepository,
    FuelEventRepository,
    MaintenanceEventRepository,
    RepairEventRepository,
    VendorRepository,
    AnalyticsRepository
)

# Initialize router
router = APIRouter()


# No longer needed - we'll use get_db_connection() directly


# ============================================================================
# VEHICLE ENDPOINTS
# ============================================================================

@router.post("/vehicles", response_model=Vehicle, status_code=status.HTTP_201_CREATED)
async def create_vehicle(vehicle: VehicleCreate):
    """Create a new vehicle."""
    conn = get_db_connection()
    try:
        created_vehicle = VehicleRepository.create(conn, vehicle)
        return created_vehicle
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vehicle with this VIN already exists"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        conn.close()


@router.get("/vehicles", response_model=List[Vehicle])
async def list_vehicles(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of vehicles to return"),
    offset: int = Query(0, ge=0, description="Number of vehicles to skip")
):
    """List all vehicles with pagination."""
    conn = get_db_connection()
    try:
        vehicles = VehicleRepository.get_all(conn, limit=limit, offset=offset)
        return vehicles
    finally:
        conn.close()


@router.get("/vehicles/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: str):
    """Get a specific vehicle by ID."""
    conn = get_db_connection()
    try:
        vehicle = VehicleRepository.get_by_id(conn, vehicle_id)
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle {vehicle_id} not found"
            )
        return vehicle


    finally:
        conn.close()
@router.put("/vehicles/{vehicle_id}", response_model=Vehicle)
async def update_vehicle(vehicle_id: str, vehicle: VehicleCreate):
    """Update a vehicle."""
    conn = get_db_connection()
    try:
        updated_vehicle = VehicleRepository.update(conn, vehicle_id, vehicle)
        if not updated_vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle {vehicle_id} not found"
            )
        return updated_vehicle


    finally:
        conn.close()
@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: str):
    """Delete a vehicle."""
    conn = get_db_connection()
    try:
        deleted = VehicleRepository.delete(conn, vehicle_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle {vehicle_id} not found"
            )
        return {"message": f"Vehicle {vehicle_id} deleted successfully"}


    finally:
        conn.close()
# ============================================================================
# FUEL EVENT ENDPOINTS
# ============================================================================

@router.post("/fuel-events", response_model=FuelEvent, status_code=status.HTTP_201_CREATED)
async def create_fuel_event(fuel_event: FuelEventCreate):
    """Create a new fuel event."""
    conn = get_db_connection()
    try:
        # Verify vehicle exists
        vehicle = VehicleRepository.get_by_id(conn, fuel_event.vehicle_id)
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle {fuel_event.vehicle_id} not found"
            )

        created_event = FuelEventRepository.create(conn, fuel_event)
        return created_event


    finally:
        conn.close()
@router.get("/fuel-events", response_model=List[FuelEvent])
async def list_fuel_events(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip")
):
    """List all fuel events with optional vehicle filter."""
    conn = get_db_connection()
    try:
        events = FuelEventRepository.get_all(conn, vehicle_id=vehicle_id, limit=limit, offset=offset)
        return events


    finally:
        conn.close()
@router.get("/fuel-events/{fuel_id}", response_model=FuelEvent)
async def get_fuel_event(fuel_id: str):
    """Get a specific fuel event by ID."""
    conn = get_db_connection()
    try:
        event = FuelEventRepository.get_by_id(conn, fuel_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fuel event {fuel_id} not found"
            )
        return event


    finally:
        conn.close()
@router.put("/fuel-events/{fuel_id}", response_model=FuelEvent)
async def update_fuel_event(fuel_id: str, fuel_event: FuelEventCreate):
    """Update a fuel event."""
    conn = get_db_connection()
    try:
        updated_event = FuelEventRepository.update(conn, fuel_id, fuel_event)
        if not updated_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fuel event {fuel_id} not found"
            )
        return updated_event


    finally:
        conn.close()
@router.delete("/fuel-events/{fuel_id}")
async def delete_fuel_event(fuel_id: str):
    """Delete a fuel event."""
    conn = get_db_connection()
    try:
        deleted = FuelEventRepository.delete(conn, fuel_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fuel event {fuel_id} not found"
            )
        return {"message": f"Fuel event {fuel_id} deleted successfully"}


    finally:
        conn.close()
# ============================================================================
# MAINTENANCE EVENT ENDPOINTS
# ============================================================================

@router.post("/maintenance-events", response_model=MaintenanceEvent, status_code=status.HTTP_201_CREATED)
async def create_maintenance_event(maintenance: MaintenanceEventCreate):
    """Create a new maintenance event."""
    conn = get_db_connection()
    try:
        # Verify vehicle exists
        vehicle = VehicleRepository.get_by_id(conn, maintenance.vehicle_id)
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle {maintenance.vehicle_id} not found"
            )

        created_event = MaintenanceEventRepository.create(conn, maintenance)
        return created_event


    finally:
        conn.close()
@router.get("/maintenance-events", response_model=List[MaintenanceEvent])
async def list_maintenance_events(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip")
):
    """List all maintenance events with optional vehicle filter."""
    conn = get_db_connection()
    try:
        events = MaintenanceEventRepository.get_all(conn, vehicle_id=vehicle_id, limit=limit, offset=offset)
        return events


    finally:
        conn.close()
@router.get("/maintenance-events/{maintenance_id}", response_model=MaintenanceEvent)
async def get_maintenance_event(maintenance_id: str):
    """Get a specific maintenance event by ID."""
    conn = get_db_connection()
    try:
        event = MaintenanceEventRepository.get_by_id(conn, maintenance_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Maintenance event {maintenance_id} not found"
            )
        return event


    finally:
        conn.close()
@router.put("/maintenance-events/{maintenance_id}", response_model=MaintenanceEvent)
async def update_maintenance_event(maintenance_id: str, maintenance: MaintenanceEventCreate):
    """Update a maintenance event."""
    conn = get_db_connection()
    try:
        updated_event = MaintenanceEventRepository.update(conn, maintenance_id, maintenance)
        if not updated_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Maintenance event {maintenance_id} not found"
            )
        return updated_event


    finally:
        conn.close()
@router.delete("/maintenance-events/{maintenance_id}")
async def delete_maintenance_event(maintenance_id: str):
    """Delete a maintenance event."""
    conn = get_db_connection()
    try:
        deleted = MaintenanceEventRepository.delete(conn, maintenance_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Maintenance event {maintenance_id} not found"
            )
        return {"message": f"Maintenance event {maintenance_id} deleted successfully"}


    finally:
        conn.close()
# ============================================================================
# REPAIR EVENT ENDPOINTS
# ============================================================================

@router.post("/repair-events", response_model=RepairEvent, status_code=status.HTTP_201_CREATED)
async def create_repair_event(repair: RepairEventCreate):
    """Create a new repair event."""
    conn = get_db_connection()
    try:
        # Verify vehicle exists
        vehicle = VehicleRepository.get_by_id(conn, repair.vehicle_id)
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle {repair.vehicle_id} not found"
            )

        created_event = RepairEventRepository.create(conn, repair)
        return created_event


    finally:
        conn.close()
@router.get("/repair-events", response_model=List[RepairEvent])
async def list_repair_events(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip")
):
    """List all repair events with optional vehicle filter."""
    conn = get_db_connection()
    try:
        events = RepairEventRepository.get_all(conn, vehicle_id=vehicle_id, limit=limit, offset=offset)
        return events


    finally:
        conn.close()
@router.get("/repair-events/{repair_id}", response_model=RepairEvent)
async def get_repair_event(repair_id: str):
    """Get a specific repair event by ID."""
    conn = get_db_connection()
    try:
        event = RepairEventRepository.get_by_id(conn, repair_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repair event {repair_id} not found"
            )
        return event


    finally:
        conn.close()
@router.put("/repair-events/{repair_id}", response_model=RepairEvent)
async def update_repair_event(repair_id: str, repair: RepairEventCreate):
    """Update a repair event."""
    conn = get_db_connection()
    try:
        updated_event = RepairEventRepository.update(conn, repair_id, repair)
        if not updated_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repair event {repair_id} not found"
            )
        return updated_event


    finally:
        conn.close()
@router.delete("/repair-events/{repair_id}")
async def delete_repair_event(repair_id: str):
    """Delete a repair event."""
    conn = get_db_connection()
    try:
        deleted = RepairEventRepository.delete(conn, repair_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repair event {repair_id} not found"
            )
        return {"message": f"Repair event {repair_id} deleted successfully"}


    finally:
        conn.close()
# ============================================================================
# VENDOR ENDPOINTS
# ============================================================================

@router.post("/vendors", response_model=Vendor, status_code=status.HTTP_201_CREATED)
async def create_vendor(vendor: VendorCreate):
    """Create a new vendor."""
    try:
        conn = get_db_connection()
        try:
            created_vendor = VendorRepository.create(conn, vendor)
            return created_vendor
        finally:
            conn.close()
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor with this name already exists"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/vendors", response_model=List[Vendor])
async def list_vendors(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of vendors to return"),
    offset: int = Query(0, ge=0, description="Number of vendors to skip")
):
    """List all vendors with pagination."""
    conn = get_db_connection()
    try:
        vendors = VendorRepository.get_all(conn, limit=limit, offset=offset)
        return vendors


    finally:
        conn.close()
@router.get("/vendors/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: str):
    """Get a specific vendor by ID."""
    conn = get_db_connection()
    try:
        vendor = VendorRepository.get_by_id(conn, vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor {vendor_id} not found"
            )
        return vendor


    finally:
        conn.close()
@router.put("/vendors/{vendor_id}", response_model=Vendor)
async def update_vendor(vendor_id: str, vendor: VendorCreate):
    """Update a vendor."""
    conn = get_db_connection()
    try:
        updated_vendor = VendorRepository.update(conn, vendor_id, vendor)
        if not updated_vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor {vendor_id} not found"
            )
        return updated_vendor


    finally:
        conn.close()
@router.delete("/vendors/{vendor_id}")
async def delete_vendor(vendor_id: str):
    """Delete a vendor."""
    conn = get_db_connection()
    try:
        deleted = VendorRepository.delete(conn, vendor_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor {vendor_id} not found"
            )
        return {"message": f"Vendor {vendor_id} deleted successfully"}


    finally:
        conn.close()
# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/vehicle/{vehicle_id}", response_model=VehicleSummary)
async def get_vehicle_summary(vehicle_id: str):
    """Get comprehensive analytics summary for a vehicle."""
    conn = get_db_connection()
    try:
        summary = AnalyticsRepository.get_vehicle_summary(conn, vehicle_id)
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle {vehicle_id} not found"
            )
        return summary


    finally:
        conn.close()
@router.get("/analytics/fleet", response_model=FleetSummary)
async def get_fleet_summary():
    """Get fleet-wide analytics summary."""
    conn = get_db_connection()
    try:
        summary = AnalyticsRepository.get_fleet_summary(conn)
        return summary


    finally:
        conn.close()
# ============================================================================
# STATISTICS
# ============================================================================

@router.get("/stats/summary")
async def get_stats_summary():
    """Get system statistics summary."""
    conn = get_db_connection()
    try:
        vehicles = VehicleRepository.get_all(conn, limit=10000)
        fuel_events = FuelEventRepository.get_all(conn, limit=10000)
        maintenance_events = MaintenanceEventRepository.get_all(conn, limit=10000)
        repair_events = RepairEventRepository.get_all(conn, limit=10000)

        return {
            "vehicles": len(vehicles),
            "fuel_events": len(fuel_events),
            "maintenance_events": len(maintenance_events),
            "repair_events": len(repair_events),
        }
    finally:
        conn.close()