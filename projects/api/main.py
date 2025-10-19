"""
LiMOS Unified API Server

Single FastAPI application serving all LiMOS modules:
- Accounting (Journal Entries, Accounts, Budgets)
- Fleet Management (Vehicles, Fuel, Maintenance, Repairs)
- Future modules can be added as new routers

All endpoints are prefixed by module:
- /api/accounting/*
- /api/fleet/*
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers from each module
from .routers import accounting, fleet, orchestrator

# Initialize FastAPI app
app = FastAPI(
    title="LiMOS Unified API",
    description="Unified REST API for Life Management Operating System",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - configure for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ROOT HEALTH CHECK
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with service information."""
    return {
        "status": "healthy",
        "service": "LiMOS Unified API",
        "version": "2.0.0",
        "modules": {
            "orchestrator": {
                "base_url": "/api/orchestrator",
                "docs": "/docs#/Orchestrator"
            },
            "accounting": {
                "base_url": "/api/accounting",
                "docs": "/docs#/Accounting"
            },
            "fleet": {
                "base_url": "/api/fleet",
                "docs": "/docs#/Fleet%20Management"
            }
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "orchestrator": "/api/orchestrator/command",
            "accounting": "/api/accounting/*",
            "fleet": "/api/fleet/*"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Combined health check for all modules."""
    # Import database functions from each module
    from projects.fleet.database import get_db_connection, VehicleRepository
    from projects.accounting.database import get_db, JournalEntryRepository

    # Check accounting
    try:
        # For Notion backend, db is None; for SQL, get a session
        from projects.accounting.database import ACCOUNTING_BACKEND
        if ACCOUNTING_BACKEND == "notion":
            db = None
        else:
            db_gen = get_db()
            db = next(db_gen)

        # Try to get journal entries count
        entries = JournalEntryRepository.get_all(db, limit=1)
        accounting_status = "healthy"
        acct_data = {"entries_accessible": len(entries) >= 0}

        # Close SQL session if it was opened
        if ACCOUNTING_BACKEND != "notion":
            try:
                next(db_gen)
            except StopIteration:
                pass
    except Exception as e:
        accounting_status = f"error: {str(e)}"
        acct_data = {}

    # Check fleet
    try:
        conn = get_db_connection()
        try:
            vehicles = VehicleRepository.get_all(conn, limit=1)
            fleet_status = "healthy"
            fleet_data_loaded = len(vehicles) > 0
        finally:
            conn.close()
    except Exception as e:
        fleet_status = f"error: {str(e)}"
        fleet_data_loaded = False

    return {
        "status": "healthy" if accounting_status == "healthy" and fleet_status == "healthy" else "degraded",
        "modules": {
            "accounting": {
                "status": accounting_status,
                "data": acct_data
            },
            "fleet": {
                "status": fleet_status,
                "data_loaded": fleet_data_loaded
            }
        }
    }


# ============================================================================
# INCLUDE MODULE ROUTERS
# ============================================================================

# Include Orchestrator routes (Universal Shortcut entry point)
app.include_router(orchestrator.router, tags=["Orchestrator"])

# Include Accounting routes under /api/accounting
app.include_router(
    accounting.router,
    prefix="/api/accounting",
    tags=["Accounting"]
)

# Include Fleet Management routes under /api/fleet
app.include_router(
    fleet.router,
    prefix="/api/fleet",
    tags=["Fleet Management"]
)
