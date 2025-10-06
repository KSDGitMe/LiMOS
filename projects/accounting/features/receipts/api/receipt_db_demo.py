#!/usr/bin/env python3
"""
Receipt Database Demo

A standalone demo of the receipt database backend with master-detail relationships.
This script creates the database, inserts sample data, and provides a simple API.
"""

import os
import logging
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, DateTime, Numeric, Integer, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite:///./receipts_demo.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

# Enums
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

# Database Models
class ReceiptVendor(Base):
    __tablename__ = "receipt_vendors"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    created_at = Column(DateTime, default=func.now())

    receipts = relationship("Receipt", back_populates="vendor")

class Receipt(Base):
    __tablename__ = "receipts"

    receipt_id = Column(String, primary_key=True, default=generate_uuid)
    vendor_id = Column(String, ForeignKey("receipt_vendors.id"))
    date = Column(DateTime, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    receipt_type = Column(SQLEnum(ReceiptType), nullable=False)
    status = Column(SQLEnum(ReceiptStatus), nullable=False, default=ReceiptStatus.PROCESSED)
    is_business_expense = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    vendor = relationship("ReceiptVendor", back_populates="receipts")
    line_items = relationship("ReceiptLineItem", back_populates="receipt", cascade="all, delete-orphan")

class ReceiptLineItem(Base):
    __tablename__ = "receipt_line_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    receipt_id = Column(String, ForeignKey("receipts.receipt_id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100))
    created_at = Column(DateTime, default=func.now())

    receipt = relationship("Receipt", back_populates="line_items")

# Database functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with sample data."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Receipt).count() > 0:
            logger.info("Database already has data")
            return

        # Create sample vendor
        vendor = ReceiptVendor(
            name="Fresh Market",
            address="123 Main Street, Demo City, DC 12345",
            phone="555-123-4567"
        )
        db.add(vendor)
        db.flush()

        # Create sample receipt
        receipt = Receipt(
            vendor_id=vendor.id,
            date=datetime.now(),
            subtotal=Decimal("45.67"),
            tax_amount=Decimal("3.65"),
            total_amount=Decimal("49.32"),
            payment_method=PaymentMethod.CREDIT_CARD,
            receipt_type=ReceiptType.GROCERY,
            status=ReceiptStatus.PROCESSED,
            is_business_expense=False,
            notes="Weekly grocery shopping"
        )
        db.add(receipt)
        db.flush()

        # Create sample line items
        line_items = [
            ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=1,
                description="Organic Bananas",
                quantity=Decimal("2.5"),
                unit_price=Decimal("1.99"),
                total_price=Decimal("4.98"),
                category="produce"
            ),
            ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=2,
                description="Whole Milk - 1 Gallon",
                quantity=Decimal("1.0"),
                unit_price=Decimal("3.49"),
                total_price=Decimal("3.49"),
                category="dairy"
            ),
            ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=3,
                description="Chicken Breast - 2 lbs",
                quantity=Decimal("2.0"),
                unit_price=Decimal("6.99"),
                total_price=Decimal("13.98"),
                category="meat"
            ),
            ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=4,
                description="Bread - Whole Wheat",
                quantity=Decimal("1.0"),
                unit_price=Decimal("2.99"),
                total_price=Decimal("2.99"),
                category="bakery"
            ),
            ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=5,
                description="Greek Yogurt - 32oz",
                quantity=Decimal("1.0"),
                unit_price=Decimal("4.99"),
                total_price=Decimal("4.99"),
                category="dairy"
            ),
            ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=6,
                description="Apples - Gala 3lb bag",
                quantity=Decimal("1.0"),
                unit_price=Decimal("3.99"),
                total_price=Decimal("3.99"),
                category="produce"
            ),
            ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=7,
                description="Orange Juice - 64oz",
                quantity=Decimal("1.0"),
                unit_price=Decimal("3.49"),
                total_price=Decimal("3.49"),
                category="beverages"
            ),
            ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=8,
                description="Ground Coffee - 12oz",
                quantity=Decimal("1.0"),
                unit_price=Decimal("7.76"),
                total_price=Decimal("7.76"),
                category="beverages"
            )
        ]

        for item in line_items:
            db.add(item)

        db.commit()
        logger.info("Sample data created successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sample data: {e}")
    finally:
        db.close()

# FastAPI app
app = FastAPI(
    title="Receipt Database Demo",
    description="Master-Detail Receipt Processing with SQLAlchemy",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Receipt Database Demo...")
    init_database()
    logger.info("✅ Database initialized")

@app.get("/")
async def root():
    return {
        "name": "Receipt Database Demo",
        "description": "Master-Detail Receipt Processing with SQLAlchemy",
        "version": "1.0.0",
        "endpoints": {
            "receipts": "/receipts",
            "line_items": "/line-items",
            "statistics": "/statistics"
        }
    }

@app.get("/receipts")
async def get_receipts(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all receipts with their line items."""
    receipts = db.query(Receipt).limit(limit).all()

    return {
        "receipts": [
            {
                "receipt_id": receipt.receipt_id,
                "vendor": {
                    "name": receipt.vendor.name if receipt.vendor else "Unknown",
                    "address": receipt.vendor.address if receipt.vendor else None,
                    "phone": receipt.vendor.phone if receipt.vendor else None
                },
                "date": receipt.date.isoformat(),
                "subtotal": float(receipt.subtotal),
                "tax_amount": float(receipt.tax_amount),
                "total_amount": float(receipt.total_amount),
                "payment_method": receipt.payment_method.value,
                "receipt_type": receipt.receipt_type.value,
                "status": receipt.status.value,
                "line_items_count": len(receipt.line_items),
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
                "created_at": receipt.created_at.isoformat()
            }
            for receipt in receipts
        ],
        "total_count": len(receipts)
    }

@app.get("/receipts/{receipt_id}")
async def get_receipt(receipt_id: str, db: Session = Depends(get_db)):
    """Get a specific receipt with all line items."""
    receipt = db.query(Receipt).filter(Receipt.receipt_id == receipt_id).first()

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return {
        "receipt_id": receipt.receipt_id,
        "vendor": {
            "name": receipt.vendor.name if receipt.vendor else "Unknown",
            "address": receipt.vendor.address if receipt.vendor else None,
            "phone": receipt.vendor.phone if receipt.vendor else None
        },
        "date": receipt.date.isoformat(),
        "subtotal": float(receipt.subtotal),
        "tax_amount": float(receipt.tax_amount),
        "total_amount": float(receipt.total_amount),
        "payment_method": receipt.payment_method.value,
        "receipt_type": receipt.receipt_type.value,
        "status": receipt.status.value,
        "notes": receipt.notes,
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
            for item in sorted(receipt.line_items, key=lambda x: x.line_number)
        ],
        "totals": {
            "line_items_count": len(receipt.line_items),
            "calculated_subtotal": float(sum(item.total_price for item in receipt.line_items))
        }
    }

@app.get("/line-items")
async def get_line_items(
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get line items across all receipts, optionally filtered by category."""
    query = db.query(ReceiptLineItem)

    if category:
        query = query.filter(ReceiptLineItem.category == category)

    line_items = query.limit(limit).all()

    return {
        "line_items": [
            {
                "id": item.id,
                "receipt_id": item.receipt_id,
                "line_number": item.line_number,
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "total_price": float(item.total_price),
                "category": item.category,
                "receipt_info": {
                    "vendor_name": item.receipt.vendor.name if item.receipt.vendor else "Unknown",
                    "date": item.receipt.date.isoformat(),
                    "total_amount": float(item.receipt.total_amount)
                }
            }
            for item in line_items
        ],
        "total_count": len(line_items),
        "filter": {"category": category} if category else None
    }

@app.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get receipt and line item statistics."""
    # Basic counts
    total_receipts = db.query(Receipt).count()
    total_line_items = db.query(ReceiptLineItem).count()

    # Financial totals
    total_spent = db.query(func.sum(Receipt.total_amount)).scalar() or 0
    avg_receipt = db.query(func.avg(Receipt.total_amount)).scalar() or 0

    # Category breakdown
    category_stats = db.query(
        ReceiptLineItem.category,
        func.count(ReceiptLineItem.id).label('item_count'),
        func.sum(ReceiptLineItem.total_price).label('category_total')
    ).group_by(ReceiptLineItem.category).all()

    # Vendor breakdown
    vendor_stats = db.query(
        ReceiptVendor.name,
        func.count(Receipt.receipt_id).label('receipt_count'),
        func.sum(Receipt.total_amount).label('vendor_total')
    ).join(Receipt).group_by(ReceiptVendor.name).all()

    return {
        "totals": {
            "receipts": total_receipts,
            "line_items": total_line_items,
            "total_spent": float(total_spent),
            "average_receipt": float(avg_receipt)
        },
        "categories": [
            {
                "category": cat or "uncategorized",
                "item_count": count,
                "total_spent": float(total)
            }
            for cat, count, total in category_stats
        ],
        "vendors": [
            {
                "vendor_name": name,
                "receipt_count": count,
                "total_spent": float(total)
            }
            for name, count, total in vendor_stats
        ]
    }

@app.post("/receipts")
async def create_receipt(receipt_data: dict, db: Session = Depends(get_db)):
    """Create a new receipt with line items."""
    try:
        # Create or get vendor
        vendor_data = receipt_data.get("vendor", {})
        vendor = None
        if vendor_data.get("name"):
            vendor = db.query(ReceiptVendor).filter(
                ReceiptVendor.name == vendor_data["name"]
            ).first()

            if not vendor:
                vendor = ReceiptVendor(**vendor_data)
                db.add(vendor)
                db.flush()

        # Create receipt
        line_items_data = receipt_data.pop("line_items", [])
        receipt = Receipt(
            vendor_id=vendor.id if vendor else None,
            date=datetime.fromisoformat(receipt_data["date"]) if "date" in receipt_data else datetime.now(),
            subtotal=Decimal(str(receipt_data.get("subtotal", 0))),
            tax_amount=Decimal(str(receipt_data.get("tax_amount", 0))),
            total_amount=Decimal(str(receipt_data["total_amount"])),
            payment_method=PaymentMethod(receipt_data.get("payment_method", "credit_card")),
            receipt_type=ReceiptType(receipt_data.get("receipt_type", "other")),
            status=ReceiptStatus(receipt_data.get("status", "processed")),
            is_business_expense=receipt_data.get("is_business_expense", False),
            notes=receipt_data.get("notes")
        )
        db.add(receipt)
        db.flush()

        # Create line items
        for idx, item_data in enumerate(line_items_data):
            line_item = ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=idx + 1,
                description=item_data["description"],
                quantity=Decimal(str(item_data.get("quantity", 1))),
                unit_price=Decimal(str(item_data["unit_price"])),
                total_price=Decimal(str(item_data["total_price"])),
                category=item_data.get("category")
            )
            db.add(line_item)

        db.commit()

        return {
            "success": True,
            "receipt_id": receipt.receipt_id,
            "message": "Receipt created successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Receipt Database Demo...")
    uvicorn.run(
        "receipt_db_demo:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )