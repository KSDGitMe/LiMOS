"""
SQLAlchemy Database Models for Receipt Processing

Defines the database schema with master-detail relationships between
receipts and their line items, with proper foreign key constraints.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Column, String, DateTime, Numeric, Integer, Boolean, Text,
    ForeignKey, Enum as SQLEnum, JSON, Index
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .database import Base
from ..models.receipt import ReceiptType, ReceiptStatus, PaymentMethod


def generate_uuid():
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class ReceiptVendor(Base):
    """Vendor information for receipts."""

    __tablename__ = "receipt_vendors"

    # Primary key
    id = Column(String, primary_key=True, default=generate_uuid)

    # Vendor details
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))

    # Business information
    tax_id = Column(String(50))
    business_type = Column(String(100))

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    receipts = relationship("Receipt", back_populates="vendor")

    # Indexes
    __table_args__ = (
        Index('idx_vendor_name', 'name'),
        Index('idx_vendor_phone', 'phone'),
    )

    def __repr__(self):
        return f"<ReceiptVendor(id='{self.id}', name='{self.name}')>"


class Receipt(Base):
    """Master table for receipts with all transaction details."""

    __tablename__ = "receipts"

    # Primary key
    receipt_id = Column(String, primary_key=True, default=generate_uuid)

    # Foreign keys
    vendor_id = Column(String, ForeignKey("receipt_vendors.id"), nullable=True)

    # Receipt metadata
    receipt_number = Column(String(100))
    date = Column(DateTime, nullable=False, index=True)
    time = Column(DateTime)

    # Financial details
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    tip_amount = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Payment information
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    payment_reference = Column(String(100))

    # Classification
    receipt_type = Column(SQLEnum(ReceiptType), nullable=False, index=True)
    category = Column(String(100), index=True)

    # Processing information
    status = Column(SQLEnum(ReceiptStatus), nullable=False, default=ReceiptStatus.PENDING, index=True)
    confidence_score = Column(Numeric(3, 2), default=0.0)
    processing_time = Column(Numeric(8, 3))

    # File information
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_hash = Column(String(64))

    # Business flags
    is_business_expense = Column(Boolean, default=False, index=True)
    is_reimbursable = Column(Boolean, default=False)
    is_tax_deductible = Column(Boolean, default=False)

    # Additional information
    notes = Column(Text)
    tags = Column(JSON)
    custom_fields = Column(JSON)

    # AI processing metadata
    ai_extracted_data = Column(JSON)
    ai_confidence_breakdown = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime)

    # Relationships
    vendor = relationship("ReceiptVendor", back_populates="receipts")
    line_items = relationship(
        "ReceiptLineItem",
        back_populates="receipt",
        cascade="all, delete-orphan",
        order_by="ReceiptLineItem.line_number"
    )

    # Indexes
    __table_args__ = (
        Index('idx_receipt_date', 'date'),
        Index('idx_receipt_vendor_date', 'vendor_id', 'date'),
        Index('idx_receipt_total', 'total_amount'),
        Index('idx_receipt_type_date', 'receipt_type', 'date'),
        Index('idx_receipt_business', 'is_business_expense'),
        Index('idx_receipt_status', 'status'),
    )

    @property
    def line_items_count(self) -> int:
        """Get the number of line items."""
        return len(self.line_items) if self.line_items else 0

    def calculate_totals(self) -> dict:
        """Calculate totals from line items."""
        if not self.line_items:
            return {
                "subtotal": Decimal("0.00"),
                "item_count": 0,
                "average_item_price": Decimal("0.00")
            }

        subtotal = sum(item.total_price for item in self.line_items)
        item_count = len(self.line_items)
        avg_price = subtotal / item_count if item_count > 0 else Decimal("0.00")

        return {
            "subtotal": subtotal,
            "item_count": item_count,
            "average_item_price": avg_price
        }

    def __repr__(self):
        return f"<Receipt(id='{self.receipt_id}', vendor='{self.vendor.name if self.vendor else 'Unknown'}', total={self.total_amount})>"


class ReceiptLineItem(Base):
    """Detail table for individual items on receipts."""

    __tablename__ = "receipt_line_items"

    # Primary key
    id = Column(String, primary_key=True, default=generate_uuid)

    # Foreign key to receipt (master table)
    receipt_id = Column(String, ForeignKey("receipts.receipt_id", ondelete="CASCADE"), nullable=False)

    # Line item details
    line_number = Column(Integer, nullable=False)
    description = Column(String(500), nullable=False)

    # Product information
    product_code = Column(String(100))
    brand = Column(String(100))
    size = Column(String(50))
    unit_of_measure = Column(String(20))

    # Pricing information
    quantity = Column(Numeric(10, 3), nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)

    # Classification
    category = Column(String(100), index=True)
    subcategory = Column(String(100))

    # Tax information
    is_taxable = Column(Boolean, default=True)
    tax_rate = Column(Numeric(5, 4))
    tax_amount = Column(Numeric(10, 2))

    # Additional information
    notes = Column(Text)
    tags = Column(JSON)

    # AI processing metadata
    ai_confidence = Column(Numeric(3, 2))
    ai_extracted_data = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    receipt = relationship("Receipt", back_populates="line_items")

    # Indexes
    __table_args__ = (
        Index('idx_line_item_receipt', 'receipt_id'),
        Index('idx_line_item_category', 'category'),
        Index('idx_line_item_price', 'unit_price'),
        Index('idx_line_item_receipt_line', 'receipt_id', 'line_number'),
    )

    def calculate_savings(self) -> Decimal:
        """Calculate savings from discount."""
        return self.discount_amount or Decimal("0.00")

    def calculate_tax(self) -> Decimal:
        """Calculate tax amount if not provided."""
        if self.tax_amount:
            return self.tax_amount

        if self.is_taxable and self.tax_rate:
            return (self.total_price * self.tax_rate).quantize(Decimal("0.01"))

        return Decimal("0.00")

    def __repr__(self):
        return f"<ReceiptLineItem(id='{self.id}', description='{self.description}', price={self.total_price})>"


# Additional models for future enhancement

class ReceiptCategory(Base):
    """Categories for receipt classification."""

    __tablename__ = "receipt_categories"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    parent_id = Column(String, ForeignKey("receipt_categories.id"))

    # Tax information
    is_tax_deductible = Column(Boolean, default=False)
    business_expense_category = Column(String(100))

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Self-referential relationship for hierarchical categories
    children = relationship("ReceiptCategory", backref=backref("parent", remote_side=[id]))


class ReceiptTag(Base):
    """Tags for flexible receipt organization."""

    __tablename__ = "receipt_tags"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7))  # Hex color code
    description = Column(Text)

    created_at = Column(DateTime, default=func.now())


class ReceiptProcessingLog(Base):
    """Log of processing attempts and results."""

    __tablename__ = "receipt_processing_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    receipt_id = Column(String, ForeignKey("receipts.receipt_id"), nullable=False)

    processing_type = Column(String(50), nullable=False)  # 'initial', 'reprocess', 'correction'
    status = Column(String(20), nullable=False)  # 'success', 'failure', 'partial'

    processing_time = Column(Numeric(8, 3))
    confidence_score = Column(Numeric(3, 2))

    # Results and errors
    extracted_data = Column(JSON)
    error_message = Column(Text)
    warnings = Column(JSON)

    # Processing metadata
    agent_version = Column(String(20))
    model_version = Column(String(50))
    processing_options = Column(JSON)

    created_at = Column(DateTime, default=func.now())

    # Relationships
    receipt = relationship("Receipt")

    # Indexes
    __table_args__ = (
        Index('idx_processing_log_receipt', 'receipt_id'),
        Index('idx_processing_log_status', 'status'),
        Index('idx_processing_log_type', 'processing_type'),
    )