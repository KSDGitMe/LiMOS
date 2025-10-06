"""
Receipt Processing FastAPI Application

This module provides a comprehensive REST API for receipt processing,
built on top of the Receipt Agent system.
"""

import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    BackgroundTasks,
    Depends,
    Query,
    Path as PathParam
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from .models import (
    ReceiptProcessingOptionsModel,
    ReceiptSearchModel,
    ReceiptUpdateModel,
    BatchProcessingModel,
    ExportRequestModel,
    ReceiptSummaryModel,
    ReceiptDetailModel,
    ProcessingResultModel,
    SearchResultModel,
    BatchProcessingResultModel,
    StorageStatsModel,
    ExportResultModel,
    HealthCheckModel,
    ErrorResponseModel
)
from ..models.receipt import ReceiptType, ReceiptStatus
from ..services.storage import ReceiptStorageService
from ....agents.receipt_agent import ReceiptAgent


# Global variables
app = FastAPI(
    title="LiMOS Receipt Processing API",
    description="AI-powered receipt processing and management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global agent and storage instances
receipt_agent: Optional[ReceiptAgent] = None
storage_service: Optional[ReceiptStorageService] = None

# Security
security = HTTPBearer(auto_error=False)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = {"image/jpeg", "image/png", "image/tiff", "application/pdf"}
MAX_BATCH_SIZE = 20


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    global receipt_agent, storage_service

    print("🚀 Starting Receipt Processing API...")

    # Initialize storage service
    storage_service = ReceiptStorageService()
    print("✅ Storage service initialized")

    # Initialize receipt agent
    try:
        from ....agents.receipt_agent import ReceiptAgent
        receipt_agent = ReceiptAgent(
            name="APIReceiptAgent",
            environment=os.getenv("ENVIRONMENT", "development")
        )
        await receipt_agent.initialize()
        print("✅ Receipt agent initialized")
    except Exception as e:
        print(f"❌ Failed to initialize receipt agent: {e}")
        # Continue without agent for basic functionality

    print("🎉 API startup completed!")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    global receipt_agent

    print("🛑 Shutting down Receipt Processing API...")

    if receipt_agent:
        await receipt_agent.cleanup()
        print("✅ Receipt agent cleaned up")

    print("👋 API shutdown completed!")


# Dependency functions
async def get_receipt_agent() -> ReceiptAgent:
    """Get the receipt agent instance."""
    if receipt_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Receipt agent not available. Please check the server configuration."
        )
    return receipt_agent


async def get_storage_service() -> ReceiptStorageService:
    """Get the storage service instance."""
    if storage_service is None:
        raise HTTPException(
            status_code=503,
            detail="Storage service not available."
        )
    return storage_service


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
        )


# Authentication dependency (optional)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token (implement as needed)."""
    # For now, return a placeholder
    # In production, implement proper JWT validation
    if credentials:
        return {"user_id": "demo_user", "permissions": ["read", "write"]}
    return None


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponseModel(
            error=exc.detail,
            timestamp=datetime.utcnow(),
            request_id=str(uuid.uuid4())
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponseModel(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.utcnow(),
            request_id=str(uuid.uuid4())
        ).model_dump()
    )


# Health check endpoints
@app.get("/health", response_model=HealthCheckModel)
async def health_check():
    """Health check endpoint."""
    global receipt_agent, storage_service

    agent_status = {}
    if receipt_agent:
        agent_status = {
            "status": receipt_agent.status.value,
            "initialized": receipt_agent.is_initialized,
            "processed_receipts": getattr(receipt_agent, 'processed_receipts', 0)
        }

    storage_status = {}
    if storage_service:
        try:
            stats = await storage_service.get_storage_stats()
            storage_status = {
                "total_receipts": stats["total_receipts"],
                "storage_size_mb": stats["total_size_mb"]
            }
        except Exception:
            storage_status = {"error": "Storage service unavailable"}

    return HealthCheckModel(
        status="healthy" if receipt_agent and storage_service else "degraded",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        agent_status=agent_status,
        storage_status=storage_status,
        dependencies={
            "receipt_agent": receipt_agent is not None,
            "storage_service": storage_service is not None,
            "anthropic_api": os.getenv("ANTHROPIC_API_KEY") is not None
        }
    )


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LiMOS Receipt Processing API",
        "version": "1.0.0",
        "description": "AI-powered receipt processing and management system",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "receipts": "/receipts",
            "process": "/receipts/process",
            "search": "/receipts/search"
        }
    }


# Receipt processing endpoints
@app.post("/receipts/process", response_model=ProcessingResultModel)
async def process_receipt(
    file: UploadFile = File(..., description="Receipt image file"),
    extract_line_items: bool = Form(True, description="Extract individual line items"),
    categorize_items: bool = Form(True, description="Categorize line items"),
    validate_totals: bool = Form(True, description="Validate mathematical totals"),
    enhance_vendor_info: bool = Form(False, description="Enhance vendor information"),
    business_context: Optional[str] = Form(None, description="Business context"),
    agent: ReceiptAgent = Depends(get_receipt_agent),
    storage: ReceiptStorageService = Depends(get_storage_service),
    current_user = Depends(get_current_user)
):
    """
    Process a receipt image and extract structured data.

    Upload a receipt image (JPEG, PNG, TIFF, or PDF) and get back
    structured data including vendor information, line items, totals, and more.
    """
    # Validate file
    validate_file(file)

    try:
        # Read file data
        file_data = await file.read()

        # Process with agent
        result = await agent.execute({
            "file_data": file_data,
            "file_name": file.filename,
            "extract_line_items": extract_line_items,
            "categorize_items": categorize_items,
            "validate_totals": validate_totals,
            "enhance_vendor_info": enhance_vendor_info,
            "business_context": business_context
        })

        # Convert result to API model
        if result.get("success"):
            receipt_detail = ReceiptDetailModel.from_receipt(
                # Convert dict back to Receipt object for the model
                # In practice, you might modify the agent to return Receipt objects directly
                result["receipt"]
            ) if result.get("receipt") else None

            return ProcessingResultModel(
                success=True,
                receipt=receipt_detail,
                warnings=result.get("warnings", []),
                validation_errors=result.get("validation_errors", []),
                processing_time=result.get("processing_time", 0.0),
                confidence_breakdown=result.get("confidence_breakdown", {}),
                agent_stats=result.get("agent_stats", {})
            )
        else:
            return ProcessingResultModel(
                success=False,
                error_message=result.get("error", "Processing failed"),
                processing_time=result.get("processing_time", 0.0)
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/receipts/{receipt_id}", response_model=ReceiptDetailModel)
async def get_receipt(
    receipt_id: str = PathParam(..., description="Receipt ID"),
    storage: ReceiptStorageService = Depends(get_storage_service),
    current_user = Depends(get_current_user)
):
    """Get a specific receipt by ID."""
    receipt = await storage.get_receipt(receipt_id)

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return ReceiptDetailModel.from_receipt(receipt)


@app.put("/receipts/{receipt_id}", response_model=ReceiptDetailModel)
async def update_receipt(
    receipt_id: str = PathParam(..., description="Receipt ID"),
    update_data: ReceiptUpdateModel = ...,
    storage: ReceiptStorageService = Depends(get_storage_service),
    current_user = Depends(get_current_user)
):
    """Update a receipt."""
    receipt = await storage.get_receipt(receipt_id)

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Apply updates
    if update_data.vendor_name is not None:
        receipt.vendor.name = update_data.vendor_name
    if update_data.receipt_type is not None:
        receipt.receipt_type = update_data.receipt_type
    if update_data.category is not None:
        receipt.category = update_data.category
    if update_data.notes is not None:
        receipt.notes = update_data.notes
    if update_data.is_business_expense is not None:
        receipt.is_business_expense = update_data.is_business_expense
    if update_data.is_reimbursable is not None:
        receipt.is_reimbursable = update_data.is_reimbursable
    if update_data.custom_fields is not None:
        receipt.custom_fields.update(update_data.custom_fields)

    # Update timestamp
    receipt.updated_at = datetime.utcnow()

    # Save changes
    success = await storage.update_receipt(receipt)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update receipt")

    return ReceiptDetailModel.from_receipt(receipt)


@app.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: str = PathParam(..., description="Receipt ID"),
    delete_image: bool = Query(True, description="Also delete associated image"),
    storage: ReceiptStorageService = Depends(get_storage_service),
    current_user = Depends(get_current_user)
):
    """Delete a receipt."""
    success = await storage.delete_receipt(receipt_id, delete_image=delete_image)

    if not success:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return {"message": "Receipt deleted successfully", "receipt_id": receipt_id}


# Search endpoints
@app.post("/receipts/search", response_model=SearchResultModel)
async def search_receipts(
    search_params: ReceiptSearchModel = ...,
    storage: ReceiptStorageService = Depends(get_storage_service),
    current_user = Depends(get_current_user)
):
    """Search receipts with filters."""
    receipts = await storage.search_receipts(
        vendor_name=search_params.vendor_name,
        date_from=search_params.date_from,
        date_to=search_params.date_to,
        min_amount=search_params.min_amount,
        max_amount=search_params.max_amount,
        receipt_type=search_params.receipt_type,
        status=search_params.status,
        limit=search_params.limit + search_params.offset  # Get extra for pagination
    )

    # Apply pagination
    paginated_receipts = receipts[search_params.offset:search_params.offset + search_params.limit]

    return SearchResultModel(
        receipts=[ReceiptSummaryModel.from_receipt(r) for r in paginated_receipts],
        total_count=len(receipts),
        page_info={
            "offset": search_params.offset,
            "limit": search_params.limit,
            "has_more": len(receipts) > search_params.offset + search_params.limit
        },
        filters_applied=search_params.model_dump(exclude_none=True)
    )


@app.get("/receipts", response_model=SearchResultModel)
async def list_receipts(
    vendor_name: Optional[str] = Query(None, description="Filter by vendor name"),
    receipt_type: Optional[ReceiptType] = Query(None, description="Filter by receipt type"),
    status: Optional[ReceiptStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    storage: ReceiptStorageService = Depends(get_storage_service),
    current_user = Depends(get_current_user)
):
    """List receipts with optional filters."""
    receipts = await storage.search_receipts(
        vendor_name=vendor_name,
        receipt_type=receipt_type,
        status=status,
        limit=limit + offset
    )

    paginated_receipts = receipts[offset:offset + limit]

    return SearchResultModel(
        receipts=[ReceiptSummaryModel.from_receipt(r) for r in paginated_receipts],
        total_count=len(receipts),
        page_info={
            "offset": offset,
            "limit": limit,
            "has_more": len(receipts) > offset + limit
        },
        filters_applied={
            "vendor_name": vendor_name,
            "receipt_type": receipt_type,
            "status": status
        }
    )


# Statistics and reporting endpoints
@app.get("/receipts/stats", response_model=StorageStatsModel)
async def get_storage_stats(
    storage: ReceiptStorageService = Depends(get_storage_service),
    current_user = Depends(get_current_user)
):
    """Get storage statistics."""
    stats = await storage.get_storage_stats()
    return StorageStatsModel(**stats)


@app.post("/receipts/export", response_model=ExportResultModel)
async def export_receipts(
    export_request: ExportRequestModel = ...,
    background_tasks: BackgroundTasks = ...,
    storage: ReceiptStorageService = Depends(get_storage_service),
    current_user = Depends(get_current_user)
):
    """Export receipts to file."""
    try:
        export_path = await storage.export_receipts(
            format=export_request.format,
            date_from=export_request.date_from,
            date_to=export_request.date_to
        )

        # Get file info
        file_size = export_path.stat().st_size

        # Get record count (simplified)
        receipts = await storage.search_receipts(
            date_from=export_request.date_from,
            date_to=export_request.date_to
        )

        return ExportResultModel(
            success=True,
            file_path=str(export_path),
            file_size=file_size,
            record_count=len(receipts),
            export_format=export_request.format,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        return ExportResultModel(
            success=False,
            export_format=export_request.format,
            generated_at=datetime.utcnow(),
            error_message=str(e)
        )


@app.get("/receipts/export/{export_id}")
async def download_export(
    export_id: str = PathParam(..., description="Export file ID"),
    current_user = Depends(get_current_user)
):
    """Download an exported file."""
    # In a real implementation, you'd look up the export file by ID
    # For now, this is a placeholder
    raise HTTPException(status_code=501, detail="Export download not implemented")


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )