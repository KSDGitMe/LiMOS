"""
Fleet Management API - FastAPI Application

REST API for fleet management with full CRUD operations for:
- Vehicles
- Fuel Events
- Maintenance Events
- Repair Events
- Analytics and Reporting
"""

from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import sqlite3

# Import models
from ..models import (
    Vehicle, VehicleCreate,
    FuelEvent, FuelEventCreate,
    MaintenanceEvent, MaintenanceEventCreate,
    RepairEvent, RepairEventCreate,
    VehicleSummary, FleetSummary,
    FuelType, SeverityLevel
)

# Import database
from ..database import (
    get_db,
    VehicleRepository,
    FuelEventRepository,
    MaintenanceEventRepository,
    RepairEventRepository,
    AnalyticsRepository
)

# Initialize FastAPI app
app = FastAPI(
    title="Fleet Management API",
    description="REST API for comprehensive fleet management operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Fleet Management API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "vehicles": "/api/vehicles",
            "fuel": "/api/fuel-events",
            "maintenance": "/api/maintenance-events",
            "repairs": "/api/repair-events",
            "analytics": "/api/analytics"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check(conn: sqlite3.Connection = Depends(get_db)):
    """Detailed health check with database stats."""
    vehicles = VehicleRepository.get_all(conn, limit=1)
    fuel_events = FuelEventRepository.get_all(conn, limit=1)
    maintenance = MaintenanceEventRepository.get_all(conn, limit=1)
    repairs = RepairEventRepository.get_all(conn, limit=1)

    return {
        "status": "healthy",
        "database": "connected",
        "data_loaded": {
            "vehicles": len(vehicles) > 0,
            "fuel_events": len(fuel_events) > 0,
            "maintenance_events": len(maintenance) > 0,
            "repair_events": len(repairs) > 0
        }
    }


# ============================================================================
# VEHICLE ENDPOINTS
# ============================================================================

@app.post("/api/vehicles", response_model=Vehicle, status_code=status.HTTP_201_CREATED, tags=["Vehicles"])
async def create_vehicle(vehicle: VehicleCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Create a new vehicle."""
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


@app.get("/api/vehicles", response_model=List[Vehicle], tags=["Vehicles"])
async def list_vehicles(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of vehicles to return"),
    offset: int = Query(0, ge=0, description="Number of vehicles to skip"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """List all vehicles with pagination."""
    vehicles = VehicleRepository.get_all(conn, limit=limit, offset=offset)
    return vehicles


@app.get("/api/vehicles/{vehicle_id}", response_model=Vehicle, tags=["Vehicles"])
async def get_vehicle(vehicle_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Get a specific vehicle by ID."""
    vehicle = VehicleRepository.get_by_id(conn, vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {vehicle_id} not found"
        )
    return vehicle


@app.put("/api/vehicles/{vehicle_id}", response_model=Vehicle, tags=["Vehicles"])
async def update_vehicle(vehicle_id: str, vehicle: VehicleCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Update a vehicle."""
    updated_vehicle = VehicleRepository.update(conn, vehicle_id, vehicle)
    if not updated_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {vehicle_id} not found"
        )
    return updated_vehicle


@app.delete("/api/vehicles/{vehicle_id}", tags=["Vehicles"])
async def delete_vehicle(vehicle_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Delete a vehicle."""
    deleted = VehicleRepository.delete(conn, vehicle_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {vehicle_id} not found"
        )
    return {"message": f"Vehicle {vehicle_id} deleted successfully"}


# ============================================================================
# FUEL EVENT ENDPOINTS
# ============================================================================

@app.post("/api/fuel-events", response_model=FuelEvent, status_code=status.HTTP_201_CREATED, tags=["Fuel Events"])
async def create_fuel_event(fuel_event: FuelEventCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Create a new fuel event."""
    # Verify vehicle exists
    vehicle = VehicleRepository.get_by_id(conn, fuel_event.vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {fuel_event.vehicle_id} not found"
        )

    created_event = FuelEventRepository.create(conn, fuel_event)
    return created_event


@app.get("/api/fuel-events", response_model=List[FuelEvent], tags=["Fuel Events"])
async def list_fuel_events(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """List all fuel events with optional vehicle filter."""
    events = FuelEventRepository.get_all(conn, vehicle_id=vehicle_id, limit=limit, offset=offset)
    return events


@app.get("/api/fuel-events/{fuel_id}", response_model=FuelEvent, tags=["Fuel Events"])
async def get_fuel_event(fuel_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Get a specific fuel event by ID."""
    event = FuelEventRepository.get_by_id(conn, fuel_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fuel event {fuel_id} not found"
        )
    return event


@app.put("/api/fuel-events/{fuel_id}", response_model=FuelEvent, tags=["Fuel Events"])
async def update_fuel_event(fuel_id: str, fuel_event: FuelEventCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Update a fuel event."""
    updated_event = FuelEventRepository.update(conn, fuel_id, fuel_event)
    if not updated_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fuel event {fuel_id} not found"
        )
    return updated_event


@app.delete("/api/fuel-events/{fuel_id}", tags=["Fuel Events"])
async def delete_fuel_event(fuel_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Delete a fuel event."""
    deleted = FuelEventRepository.delete(conn, fuel_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fuel event {fuel_id} not found"
        )
    return {"message": f"Fuel event {fuel_id} deleted successfully"}


# ============================================================================
# MAINTENANCE EVENT ENDPOINTS
# ============================================================================

@app.post("/api/maintenance-events", response_model=MaintenanceEvent, status_code=status.HTTP_201_CREATED, tags=["Maintenance"])
async def create_maintenance_event(maintenance: MaintenanceEventCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Create a new maintenance event."""
    # Verify vehicle exists
    vehicle = VehicleRepository.get_by_id(conn, maintenance.vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {maintenance.vehicle_id} not found"
        )

    created_event = MaintenanceEventRepository.create(conn, maintenance)
    return created_event


@app.get("/api/maintenance-events", response_model=List[MaintenanceEvent], tags=["Maintenance"])
async def list_maintenance_events(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """List all maintenance events with optional vehicle filter."""
    events = MaintenanceEventRepository.get_all(conn, vehicle_id=vehicle_id, limit=limit, offset=offset)
    return events


@app.get("/api/maintenance-events/{maintenance_id}", response_model=MaintenanceEvent, tags=["Maintenance"])
async def get_maintenance_event(maintenance_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Get a specific maintenance event by ID."""
    event = MaintenanceEventRepository.get_by_id(conn, maintenance_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance event {maintenance_id} not found"
        )
    return event


@app.put("/api/maintenance-events/{maintenance_id}", response_model=MaintenanceEvent, tags=["Maintenance"])
async def update_maintenance_event(
    maintenance_id: str,
    maintenance: MaintenanceEventCreate,
    conn: sqlite3.Connection = Depends(get_db)
):
    """Update a maintenance event."""
    updated_event = MaintenanceEventRepository.update(conn, maintenance_id, maintenance)
    if not updated_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance event {maintenance_id} not found"
        )
    return updated_event


@app.delete("/api/maintenance-events/{maintenance_id}", tags=["Maintenance"])
async def delete_maintenance_event(maintenance_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Delete a maintenance event."""
    deleted = MaintenanceEventRepository.delete(conn, maintenance_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maintenance event {maintenance_id} not found"
        )
    return {"message": f"Maintenance event {maintenance_id} deleted successfully"}


# ============================================================================
# REPAIR EVENT ENDPOINTS
# ============================================================================

@app.post("/api/repair-events", response_model=RepairEvent, status_code=status.HTTP_201_CREATED, tags=["Repairs"])
async def create_repair_event(repair: RepairEventCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Create a new repair event."""
    # Verify vehicle exists
    vehicle = VehicleRepository.get_by_id(conn, repair.vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {repair.vehicle_id} not found"
        )

    created_event = RepairEventRepository.create(conn, repair)
    return created_event


@app.get("/api/repair-events", response_model=List[RepairEvent], tags=["Repairs"])
async def list_repair_events(
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """List all repair events with optional vehicle filter."""
    events = RepairEventRepository.get_all(conn, vehicle_id=vehicle_id, limit=limit, offset=offset)
    return events


@app.get("/api/repair-events/{repair_id}", response_model=RepairEvent, tags=["Repairs"])
async def get_repair_event(repair_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Get a specific repair event by ID."""
    event = RepairEventRepository.get_by_id(conn, repair_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair event {repair_id} not found"
        )
    return event


@app.put("/api/repair-events/{repair_id}", response_model=RepairEvent, tags=["Repairs"])
async def update_repair_event(repair_id: str, repair: RepairEventCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Update a repair event."""
    updated_event = RepairEventRepository.update(conn, repair_id, repair)
    if not updated_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair event {repair_id} not found"
        )
    return updated_event


@app.delete("/api/repair-events/{repair_id}", tags=["Repairs"])
async def delete_repair_event(repair_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Delete a repair event."""
    deleted = RepairEventRepository.delete(conn, repair_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair event {repair_id} not found"
        )
    return {"message": f"Repair event {repair_id} deleted successfully"}


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/analytics/vehicle/{vehicle_id}", response_model=VehicleSummary, tags=["Analytics"])
async def get_vehicle_summary(vehicle_id: str, conn: sqlite3.Connection = Depends(get_db)):
    """Get comprehensive analytics summary for a vehicle."""
    summary = AnalyticsRepository.get_vehicle_summary(conn, vehicle_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle {vehicle_id} not found"
        )
    return summary


@app.get("/api/analytics/fleet", response_model=FleetSummary, tags=["Analytics"])
async def get_fleet_summary(conn: sqlite3.Connection = Depends(get_db)):
    """Get fleet-wide analytics summary."""
    summary = AnalyticsRepository.get_fleet_summary(conn)
    return summary


# ============================================================================
# STATISTICS
# ============================================================================

@app.get("/api/stats/summary", tags=["Statistics"])
async def get_stats_summary(conn: sqlite3.Connection = Depends(get_db)):
    """Get system statistics summary."""
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
