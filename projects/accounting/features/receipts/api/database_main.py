#!/usr/bin/env python3
"""
Receipt Processing FastAPI Application with Database Backend

Complete API with SQLAlchemy database backend supporting master-detail
relationships between receipts and line items.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Database imports
from database import get_db, init_database
from database.repository import ReceiptRepository
from database.models import Receipt as DBReceipt, ReceiptLineItem as DBLineItem

# Model imports - simplified for now
from enum import Enum

class ReceiptType(Enum):
    GROCERY = "grocery"
    RESTAURANT = "restaurant"
    GAS = "gas"
    RETAIL = "retail"
    OTHER = "other"

class ReceiptStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class PaymentMethod(Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CHECK = "check"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LiMOS Receipt Processing API with Database",
    description="AI-powered receipt processing with full database backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize the application and database."""
    logger.info("🚀 Starting Receipt Processing API with Database...")

    # Initialize database
    try:
        from database.migrations import init_database
        if not init_database():
            logger.error("❌ Failed to initialize database")
        else:
            logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        logger.info("⚠️ Continuing without database initialization")

    logger.info("🎉 API startup completed!")


# Dependency to get repository
def get_repository(db: Session = Depends(get_db)) -> ReceiptRepository:
    """Get repository instance."""
    return ReceiptRepository(db)


# Root and health endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LiMOS Receipt Processing API",
        "version": "1.0.0",
        "status": "running",
        "database": "enabled",
        "description": "AI-powered receipt processing with database backend",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "receipts": "/receipts",
            "line_items": "/line-items"
        }
    }


@app.get("/health")
async def health_check(repo: ReceiptRepository = Depends(get_repository)):
    """Health check endpoint."""
    try:
        # Test database connection by getting receipt count
        receipts, total_count = repo.get_receipts_with_pagination(limit=1)

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": {
                "status": "connected",
                "total_receipts": total_count
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": {
                "status": "error",
                "error": str(e)
            }
        }


# Receipt CRUD endpoints
@app.post("/receipts", response_model=dict)
async def create_receipt(
    receipt_data: dict,
    repo: ReceiptRepository = Depends(get_repository)
):
    """Create a new receipt with line items."""
    try:
        receipt = repo.create_receipt(receipt_data)
        return {
            "success": True,
            "receipt_id": receipt.receipt_id,
            "message": "Receipt created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/receipts/{receipt_id}")
async def get_receipt(
    receipt_id: str = PathParam(..., description="Receipt ID"),
    repo: ReceiptRepository = Depends(get_repository)
):
    """Get a specific receipt with all line items."""
    receipt = repo.get_receipt_by_id(receipt_id)

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return {
        "receipt_id": receipt.receipt_id,
        "vendor": {
            "name": receipt.vendor.name if receipt.vendor else None,
            "address": receipt.vendor.address if receipt.vendor else None,
            "phone": receipt.vendor.phone if receipt.vendor else None
        } if receipt.vendor else None,
        "date": receipt.date.isoformat(),
        "subtotal": float(receipt.subtotal),
        "tax_amount": float(receipt.tax_amount),
        "total_amount": float(receipt.total_amount),
        "payment_method": receipt.payment_method.value,
        "receipt_type": receipt.receipt_type.value,
        "status": receipt.status.value,
        "line_items": [
            {
                "id": item.id,
                "line_number": item.line_number,
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
                "category": item.category
            }
            for item in receipt.line_items
        ],
        "line_items_count": len(receipt.line_items),
        "created_at": receipt.created_at.isoformat(),
        "updated_at": receipt.updated_at.isoformat()
    }


@app.get("/receipts")
async def list_receipts(
    skip: int = Query(0, ge=0, description="Number of receipts to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of receipts"),
    vendor_name: Optional[str] = Query(None, description="Filter by vendor name"),
    receipt_type: Optional[ReceiptType] = Query(None, description="Filter by receipt type"),
    status: Optional[ReceiptStatus] = Query(None, description="Filter by status"),
    repo: ReceiptRepository = Depends(get_repository)
):
    """List receipts with pagination and filtering."""
    try:
        # Build filters
        filters = {}
        if vendor_name:
            filters["vendor_name"] = vendor_name
        if receipt_type:
            filters["receipt_type"] = receipt_type
        if status:
            filters["status"] = status

        receipts, total_count = repo.get_receipts_with_pagination(
            skip=skip,
            limit=limit,
            filters=filters if filters else None
        )

        return {
            "receipts": [
                {
                    "receipt_id": receipt.receipt_id,
                    "vendor_name": receipt.vendor.name if receipt.vendor else "Unknown",
                    "date": receipt.date.isoformat(),
                    "total_amount": float(receipt.total_amount),
                    "receipt_type": receipt.receipt_type.value,
                    "status": receipt.status.value,
                    "line_items_count": len(receipt.line_items)
                }
                for receipt in receipts
            ],
            "pagination": {
                "total_count": total_count,
                "skip": skip,
                "limit": limit,
                "has_more": total_count > skip + limit
            },
            "filters_applied": filters
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/receipts/{receipt_id}")
async def update_receipt(
    receipt_id: str = PathParam(..., description="Receipt ID"),
    update_data: dict = ...,
    repo: ReceiptRepository = Depends(get_repository)
):
    """Update a receipt."""
    try:
        receipt = repo.update_receipt(receipt_id, update_data)
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")

        return {
            "success": True,
            "receipt_id": receipt.receipt_id,
            "message": "Receipt updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: str = PathParam(..., description="Receipt ID"),
    repo: ReceiptRepository = Depends(get_repository)
):
    """Delete a receipt and all its line items."""
    success = repo.delete_receipt(receipt_id)

    if not success:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return {
        "success": True,
        "receipt_id": receipt_id,
        "message": "Receipt deleted successfully"
    }


# Line item endpoints
@app.get("/receipts/{receipt_id}/line-items")
async def get_line_items(
    receipt_id: str = PathParam(..., description="Receipt ID"),
    repo: ReceiptRepository = Depends(get_repository)
):
    """Get all line items for a receipt."""
    line_items = repo.get_line_items_by_receipt(receipt_id)

    return {
        "receipt_id": receipt_id,
        "line_items": [
            {
                "id": item.id,
                "line_number": item.line_number,
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
                "category": item.category,
                "created_at": item.created_at.isoformat()
            }
            for item in line_items
        ],
        "total_items": len(line_items)
    }


@app.post("/receipts/{receipt_id}/line-items")
async def add_line_item(
    receipt_id: str = PathParam(..., description="Receipt ID"),
    line_item_data: dict = ...,
    repo: ReceiptRepository = Depends(get_repository)
):
    """Add a new line item to a receipt."""
    try:
        line_item = repo.add_line_item(receipt_id, line_item_data)
        if not line_item:
            raise HTTPException(status_code=404, detail="Receipt not found")

        return {
            "success": True,
            "line_item_id": line_item.id,
            "receipt_id": receipt_id,
            "message": "Line item added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/line-items/{line_item_id}")
async def update_line_item(
    line_item_id: str = PathParam(..., description="Line item ID"),
    update_data: dict = ...,
    repo: ReceiptRepository = Depends(get_repository)
):
    """Update a specific line item."""
    try:
        line_item = repo.update_line_item(line_item_id, update_data)
        if not line_item:
            raise HTTPException(status_code=404, detail="Line item not found")

        return {
            "success": True,
            "line_item_id": line_item.id,
            "message": "Line item updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/line-items/{line_item_id}")
async def delete_line_item(
    line_item_id: str = PathParam(..., description="Line item ID"),
    repo: ReceiptRepository = Depends(get_repository)
):
    """Delete a specific line item."""
    success = repo.delete_line_item(line_item_id)

    if not success:
        raise HTTPException(status_code=404, detail="Line item not found")

    return {
        "success": True,
        "line_item_id": line_item_id,
        "message": "Line item deleted successfully"
    }


# Search endpoints
@app.post("/receipts/search")
async def search_receipts(
    search_params: dict,
    repo: ReceiptRepository = Depends(get_repository)
):
    """Advanced search for receipts."""
    try:
        receipts, total_count = repo.search_receipts(
            vendor_name=search_params.get("vendor_name"),
            date_from=search_params.get("date_from"),
            date_to=search_params.get("date_to"),
            min_amount=search_params.get("min_amount"),
            max_amount=search_params.get("max_amount"),
            receipt_type=search_params.get("receipt_type"),
            status=search_params.get("status"),
            category=search_params.get("category"),
            is_business_expense=search_params.get("is_business_expense"),
            limit=search_params.get("limit", 50),
            offset=search_params.get("offset", 0)
        )

        return {
            "receipts": [
                {
                    "receipt_id": receipt.receipt_id,
                    "vendor_name": receipt.vendor.name if receipt.vendor else "Unknown",
                    "date": receipt.date.isoformat(),
                    "total_amount": float(receipt.total_amount),
                    "receipt_type": receipt.receipt_type.value,
                    "status": receipt.status.value,
                    "line_items_count": len(receipt.line_items)
                }
                for receipt in receipts
            ],
            "total_count": total_count,
            "search_params": search_params
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/line-items/search")
async def search_line_items(
    description: Optional[str] = Query(None, description="Search in item description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum unit price"),
    max_price: Optional[float] = Query(None, description="Maximum unit price"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    repo: ReceiptRepository = Depends(get_repository)
):
    """Search line items across all receipts."""
    try:
        line_items = repo.search_line_items(
            description=description,
            category=category,
            min_price=Decimal(str(min_price)) if min_price else None,
            max_price=Decimal(str(max_price)) if max_price else None,
            limit=limit
        )

        return {
            "line_items": [
                {
                    "id": item.id,
                    "receipt_id": item.receipt_id,
                    "description": item.description,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price),
                    "category": item.category,
                    "receipt_date": item.receipt.date.isoformat(),
                    "vendor_name": item.receipt.vendor.name if item.receipt.vendor else "Unknown"
                }
                for item in line_items
            ],
            "total_found": len(line_items),
            "search_criteria": {
                "description": description,
                "category": category,
                "min_price": min_price,
                "max_price": max_price
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Statistics endpoints
@app.get("/receipts/statistics")
async def get_statistics(
    repo: ReceiptRepository = Depends(get_repository)
):
    """Get receipt statistics and analytics."""
    try:
        stats = repo.get_receipt_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vendors/{vendor_id}/statistics")
async def get_vendor_statistics(
    vendor_id: str = PathParam(..., description="Vendor ID"),
    repo: ReceiptRepository = Depends(get_repository)
):
    """Get statistics for a specific vendor."""
    try:
        stats = repo.get_vendor_statistics(vendor_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Bulk operations
@app.post("/receipts/bulk-update")
async def bulk_update_receipts(
    bulk_data: dict,
    repo: ReceiptRepository = Depends(get_repository)
):
    """Bulk update multiple receipts."""
    try:
        receipt_ids = bulk_data.get("receipt_ids", [])
        update_data = bulk_data.get("update_data", {})

        if not receipt_ids:
            raise HTTPException(status_code=400, detail="receipt_ids are required")

        updated_count = repo.bulk_update_receipts(receipt_ids, update_data)

        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Updated {updated_count} receipts"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/receipts/bulk-delete")
async def bulk_delete_receipts(
    receipt_ids: List[str],
    repo: ReceiptRepository = Depends(get_repository)
):
    """Bulk delete multiple receipts."""
    try:
        if not receipt_ids:
            raise HTTPException(status_code=400, detail="receipt_ids are required")

        deleted_count = repo.bulk_delete_receipts(receipt_ids)

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} receipts"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    print("🚀 Starting LiMOS Receipt Processing API with Database...")
    uvicorn.run(
        "database_main:app",
        host="0.0.0.0",
        port=8001,  # Different port to avoid conflict
        reload=True,
        log_level="info"
    )