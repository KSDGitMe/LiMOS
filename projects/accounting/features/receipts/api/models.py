"""
FastAPI Models for Receipt Processing API

This module defines Pydantic models for API requests and responses,
providing validation and serialization for the receipt processing endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

from fastapi import File, Form, UploadFile
from pydantic import BaseModel, Field, validator

from ..models.receipt import (
    Receipt,
    ReceiptStatus,
    ReceiptType,
    PaymentMethod
)


# Request Models
class ReceiptProcessingOptionsModel(BaseModel):
    """Options for receipt processing."""
    extract_line_items: bool = Field(default=True, description="Extract individual line items")
    categorize_items: bool = Field(default=True, description="Categorize line items")
    validate_totals: bool = Field(default=True, description="Validate mathematical totals")
    enhance_vendor_info: bool = Field(default=False, description="Enhance vendor information")
    business_context: Optional[str] = Field(default=None, description="Business context for categorization")


class ReceiptUploadModel(BaseModel):
    """Model for receipt upload request."""
    processing_options: ReceiptProcessingOptionsModel = Field(default_factory=ReceiptProcessingOptionsModel)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ReceiptSearchModel(BaseModel):
    """Model for receipt search request."""
    vendor_name: Optional[str] = Field(default=None, description="Filter by vendor name")
    date_from: Optional[datetime] = Field(default=None, description="Start date for search")
    date_to: Optional[datetime] = Field(default=None, description="End date for search")
    min_amount: Optional[float] = Field(default=None, ge=0, description="Minimum total amount")
    max_amount: Optional[float] = Field(default=None, ge=0, description="Maximum total amount")
    receipt_type: Optional[ReceiptType] = Field(default=None, description="Filter by receipt type")
    status: Optional[ReceiptStatus] = Field(default=None, description="Filter by receipt status")
    limit: Optional[int] = Field(default=50, ge=1, le=1000, description="Maximum number of results")
    offset: Optional[int] = Field(default=0, ge=0, description="Offset for pagination")

    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        """Ensure max_amount is greater than min_amount."""
        if v is not None and values.get('min_amount') is not None:
            if v < values['min_amount']:
                raise ValueError('max_amount must be greater than min_amount')
        return v


class ReceiptUpdateModel(BaseModel):
    """Model for receipt update request."""
    vendor_name: Optional[str] = Field(default=None, description="Update vendor name")
    receipt_type: Optional[ReceiptType] = Field(default=None, description="Update receipt type")
    category: Optional[str] = Field(default=None, description="Update category")
    notes: Optional[str] = Field(default=None, description="Update notes")
    is_business_expense: Optional[bool] = Field(default=None, description="Update business expense flag")
    is_reimbursable: Optional[bool] = Field(default=None, description="Update reimbursable flag")
    custom_fields: Optional[Dict[str, Any]] = Field(default=None, description="Update custom fields")


class BatchProcessingModel(BaseModel):
    """Model for batch processing request."""
    processing_options: ReceiptProcessingOptionsModel = Field(default_factory=ReceiptProcessingOptionsModel)
    max_concurrent: int = Field(default=3, ge=1, le=10, description="Maximum concurrent processing")
    continue_on_error: bool = Field(default=True, description="Continue processing if individual receipts fail")


class ExportRequestModel(BaseModel):
    """Model for export request."""
    format: str = Field(..., regex="^(json|csv)$", description="Export format")
    date_from: Optional[datetime] = Field(default=None, description="Start date for export")
    date_to: Optional[datetime] = Field(default=None, description="End date for export")
    vendor_name: Optional[str] = Field(default=None, description="Filter by vendor name")
    receipt_type: Optional[ReceiptType] = Field(default=None, description="Filter by receipt type")
    include_line_items: bool = Field(default=True, description="Include line items in export")


# Response Models
class ReceiptSummaryModel(BaseModel):
    """Summary model for receipt in lists."""
    receipt_id: str
    vendor_name: str
    date: datetime
    total_amount: float
    receipt_type: ReceiptType
    status: ReceiptStatus
    confidence_score: float
    line_items_count: int
    created_at: datetime

    @classmethod
    def from_receipt(cls, receipt: Receipt) -> "ReceiptSummaryModel":
        """Create summary from full receipt."""
        return cls(
            receipt_id=receipt.receipt_id,
            vendor_name=receipt.vendor.name,
            date=receipt.date,
            total_amount=float(receipt.total_amount),
            receipt_type=receipt.receipt_type,
            status=receipt.status,
            confidence_score=receipt.confidence_score,
            line_items_count=len(receipt.line_items),
            created_at=receipt.created_at
        )


class ReceiptDetailModel(BaseModel):
    """Detailed receipt model for API responses."""
    receipt_id: str
    vendor: Dict[str, Any]
    date: datetime
    receipt_number: Optional[str]
    subtotal: float
    tax_amount: float
    tip_amount: Optional[float]
    discount_amount: Optional[float]
    total_amount: float
    payment_method: PaymentMethod
    card_last_four: Optional[str]
    receipt_type: ReceiptType
    category: Optional[str]
    line_items: List[Dict[str, Any]]
    status: ReceiptStatus
    confidence_score: float
    notes: Optional[str]
    is_business_expense: bool
    is_reimbursable: bool
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    @classmethod
    def from_receipt(cls, receipt: Receipt) -> "ReceiptDetailModel":
        """Create detailed model from receipt."""
        return cls(
            receipt_id=receipt.receipt_id,
            vendor=receipt.vendor.model_dump(),
            date=receipt.date,
            receipt_number=receipt.receipt_number,
            subtotal=float(receipt.subtotal),
            tax_amount=float(receipt.tax_amount),
            tip_amount=float(receipt.tip_amount) if receipt.tip_amount else None,
            discount_amount=float(receipt.discount_amount) if receipt.discount_amount else None,
            total_amount=float(receipt.total_amount),
            payment_method=receipt.payment_method,
            card_last_four=receipt.card_last_four,
            receipt_type=receipt.receipt_type,
            category=receipt.category,
            line_items=[item.model_dump() for item in receipt.line_items],
            status=receipt.status,
            confidence_score=receipt.confidence_score,
            notes=receipt.notes,
            is_business_expense=receipt.is_business_expense,
            is_reimbursable=receipt.is_reimbursable,
            custom_fields=receipt.custom_fields,
            created_at=receipt.created_at,
            updated_at=receipt.updated_at,
            processed_at=receipt.processed_at
        )


class ProcessingResultModel(BaseModel):
    """Model for processing result response."""
    success: bool
    receipt: Optional[ReceiptDetailModel] = None
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    processing_time: float
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)
    agent_stats: Dict[str, Any] = Field(default_factory=dict)


class SearchResultModel(BaseModel):
    """Model for search results response."""
    receipts: List[ReceiptSummaryModel]
    total_count: int
    page_info: Dict[str, Any]
    filters_applied: Dict[str, Any]


class BatchProcessingResultModel(BaseModel):
    """Model for batch processing results."""
    total_files: int
    successful: int
    failed: int
    processing_time: float
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]


class StorageStatsModel(BaseModel):
    """Model for storage statistics."""
    total_receipts: int
    total_size_mb: float
    date_range: Dict[str, Any]
    receipt_types: Dict[str, int]
    top_vendors: List[tuple]
    storage_path: str


class ExportResultModel(BaseModel):
    """Model for export result."""
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    record_count: Optional[int] = None
    export_format: str
    generated_at: datetime
    error_message: Optional[str] = None


class HealthCheckModel(BaseModel):
    """Model for health check response."""
    status: str
    timestamp: datetime
    version: str
    agent_status: Dict[str, Any]
    storage_status: Dict[str, Any]
    dependencies: Dict[str, bool]


class ErrorResponseModel(BaseModel):
    """Model for error responses."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None


# Validation Models
class FileValidationModel(BaseModel):
    """Model for file validation."""
    filename: str
    size: int
    content_type: str
    is_valid: bool
    errors: List[str] = Field(default_factory=list)


# Statistics Models
class ReceiptStatsModel(BaseModel):
    """Model for receipt statistics."""
    period: str
    total_receipts: int
    total_amount: float
    avg_amount: float
    by_type: Dict[str, Dict[str, Union[int, float]]]
    by_vendor: List[Dict[str, Union[str, int, float]]]
    trends: Dict[str, Any]


class AgentStatsModel(BaseModel):
    """Model for agent performance statistics."""
    agent_id: str
    agent_name: str
    total_processed: int
    success_rate: float
    avg_processing_time: float
    confidence_scores: Dict[str, float]
    last_activity: datetime
    uptime: float


# Configuration Models
class APIConfigModel(BaseModel):
    """Model for API configuration."""
    max_file_size: int
    allowed_file_types: List[str]
    max_batch_size: int
    default_timeout: int
    rate_limits: Dict[str, int]
    features_enabled: Dict[str, bool]