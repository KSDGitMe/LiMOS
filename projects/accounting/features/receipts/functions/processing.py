"""
Receipt Processing Functions

This module provides utility functions for receipt processing,
validation, and data transformation.
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..models.receipt import (
    Receipt,
    ReceiptLineItem,
    ReceiptType,
    ReceiptVendor,
    PaymentMethod
)


class ReceiptValidator:
    """Utility class for validating receipt data."""

    @staticmethod
    def validate_amounts(receipt: Receipt) -> List[str]:
        """Validate all monetary amounts in the receipt."""
        errors = []

        # Check for negative amounts
        if receipt.subtotal < 0:
            errors.append("Subtotal cannot be negative")

        if receipt.tax_amount < 0:
            errors.append("Tax amount cannot be negative")

        if receipt.total_amount <= 0:
            errors.append("Total amount must be positive")

        # Validate line item amounts
        for i, item in enumerate(receipt.line_items):
            if item.total_price <= 0:
                errors.append(f"Line item {i+1} total price must be positive")

            if item.quantity and item.quantity <= 0:
                errors.append(f"Line item {i+1} quantity must be positive")

            if item.unit_price and item.quantity:
                expected_total = item.unit_price * Decimal(str(item.quantity))
                if abs(expected_total - item.total_price) > Decimal('0.01'):
                    errors.append(f"Line item {i+1} price calculation mismatch")

        return errors

    @staticmethod
    def validate_totals(receipt: Receipt, tolerance: Decimal = Decimal('0.01')) -> List[str]:
        """Validate that receipt totals are mathematically correct."""
        errors = []

        # Calculate expected total
        expected_total = receipt.subtotal + receipt.tax_amount

        if receipt.tip_amount:
            expected_total += receipt.tip_amount

        if receipt.discount_amount:
            expected_total -= receipt.discount_amount

        # Check total
        difference = abs(expected_total - receipt.total_amount)
        if difference > tolerance:
            errors.append(f"Total amount mismatch: expected {expected_total}, got {receipt.total_amount}")

        # Validate line items sum to subtotal
        if receipt.line_items:
            line_items_total = sum(item.total_price for item in receipt.line_items)
            subtotal_difference = abs(line_items_total - receipt.subtotal)
            if subtotal_difference > tolerance:
                errors.append(f"Line items total {line_items_total} doesn't match subtotal {receipt.subtotal}")

        return errors

    @staticmethod
    def validate_vendor_info(receipt: Receipt) -> List[str]:
        """Validate vendor information."""
        warnings = []

        if not receipt.vendor.name or receipt.vendor.name.strip() == "":
            warnings.append("Vendor name is missing")

        if not receipt.vendor.address:
            warnings.append("Vendor address is missing")

        # Basic phone number validation
        if receipt.vendor.phone:
            phone_clean = re.sub(r'[^\d]', '', receipt.vendor.phone)
            if len(phone_clean) < 10:
                warnings.append("Phone number appears to be incomplete")

        return warnings

    @staticmethod
    def validate_date(receipt: Receipt) -> List[str]:
        """Validate receipt date."""
        errors = []

        # Check if date is too far in the future
        if receipt.date > datetime.now() + timedelta(days=1):
            errors.append("Receipt date is too far in the future")

        # Check if date is too old (configurable threshold)
        if receipt.date < datetime.now() - timedelta(days=365 * 5):  # 5 years
            errors.append("Receipt date is very old (over 5 years)")

        return errors


class ReceiptEnhancer:
    """Utility class for enhancing receipt data."""

    VENDOR_CATEGORIES = {
        # Grocery stores
        'walmart': ReceiptType.GROCERY,
        'kroger': ReceiptType.GROCERY,
        'safeway': ReceiptType.GROCERY,
        'whole foods': ReceiptType.GROCERY,
        'trader joe': ReceiptType.GROCERY,

        # Restaurants
        'mcdonald': ReceiptType.RESTAURANT,
        'subway': ReceiptType.RESTAURANT,
        'starbucks': ReceiptType.RESTAURANT,
        'chipotle': ReceiptType.RESTAURANT,

        # Gas stations
        'shell': ReceiptType.GAS_STATION,
        'chevron': ReceiptType.GAS_STATION,
        'exxon': ReceiptType.GAS_STATION,
        'bp': ReceiptType.GAS_STATION,

        # Pharmacies
        'cvs': ReceiptType.PHARMACY,
        'walgreens': ReceiptType.PHARMACY,
        'rite aid': ReceiptType.PHARMACY,

        # Retail
        'target': ReceiptType.RETAIL,
        'amazon': ReceiptType.RETAIL,
        'best buy': ReceiptType.RETAIL,
        'home depot': ReceiptType.RETAIL,
    }

    @staticmethod
    def enhance_receipt_type(receipt: Receipt) -> Receipt:
        """Automatically determine receipt type based on vendor."""
        vendor_name = receipt.vendor.name.lower()

        for keyword, receipt_type in ReceiptEnhancer.VENDOR_CATEGORIES.items():
            if keyword in vendor_name:
                receipt.receipt_type = receipt_type
                break

        return receipt

    @staticmethod
    def categorize_line_items(receipt: Receipt) -> Receipt:
        """Automatically categorize line items based on description."""
        category_keywords = {
            'Food': ['food', 'snack', 'bread', 'milk', 'meat', 'fruit', 'vegetable'],
            'Beverages': ['drink', 'soda', 'water', 'juice', 'coffee', 'tea'],
            'Personal Care': ['shampoo', 'soap', 'toothpaste', 'deodorant'],
            'Household': ['paper', 'towel', 'detergent', 'cleaner'],
            'Pharmacy': ['medicine', 'vitamin', 'prescription', 'pill'],
            'Automotive': ['gas', 'oil', 'tire', 'battery'],
            'Electronics': ['phone', 'computer', 'cable', 'battery'],
            'Clothing': ['shirt', 'pants', 'shoes', 'jacket'],
        }

        for item in receipt.line_items:
            if not item.category:
                description_lower = item.description.lower()
                for category, keywords in category_keywords.items():
                    if any(keyword in description_lower for keyword in keywords):
                        item.category = category
                        break
                else:
                    item.category = 'Other'

        return receipt

    @staticmethod
    def standardize_vendor_name(vendor_name: str) -> str:
        """Standardize vendor names for consistency."""
        # Common replacements
        replacements = {
            'walmart supercenter': 'Walmart',
            'walmart neighborhood market': 'Walmart',
            'target corp': 'Target',
            'kroger co': 'Kroger',
            'mcdonald\'s': 'McDonald\'s',
            'mc donald\'s': 'McDonald\'s',
        }

        name_lower = vendor_name.lower().strip()
        for pattern, replacement in replacements.items():
            if pattern in name_lower:
                return replacement

        # Capitalize properly
        return ' '.join(word.capitalize() for word in vendor_name.split())


class ReceiptParser:
    """Utility class for parsing various receipt formats."""

    @staticmethod
    def parse_amount(amount_str: str) -> Optional[Decimal]:
        """Parse amount string to Decimal."""
        if not amount_str:
            return None

        try:
            # Remove currency symbols and whitespace
            clean_amount = re.sub(r'[$€£¥,\s]', '', str(amount_str))

            # Handle negative amounts
            is_negative = False
            if clean_amount.startswith('-') or clean_amount.endswith('-'):
                is_negative = True
                clean_amount = clean_amount.replace('-', '')

            # Convert to Decimal
            amount = Decimal(clean_amount)

            return -amount if is_negative else amount

        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None

        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%d/%m/%Y',
            '%d/%m/%y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def parse_time(time_str: str) -> Optional[str]:
        """Parse and validate time string."""
        if not time_str:
            return None

        # Remove extra whitespace
        time_str = time_str.strip()

        # Common time formats
        time_patterns = [
            r'^(\d{1,2}):(\d{2}):(\d{2})$',  # HH:MM:SS
            r'^(\d{1,2}):(\d{2})$',         # HH:MM
            r'^(\d{1,2}):(\d{2})\s*(AM|PM)$',  # HH:MM AM/PM
        ]

        for pattern in time_patterns:
            match = re.match(pattern, time_str.upper())
            if match:
                return time_str

        return None

    @staticmethod
    def extract_card_info(text: str) -> Optional[str]:
        """Extract last 4 digits of card from text."""
        # Look for patterns like "****1234", "XXXX1234", "ending in 1234"
        patterns = [
            r'[*X]{4}(\d{4})',
            r'ending in (\d{4})',
            r'last 4: (\d{4})',
            r'card ending (\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None


class ReceiptMerger:
    """Utility class for merging receipt data from multiple sources."""

    @staticmethod
    def merge_receipts(primary: Receipt, secondary: Receipt) -> Receipt:
        """Merge two receipt objects, preferring primary data."""
        merged = primary.model_copy()

        # Merge vendor information
        if not merged.vendor.address and secondary.vendor.address:
            merged.vendor.address = secondary.vendor.address

        if not merged.vendor.phone and secondary.vendor.phone:
            merged.vendor.phone = secondary.vendor.phone

        # Merge missing line items
        if not merged.line_items and secondary.line_items:
            merged.line_items = secondary.line_items

        # Use higher confidence score
        if secondary.confidence_score > merged.confidence_score:
            merged.confidence_score = secondary.confidence_score

        return merged

    @staticmethod
    def combine_line_items(items1: List[ReceiptLineItem], items2: List[ReceiptLineItem]) -> List[ReceiptLineItem]:
        """Combine line items from two sources, removing duplicates."""
        combined = list(items1)

        for item2 in items2:
            # Check if item already exists (by description similarity)
            is_duplicate = False
            for item1 in items1:
                if ReceiptMerger._items_similar(item1, item2):
                    is_duplicate = True
                    break

            if not is_duplicate:
                combined.append(item2)

        return combined

    @staticmethod
    def _items_similar(item1: ReceiptLineItem, item2: ReceiptLineItem) -> bool:
        """Check if two line items are similar enough to be considered duplicates."""
        # Simple similarity check
        desc1 = item1.description.lower().strip()
        desc2 = item2.description.lower().strip()

        # Exact match
        if desc1 == desc2:
            return True

        # Price match with similar description
        if abs(item1.total_price - item2.total_price) < Decimal('0.01'):
            # Check if descriptions have significant overlap
            words1 = set(desc1.split())
            words2 = set(desc2.split())
            overlap = len(words1.intersection(words2))
            total_words = len(words1.union(words2))

            if total_words > 0 and overlap / total_words > 0.7:
                return True

        return False


async def process_receipt_batch(
    receipt_files: List[Path],
    agent,
    max_concurrent: int = 3
) -> List[Dict[str, Any]]:
    """Process multiple receipts concurrently."""

    async def process_single_receipt(file_path: Path) -> Dict[str, Any]:
        """Process a single receipt file."""
        try:
            result = await agent.execute({
                'file_path': str(file_path),
                'extract_line_items': True,
                'categorize_items': True,
                'validate_totals': True
            })
            return {
                'file_path': str(file_path),
                'success': result.get('success', False),
                'receipt': result.get('receipt'),
                'error': result.get('error')
            }
        except Exception as e:
            return {
                'file_path': str(file_path),
                'success': False,
                'error': str(e)
            }

    # Create semaphore to limit concurrent processing
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(file_path: Path):
        async with semaphore:
            return await process_single_receipt(file_path)

    # Process all receipts
    tasks = [process_with_semaphore(file_path) for file_path in receipt_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                'file_path': str(receipt_files[i]),
                'success': False,
                'error': str(result)
            })
        else:
            processed_results.append(result)

    return processed_results