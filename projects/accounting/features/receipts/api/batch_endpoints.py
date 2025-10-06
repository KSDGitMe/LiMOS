"""
Batch Processing Endpoints

This module provides endpoints for batch processing multiple receipts,
including upload, processing status tracking, and result retrieval.
"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    BackgroundTasks,
    Depends,
    Query,
    Path as PathParam
)
from fastapi.responses import JSONResponse

from .models import (
    BatchProcessingModel,
    BatchProcessingResultModel,
    ProcessingResultModel,
    ReceiptDetailModel
)
from ..services.storage import ReceiptStorageService
from ..functions.processing import process_receipt_batch
from ...agents.receipt_agent import ReceiptAgent


# Router for batch processing endpoints
router = APIRouter(prefix="/batch", tags=["batch_processing"])

# In-memory storage for batch processing status (use Redis in production)
batch_jobs: Dict[str, Dict[str, Any]] = {}


class BatchJobManager:
    """Manages batch processing jobs."""

    @staticmethod
    def create_job(job_id: str, total_files: int, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new batch job."""
        job = {
            "job_id": job_id,
            "status": "pending",
            "total_files": total_files,
            "processed_files": 0,
            "successful": 0,
            "failed": 0,
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None,
            "options": options,
            "results": [],
            "errors": [],
            "progress_percentage": 0.0
        }
        batch_jobs[job_id] = job
        return job

    @staticmethod
    def update_job(job_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update a batch job."""
        if job_id not in batch_jobs:
            return None

        job = batch_jobs[job_id]
        job.update(updates)
        job["updated_at"] = datetime.utcnow()

        # Calculate progress
        if job["total_files"] > 0:
            job["progress_percentage"] = (job["processed_files"] / job["total_files"]) * 100

        return job

    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        """Get a batch job."""
        return batch_jobs.get(job_id)

    @staticmethod
    def complete_job(job_id: str) -> Optional[Dict[str, Any]]:
        """Mark a job as completed."""
        if job_id not in batch_jobs:
            return None

        job = batch_jobs[job_id]
        job["status"] = "completed"
        job["completed_at"] = datetime.utcnow()
        job["progress_percentage"] = 100.0

        return job

    @staticmethod
    def fail_job(job_id: str, error: str) -> Optional[Dict[str, Any]]:
        """Mark a job as failed."""
        if job_id not in batch_jobs:
            return None

        job = batch_jobs[job_id]
        job["status"] = "failed"
        job["completed_at"] = datetime.utcnow()
        job["errors"].append({
            "timestamp": datetime.utcnow(),
            "error": error
        })

        return job


async def process_batch_job(
    job_id: str,
    files_data: List[Dict[str, Any]],
    options: Dict[str, Any],
    agent: ReceiptAgent,
    storage: ReceiptStorageService
):
    """Process a batch job in the background."""
    try:
        # Update job status
        BatchJobManager.update_job(job_id, status="processing")

        results = []

        for i, file_data in enumerate(files_data):
            try:
                # Process individual receipt
                result = await agent.execute({
                    "file_data": file_data["data"],
                    "file_name": file_data["filename"],
                    **options
                })

                # Store result
                if result.get("success") and result.get("receipt"):
                    # Store receipt in storage service
                    receipt = result["receipt"]  # Assume this is a Receipt object
                    await storage.store_receipt(receipt, file_data["data"])

                results.append({
                    "filename": file_data["filename"],
                    "success": result.get("success", False),
                    "receipt_id": result.get("receipt", {}).get("receipt_id") if result.get("receipt") else None,
                    "error": result.get("error"),
                    "processing_time": result.get("processing_time", 0.0)
                })

                # Update progress
                processed = i + 1
                successful = sum(1 for r in results if r["success"])
                failed = processed - successful

                BatchJobManager.update_job(
                    job_id,
                    processed_files=processed,
                    successful=successful,
                    failed=failed,
                    results=results
                )

            except Exception as e:
                results.append({
                    "filename": file_data["filename"],
                    "success": False,
                    "error": str(e),
                    "processing_time": 0.0
                })

                # Update progress with error
                processed = i + 1
                successful = sum(1 for r in results if r["success"])
                failed = processed - successful

                BatchJobManager.update_job(
                    job_id,
                    processed_files=processed,
                    successful=successful,
                    failed=failed,
                    results=results
                )

        # Complete the job
        BatchJobManager.complete_job(job_id)

    except Exception as e:
        BatchJobManager.fail_job(job_id, str(e))


@router.post("/process", response_model=dict)
async def start_batch_processing(
    files: List[UploadFile] = File(..., description="Receipt image files"),
    extract_line_items: bool = Form(True, description="Extract individual line items"),
    categorize_items: bool = Form(True, description="Categorize line items"),
    validate_totals: bool = Form(True, description="Validate mathematical totals"),
    max_concurrent: int = Form(3, ge=1, le=10, description="Maximum concurrent processing"),
    continue_on_error: bool = Form(True, description="Continue processing if individual receipts fail"),
    background_tasks: BackgroundTasks = ...,
    agent: ReceiptAgent = Depends(lambda: None),  # Get from dependency
    storage: ReceiptStorageService = Depends(lambda: None)  # Get from dependency
):
    """
    Start batch processing of multiple receipt files.

    Upload multiple receipt images for batch processing. Returns a job ID
    that can be used to track processing progress and retrieve results.
    """
    # Validate batch size
    if len(files) > 20:  # MAX_BATCH_SIZE
        raise HTTPException(
            status_code=413,
            detail=f"Too many files. Maximum batch size is 20 files"
        )

    # Validate files and read data
    files_data = []
    for file in files:
        # Basic validation
        if file.size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=413,
                detail=f"File {file.filename} is too large. Maximum size is 10MB"
            )

        # Read file data
        file_data = await file.read()
        files_data.append({
            "filename": file.filename,
            "data": file_data,
            "size": len(file_data),
            "content_type": file.content_type
        })

    # Create batch job
    job_id = str(uuid.uuid4())
    options = {
        "extract_line_items": extract_line_items,
        "categorize_items": categorize_items,
        "validate_totals": validate_totals,
        "max_concurrent": max_concurrent,
        "continue_on_error": continue_on_error
    }

    job = BatchJobManager.create_job(job_id, len(files), options)

    # Start background processing
    background_tasks.add_task(
        process_batch_job,
        job_id,
        files_data,
        options,
        agent,
        storage
    )

    return {
        "job_id": job_id,
        "status": "started",
        "total_files": len(files),
        "message": "Batch processing started. Use the job_id to check status."
    }


@router.get("/jobs/{job_id}/status", response_model=dict)
async def get_batch_status(
    job_id: str = PathParam(..., description="Batch job ID")
):
    """Get the status of a batch processing job."""
    job = BatchJobManager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    return {
        "job_id": job_id,
        "status": job["status"],
        "total_files": job["total_files"],
        "processed_files": job["processed_files"],
        "successful": job["successful"],
        "failed": job["failed"],
        "progress_percentage": job["progress_percentage"],
        "started_at": job["started_at"],
        "updated_at": job["updated_at"],
        "completed_at": job["completed_at"],
        "estimated_completion": None  # Could implement ETA calculation
    }


@router.get("/jobs/{job_id}/results", response_model=BatchProcessingResultModel)
async def get_batch_results(
    job_id: str = PathParam(..., description="Batch job ID"),
    include_details: bool = Query(False, description="Include detailed receipt data")
):
    """Get the results of a batch processing job."""
    job = BatchJobManager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    if job["status"] not in ["completed", "failed"]:
        raise HTTPException(
            status_code=409,
            detail=f"Job is still {job['status']}. Results not yet available."
        )

    processing_time = 0.0
    if job["completed_at"] and job["started_at"]:
        processing_time = (job["completed_at"] - job["started_at"]).total_seconds()

    return BatchProcessingResultModel(
        total_files=job["total_files"],
        successful=job["successful"],
        failed=job["failed"],
        processing_time=processing_time,
        results=job["results"],
        summary={
            "success_rate": (job["successful"] / job["total_files"]) * 100 if job["total_files"] > 0 else 0,
            "avg_processing_time": processing_time / job["total_files"] if job["total_files"] > 0 else 0,
            "status": job["status"],
            "job_id": job_id
        }
    )


@router.get("/jobs", response_model=List[dict])
async def list_batch_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of jobs to return")
):
    """List batch processing jobs."""
    jobs = list(batch_jobs.values())

    # Filter by status if provided
    if status:
        jobs = [job for job in jobs if job["status"] == status]

    # Sort by creation time (most recent first)
    jobs.sort(key=lambda x: x["started_at"], reverse=True)

    # Apply limit
    jobs = jobs[:limit]

    # Return simplified job info
    return [
        {
            "job_id": job["job_id"],
            "status": job["status"],
            "total_files": job["total_files"],
            "processed_files": job["processed_files"],
            "successful": job["successful"],
            "failed": job["failed"],
            "progress_percentage": job["progress_percentage"],
            "started_at": job["started_at"],
            "completed_at": job["completed_at"]
        }
        for job in jobs
    ]


@router.delete("/jobs/{job_id}")
async def cancel_batch_job(
    job_id: str = PathParam(..., description="Batch job ID")
):
    """Cancel a batch processing job."""
    job = BatchJobManager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    if job["status"] in ["completed", "failed"]:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel job that is already {job['status']}"
        )

    # Mark as cancelled
    BatchJobManager.update_job(job_id, status="cancelled")

    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Batch job cancelled successfully"
    }


@router.post("/jobs/{job_id}/retry")
async def retry_batch_job(
    job_id: str = PathParam(..., description="Batch job ID"),
    retry_failed_only: bool = Query(True, description="Only retry failed files"),
    background_tasks: BackgroundTasks = ...,
    agent: ReceiptAgent = Depends(lambda: None),
    storage: ReceiptStorageService = Depends(lambda: None)
):
    """Retry a failed batch processing job."""
    job = BatchJobManager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    if job["status"] != "failed":
        raise HTTPException(
            status_code=409,
            detail="Can only retry failed jobs"
        )

    # Create new job for retry
    new_job_id = str(uuid.uuid4())

    # Determine which files to retry
    files_to_retry = []
    if retry_failed_only:
        # Only retry files that failed
        failed_results = [r for r in job["results"] if not r["success"]]
        # Note: We'd need to store the original file data to retry
        # For now, this is a conceptual implementation
    else:
        # Retry all files
        pass

    # For demonstration, create a placeholder retry job
    retry_job = BatchJobManager.create_job(new_job_id, len(files_to_retry), job["options"])

    return {
        "original_job_id": job_id,
        "retry_job_id": new_job_id,
        "status": "retry_started",
        "files_to_retry": len(files_to_retry),
        "message": "Retry job started. Use the new job_id to track progress."
    }