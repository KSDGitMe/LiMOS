"""
Database module for Receipt Processing

This module provides database models, configuration, and access patterns
for the receipt processing system with master-detail relationships.
"""

from .models import Receipt, ReceiptLineItem, ReceiptVendor
from .database import get_db, engine, SessionLocal
from .repository import ReceiptRepository

__all__ = [
    "Receipt",
    "ReceiptLineItem",
    "ReceiptVendor",
    "get_db",
    "engine",
    "SessionLocal",
    "ReceiptRepository"
]