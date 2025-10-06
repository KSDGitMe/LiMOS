"""
Receipt Data Models

This module defines the data models for receipt processing,
including receipt metadata, line items, and processing results.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ReceiptStatus(str, Enum):
    """Receipt processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    VALIDATED = "validated"
    ARCHIVED = "archived"


class ReceiptType(str, Enum):
    """Type of receipt."""
    GROCERY = "grocery"
    RESTAURANT = "restaurant"
    GAS_STATION = "gas_station"
    RETAIL = "retail"
    PHARMACY = "pharmacy"
    OFFICE_SUPPLIES = "office_supplies"
    TRAVEL = "travel"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    SERVICES = "services"
    OTHER = "other"


class PaymentMethod(str, Enum):
    """Payment method used."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CHECK = "check"
    DIGITAL_WALLET = "digital_wallet"
    BANK_TRANSFER = "bank_transfer"
    OTHER = "other"


class ReceiptLineItem(BaseModel):
    """Individual line item on a receipt."""
    description: str = Field(..., description="Item description")
    quantity: Optional[float] = Field(default=1.0, description="Quantity purchased")
    unit_price: Optional[Decimal] = Field(default=None, description="Price per unit")
    total_price: Decimal = Field(..., description="Total price for this item")
    category: Optional[str] = Field(default=None, description="Item category")
    sku: Optional[str] = Field(default=None, description="Stock keeping unit")
    tax_amount: Optional[Decimal] = Field(default=None, description="Tax for this item")
    discount_amount: Optional[Decimal] = Field(default=None, description="Discount applied")

    @validator('total_price', 'unit_price', 'tax_amount', 'discount_amount')
    def validate_decimal_precision(cls, v):
        """Ensure decimal values have appropriate precision for currency."""
        if v is not None:
            return round(v, 2)
        return v

    @validator('quantity')
    def validate_quantity(cls, v):
        """Ensure quantity is positive."""
        if v is not None and v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class ReceiptTax(BaseModel):
    """Tax information from receipt."""
    tax_type: str = Field(..., description="Type of tax (sales, VAT, etc.)")
    tax_rate: Optional[float] = Field(default=None, description="Tax rate as percentage")
    tax_amount: Decimal = Field(..., description="Tax amount")
    taxable_amount: Optional[Decimal] = Field(default=None, description="Amount subject to tax")

    @validator('tax_amount', 'taxable_amount')
    def validate_decimal_precision(cls, v):
        """Ensure decimal values have appropriate precision for currency."""
        if v is not None:
            return round(v, 2)
        return v


class ReceiptVendor(BaseModel):
    """Vendor/merchant information."""
    name: str = Field(..., description="Vendor name")
    address: Optional[str] = Field(default=None, description="Vendor address")
    phone: Optional[str] = Field(default=None, description="Vendor phone number")
    email: Optional[str] = Field(default=None, description="Vendor email")
    website: Optional[str] = Field(default=None, description="Vendor website")
    tax_id: Optional[str] = Field(default=None, description="Vendor tax ID")
    store_number: Optional[str] = Field(default=None, description="Store number")


class ReceiptMetadata(BaseModel):
    """Receipt processing metadata."""
    source_file: Optional[str] = Field(default=None, description="Original file path/name")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    file_type: Optional[str] = Field(default=None, description="File MIME type")
    image_dimensions: Optional[tuple] = Field(default=None, description="Image width, height")
    ocr_confidence: Optional[float] = Field(default=None, description="OCR confidence score")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")
    claude_model: Optional[str] = Field(default=None, description="Claude model used")
    api_tokens_used: Optional[int] = Field(default=None, description="API tokens consumed")


class Receipt(BaseModel):
    """Complete receipt data model."""
    # Identifiers
    receipt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Basic receipt information
    vendor: ReceiptVendor
    receipt_number: Optional[str] = Field(default=None, description="Receipt/transaction number")
    date: datetime = Field(..., description="Transaction date")
    time: Optional[str] = Field(default=None, description="Transaction time")

    # Financial information
    subtotal: Decimal = Field(..., description="Subtotal before taxes and fees")
    tax_amount: Decimal = Field(default=Decimal('0.00'), description="Total tax amount")
    tip_amount: Optional[Decimal] = Field(default=None, description="Tip amount")
    discount_amount: Optional[Decimal] = Field(default=None, description="Total discount")
    total_amount: Decimal = Field(..., description="Final total amount")

    # Payment information
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    card_last_four: Optional[str] = Field(default=None, description="Last 4 digits of card")

    # Classification
    receipt_type: ReceiptType = Field(default=ReceiptType.OTHER)
    category: Optional[str] = Field(default=None, description="Business category")

    # Line items and taxes
    line_items: List[ReceiptLineItem] = Field(default_factory=list)
    taxes: List[ReceiptTax] = Field(default_factory=list)

    # Processing information
    status: ReceiptStatus = Field(default=ReceiptStatus.PENDING)
    confidence_score: float = Field(default=0.0, description="Overall processing confidence")

    # Metadata
    metadata: ReceiptMetadata = Field(default_factory=ReceiptMetadata)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(default=None)

    # Custom fields for additional data
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    # Notes and flags
    notes: Optional[str] = Field(default=None, description="Additional notes")
    is_business_expense: bool = Field(default=False, description="Business expense flag")
    is_reimbursable: bool = Field(default=False, description="Reimbursable expense flag")

    @validator('total_amount', 'subtotal', 'tax_amount', 'tip_amount', 'discount_amount')
    def validate_decimal_precision(cls, v):
        """Ensure decimal values have appropriate precision for currency."""
        if v is not None:
            return round(v, 2)
        return v

    @validator('card_last_four')
    def validate_card_last_four(cls, v):
        """Validate card last four digits format."""
        if v is not None:
            if not v.isdigit() or len(v) != 4:
                raise ValueError("Card last four must be exactly 4 digits")
        return v

    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        """Ensure confidence score is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return v

    def calculate_totals(self) -> None:
        """Calculate and validate totals based on line items."""
        if self.line_items:
            calculated_subtotal = sum(item.total_price for item in self.line_items)
            calculated_tax = sum(item.tax_amount or Decimal('0.00') for item in self.line_items)
            calculated_discount = sum(item.discount_amount or Decimal('0.00') for item in self.line_items)

            # Update calculated values
            self.subtotal = calculated_subtotal
            if not self.taxes:  # Only update if no explicit tax breakdown
                self.tax_amount = calculated_tax
            if self.discount_amount is None:
                self.discount_amount = calculated_discount

    def validate_totals(self) -> bool:
        """Validate that totals are mathematically correct."""
        expected_total = self.subtotal + self.tax_amount
        if self.tip_amount:
            expected_total += self.tip_amount
        if self.discount_amount:
            expected_total -= self.discount_amount

        # Allow for small rounding differences
        return abs(expected_total - self.total_amount) < Decimal('0.01')

    def get_items_by_category(self, category: str) -> List[ReceiptLineItem]:
        """Get all line items for a specific category."""
        return [item for item in self.line_items if item.category == category]

    def get_total_by_category(self, category: str) -> Decimal:
        """Get total amount for a specific category."""
        return sum(item.total_price for item in self.get_items_by_category(category))

    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary with serializable values."""
        data = self.model_dump()

        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(v) for v in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        return convert_decimals(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Receipt":
        """Create receipt from dictionary."""
        # Convert datetime strings back to datetime objects
        if 'date' in data and isinstance(data['date'], str):
            data['date'] = datetime.fromisoformat(data['date'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if 'processed_at' in data and isinstance(data['processed_at'], str):
            data['processed_at'] = datetime.fromisoformat(data['processed_at'])

        return cls(**data)


class ReceiptProcessingRequest(BaseModel):
    """Request model for receipt processing."""
    file_path: Optional[str] = Field(default=None, description="Path to receipt file")
    file_data: Optional[bytes] = Field(default=None, description="Raw file data")
    file_name: Optional[str] = Field(default=None, description="Original file name")
    processing_options: Dict[str, Any] = Field(default_factory=dict)

    # Processing preferences
    extract_line_items: bool = Field(default=True, description="Extract individual line items")
    categorize_items: bool = Field(default=True, description="Categorize line items")
    validate_totals: bool = Field(default=True, description="Validate mathematical totals")
    enhance_vendor_info: bool = Field(default=False, description="Enhance vendor information")

    # Business context
    default_category: Optional[str] = Field(default=None, description="Default expense category")
    business_context: Optional[str] = Field(default=None, description="Business context for categorization")


class ReceiptProcessingResult(BaseModel):
    """Result model for receipt processing."""
    receipt: Receipt
    processing_success: bool = Field(..., description="Whether processing succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")

    # Processing statistics
    processing_time: float = Field(..., description="Total processing time in seconds")
    tokens_used: Optional[int] = Field(default=None, description="API tokens consumed")
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)

    # Extracted data quality metrics
    ocr_confidence: Optional[float] = Field(default=None, description="OCR confidence score")
    extraction_confidence: Optional[float] = Field(default=None, description="Data extraction confidence")
    validation_score: Optional[float] = Field(default=None, description="Validation score")

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if processing result has high confidence."""
        return self.receipt.confidence_score >= threshold

    def needs_review(self) -> bool:
        """Determine if receipt needs manual review."""
        return (
            not self.processing_success or
            self.validation_errors or
            self.receipt.confidence_score < 0.7 or
            not self.receipt.validate_totals()
        )