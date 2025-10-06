"""
Receipt Data Models

This package provides data models for receipt processing,
including receipt structures, line items, and processing results.
"""

from .receipt import (
    Receipt,
    ReceiptLineItem,
    ReceiptTax,
    ReceiptVendor,
    ReceiptMetadata,
    ReceiptProcessingRequest,
    ReceiptProcessingResult,
    ReceiptStatus,
    ReceiptType,
    PaymentMethod
)

__all__ = [
    # Core models
    "Receipt",
    "ReceiptLineItem",
    "ReceiptTax",
    "ReceiptVendor",
    "ReceiptMetadata",

    # Processing models
    "ReceiptProcessingRequest",
    "ReceiptProcessingResult",

    # Enums
    "ReceiptStatus",
    "ReceiptType",
    "PaymentMethod",
]