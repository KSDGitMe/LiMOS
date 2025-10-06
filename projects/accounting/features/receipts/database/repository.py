"""
Repository Pattern Implementation for Receipt Data Access

Provides a clean abstraction layer for database operations with
proper master-detail relationship handling.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc, func, text

from .models import Receipt, ReceiptLineItem, ReceiptVendor, ReceiptProcessingLog
from ..models.receipt import ReceiptType, ReceiptStatus, PaymentMethod


class ReceiptRepository:
    """Repository for receipt data access operations."""

    def __init__(self, db: Session):
        self.db = db

    # Create operations
    def create_receipt(self, receipt_data: Dict[str, Any]) -> Receipt:
        """
        Create a new receipt with line items.

        Args:
            receipt_data: Dictionary containing receipt and line items data

        Returns:
            Receipt: Created receipt with all relationships
        """
        # Extract vendor information
        vendor_data = receipt_data.get("vendor")
        vendor = None

        if vendor_data:
            vendor = self._get_or_create_vendor(vendor_data)

        # Create receipt
        line_items_data = receipt_data.pop("line_items", [])
        receipt = Receipt(
            vendor_id=vendor.id if vendor else None,
            **{k: v for k, v in receipt_data.items() if k != "vendor"}
        )

        self.db.add(receipt)
        self.db.flush()  # Get the receipt_id

        # Create line items
        for idx, item_data in enumerate(line_items_data):
            line_item = ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=idx + 1,
                **item_data
            )
            self.db.add(line_item)

        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def _get_or_create_vendor(self, vendor_data: Dict[str, Any]) -> ReceiptVendor:
        """Get existing vendor or create new one."""
        vendor_name = vendor_data.get("name")
        if not vendor_name:
            raise ValueError("Vendor name is required")

        # Try to find existing vendor
        vendor = self.db.query(ReceiptVendor).filter(
            ReceiptVendor.name == vendor_name
        ).first()

        if not vendor:
            vendor = ReceiptVendor(**vendor_data)
            self.db.add(vendor)
            self.db.flush()

        return vendor

    # Read operations
    def get_receipt_by_id(self, receipt_id: str) -> Optional[Receipt]:
        """Get receipt by ID with all relationships loaded."""
        return self.db.query(Receipt).options(
            joinedload(Receipt.vendor),
            selectinload(Receipt.line_items)
        ).filter(Receipt.receipt_id == receipt_id).first()

    def get_receipts_with_pagination(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Receipt], int]:
        """
        Get receipts with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters to apply

        Returns:
            Tuple of (receipts, total_count)
        """
        query = self.db.query(Receipt).options(
            joinedload(Receipt.vendor),
            selectinload(Receipt.line_items)
        )

        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)

        # Get total count
        total_count = query.count()

        # Apply pagination and ordering
        receipts = query.order_by(desc(Receipt.created_at)).offset(skip).limit(limit).all()

        return receipts, total_count

    def search_receipts(
        self,
        vendor_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        receipt_type: Optional[ReceiptType] = None,
        status: Optional[ReceiptStatus] = None,
        category: Optional[str] = None,
        is_business_expense: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Receipt], int]:
        """Advanced search with multiple criteria."""
        query = self.db.query(Receipt).options(
            joinedload(Receipt.vendor),
            selectinload(Receipt.line_items)
        )

        # Apply search filters
        if vendor_name:
            query = query.join(ReceiptVendor).filter(
                ReceiptVendor.name.ilike(f"%{vendor_name}%")
            )

        if date_from:
            query = query.filter(Receipt.date >= date_from)

        if date_to:
            query = query.filter(Receipt.date <= date_to)

        if min_amount:
            query = query.filter(Receipt.total_amount >= min_amount)

        if max_amount:
            query = query.filter(Receipt.total_amount <= max_amount)

        if receipt_type:
            query = query.filter(Receipt.receipt_type == receipt_type)

        if status:
            query = query.filter(Receipt.status == status)

        if category:
            query = query.filter(Receipt.category.ilike(f"%{category}%"))

        if is_business_expense is not None:
            query = query.filter(Receipt.is_business_expense == is_business_expense)

        if tags:
            # Search in JSON tags array
            for tag in tags:
                query = query.filter(Receipt.tags.contains([tag]))

        # Get total count
        total_count = query.count()

        # Apply pagination
        receipts = query.order_by(desc(Receipt.date)).offset(offset).limit(limit).all()

        return receipts, total_count

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query."""
        for key, value in filters.items():
            if value is None:
                continue

            if key == "vendor_name":
                query = query.join(ReceiptVendor).filter(
                    ReceiptVendor.name.ilike(f"%{value}%")
                )
            elif key == "date_from":
                query = query.filter(Receipt.date >= value)
            elif key == "date_to":
                query = query.filter(Receipt.date <= value)
            elif key == "min_amount":
                query = query.filter(Receipt.total_amount >= value)
            elif key == "max_amount":
                query = query.filter(Receipt.total_amount <= value)
            elif hasattr(Receipt, key):
                query = query.filter(getattr(Receipt, key) == value)

        return query

    # Update operations
    def update_receipt(self, receipt_id: str, update_data: Dict[str, Any]) -> Optional[Receipt]:
        """Update receipt information."""
        receipt = self.get_receipt_by_id(receipt_id)
        if not receipt:
            return None

        # Handle vendor updates
        if "vendor" in update_data:
            vendor_data = update_data.pop("vendor")
            vendor = self._get_or_create_vendor(vendor_data)
            receipt.vendor_id = vendor.id

        # Handle line items updates
        if "line_items" in update_data:
            line_items_data = update_data.pop("line_items")
            self._update_line_items(receipt, line_items_data)

        # Update receipt fields
        for key, value in update_data.items():
            if hasattr(receipt, key):
                setattr(receipt, key, value)

        receipt.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def _update_line_items(self, receipt: Receipt, line_items_data: List[Dict[str, Any]]):
        """Update receipt line items."""
        # Delete existing line items
        self.db.query(ReceiptLineItem).filter(
            ReceiptLineItem.receipt_id == receipt.receipt_id
        ).delete()

        # Create new line items
        for idx, item_data in enumerate(line_items_data):
            line_item = ReceiptLineItem(
                receipt_id=receipt.receipt_id,
                line_number=idx + 1,
                **item_data
            )
            self.db.add(line_item)

    def add_line_item(self, receipt_id: str, line_item_data: Dict[str, Any]) -> Optional[ReceiptLineItem]:
        """Add a new line item to existing receipt."""
        receipt = self.get_receipt_by_id(receipt_id)
        if not receipt:
            return None

        # Get next line number
        max_line = self.db.query(func.max(ReceiptLineItem.line_number)).filter(
            ReceiptLineItem.receipt_id == receipt_id
        ).scalar() or 0

        line_item = ReceiptLineItem(
            receipt_id=receipt_id,
            line_number=max_line + 1,
            **line_item_data
        )

        self.db.add(line_item)
        self.db.commit()
        self.db.refresh(line_item)
        return line_item

    def update_line_item(self, line_item_id: str, update_data: Dict[str, Any]) -> Optional[ReceiptLineItem]:
        """Update a specific line item."""
        line_item = self.db.query(ReceiptLineItem).filter(
            ReceiptLineItem.id == line_item_id
        ).first()

        if not line_item:
            return None

        for key, value in update_data.items():
            if hasattr(line_item, key):
                setattr(line_item, key, value)

        line_item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(line_item)
        return line_item

    # Delete operations
    def delete_receipt(self, receipt_id: str) -> bool:
        """Delete receipt and all associated line items."""
        receipt = self.get_receipt_by_id(receipt_id)
        if not receipt:
            return False

        self.db.delete(receipt)
        self.db.commit()
        return True

    def delete_line_item(self, line_item_id: str) -> bool:
        """Delete a specific line item."""
        line_item = self.db.query(ReceiptLineItem).filter(
            ReceiptLineItem.id == line_item_id
        ).first()

        if not line_item:
            return False

        self.db.delete(line_item)
        self.db.commit()
        return True

    # Analytics and statistics
    def get_receipt_statistics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get receipt statistics."""
        query = self.db.query(Receipt)

        if filters:
            query = self._apply_filters(query, filters)

        total_receipts = query.count()
        total_amount = query.with_entities(func.sum(Receipt.total_amount)).scalar() or 0
        avg_amount = query.with_entities(func.avg(Receipt.total_amount)).scalar() or 0

        # Top vendors
        top_vendors = self.db.query(
            ReceiptVendor.name,
            func.count(Receipt.receipt_id).label("receipt_count"),
            func.sum(Receipt.total_amount).label("total_spent")
        ).join(Receipt).group_by(ReceiptVendor.name).order_by(
            desc("total_spent")
        ).limit(10).all()

        # Receipt types breakdown
        type_breakdown = self.db.query(
            Receipt.receipt_type,
            func.count(Receipt.receipt_id).label("count"),
            func.sum(Receipt.total_amount).label("total")
        ).group_by(Receipt.receipt_type).all()

        # Monthly trends (last 12 months)
        monthly_trends = self.db.query(
            func.date_trunc('month', Receipt.date).label('month'),
            func.count(Receipt.receipt_id).label('count'),
            func.sum(Receipt.total_amount).label('total')
        ).filter(
            Receipt.date >= datetime.utcnow().replace(day=1, month=1)  # This year
        ).group_by('month').order_by('month').all()

        return {
            "total_receipts": total_receipts,
            "total_amount": float(total_amount),
            "average_amount": float(avg_amount),
            "top_vendors": [
                {"name": name, "receipt_count": count, "total_spent": float(total)}
                for name, count, total in top_vendors
            ],
            "receipt_types": [
                {"type": str(type_), "count": count, "total": float(total)}
                for type_, count, total in type_breakdown
            ],
            "monthly_trends": [
                {"month": month.isoformat(), "count": count, "total": float(total)}
                for month, count, total in monthly_trends
            ]
        }

    def get_vendor_statistics(self, vendor_id: str) -> Dict[str, Any]:
        """Get statistics for a specific vendor."""
        vendor = self.db.query(ReceiptVendor).filter(ReceiptVendor.id == vendor_id).first()
        if not vendor:
            return {}

        receipts = self.db.query(Receipt).filter(Receipt.vendor_id == vendor_id)

        total_receipts = receipts.count()
        total_spent = receipts.with_entities(func.sum(Receipt.total_amount)).scalar() or 0
        avg_amount = receipts.with_entities(func.avg(Receipt.total_amount)).scalar() or 0

        # Most recent visit
        last_visit = receipts.order_by(desc(Receipt.date)).first()

        # Most purchased items
        top_items = self.db.query(
            ReceiptLineItem.description,
            func.sum(ReceiptLineItem.quantity).label("total_quantity"),
            func.sum(ReceiptLineItem.total_price).label("total_spent")
        ).join(Receipt).filter(
            Receipt.vendor_id == vendor_id
        ).group_by(ReceiptLineItem.description).order_by(
            desc("total_spent")
        ).limit(10).all()

        return {
            "vendor": {
                "id": vendor.id,
                "name": vendor.name,
                "address": vendor.address,
                "phone": vendor.phone
            },
            "total_receipts": total_receipts,
            "total_spent": float(total_spent),
            "average_amount": float(avg_amount),
            "last_visit": last_visit.date.isoformat() if last_visit else None,
            "top_items": [
                {
                    "description": desc,
                    "total_quantity": float(qty),
                    "total_spent": float(spent)
                }
                for desc, qty, spent in top_items
            ]
        }

    # Line item specific operations
    def get_line_items_by_receipt(self, receipt_id: str) -> List[ReceiptLineItem]:
        """Get all line items for a receipt."""
        return self.db.query(ReceiptLineItem).filter(
            ReceiptLineItem.receipt_id == receipt_id
        ).order_by(ReceiptLineItem.line_number).all()

    def search_line_items(
        self,
        description: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        limit: int = 100
    ) -> List[ReceiptLineItem]:
        """Search line items across all receipts."""
        query = self.db.query(ReceiptLineItem).options(joinedload(ReceiptLineItem.receipt))

        if description:
            query = query.filter(ReceiptLineItem.description.ilike(f"%{description}%"))

        if category:
            query = query.filter(ReceiptLineItem.category.ilike(f"%{category}%"))

        if min_price:
            query = query.filter(ReceiptLineItem.unit_price >= min_price)

        if max_price:
            query = query.filter(ReceiptLineItem.unit_price <= max_price)

        return query.order_by(desc(ReceiptLineItem.created_at)).limit(limit).all()

    # Bulk operations
    def bulk_update_receipts(self, receipt_ids: List[str], update_data: Dict[str, Any]) -> int:
        """Bulk update multiple receipts."""
        updated_count = self.db.query(Receipt).filter(
            Receipt.receipt_id.in_(receipt_ids)
        ).update(update_data, synchronize_session=False)

        self.db.commit()
        return updated_count

    def bulk_delete_receipts(self, receipt_ids: List[str]) -> int:
        """Bulk delete multiple receipts."""
        deleted_count = self.db.query(Receipt).filter(
            Receipt.receipt_id.in_(receipt_ids)
        ).delete(synchronize_session=False)

        self.db.commit()
        return deleted_count