"""
Receipt Storage Service

This module provides storage and retrieval services for receipt data,
including file management, database operations, and search capabilities.
"""

import asyncio
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..models.receipt import Receipt, ReceiptStatus, ReceiptType


class ReceiptStorageService:
    """Service for managing receipt storage and retrieval."""

    def __init__(self, storage_root: Union[str, Path] = "storage/processed_data/receipts"):
        """
        Initialize the storage service.

        Args:
            storage_root: Root directory for receipt storage
        """
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.receipts_dir = self.storage_root / "receipts"
        self.images_dir = self.storage_root / "images"
        self.exports_dir = self.storage_root / "exports"
        self.backups_dir = self.storage_root / "backups"

        for directory in [self.receipts_dir, self.images_dir, self.exports_dir, self.backups_dir]:
            directory.mkdir(exist_ok=True)

        # Initialize index file for fast searching
        self.index_file = self.storage_root / "receipt_index.json"
        self._load_index()

    def _load_index(self) -> None:
        """Load the receipt index from file."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception:
                self.index = {}
        else:
            self.index = {}

    def _save_index(self) -> None:
        """Save the receipt index to file."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to save index: {e}")

    def _get_receipt_file_path(self, receipt: Receipt) -> Path:
        """Generate file path for a receipt."""
        # Organize by year/month for better file management
        year = receipt.date.year
        month = receipt.date.month

        date_dir = self.receipts_dir / str(year) / f"{month:02d}"
        date_dir.mkdir(parents=True, exist_ok=True)

        # Create filename
        date_str = receipt.date.strftime('%Y%m%d')
        vendor_slug = self._create_vendor_slug(receipt.vendor.name)
        filename = f"{date_str}_{vendor_slug}_{receipt.receipt_id[:8]}.json"

        return date_dir / filename

    def _create_vendor_slug(self, vendor_name: str) -> str:
        """Create a safe filename slug from vendor name."""
        import re
        # Remove special characters and spaces
        slug = re.sub(r'[^\w\s-]', '', vendor_name.lower())
        slug = re.sub(r'[-\s]+', '_', slug)
        return slug[:20]  # Limit length

    async def store_receipt(self, receipt: Receipt, image_data: Optional[bytes] = None) -> Path:
        """
        Store a receipt with optional image data.

        Args:
            receipt: Receipt object to store
            image_data: Optional image data

        Returns:
            Path where receipt was stored
        """
        # Get file path
        file_path = self._get_receipt_file_path(receipt)

        # Store receipt data
        receipt_data = receipt.to_dict()
        with open(file_path, 'w') as f:
            json.dump(receipt_data, f, indent=2, default=str)

        # Store image if provided
        image_path = None
        if image_data:
            image_path = await self._store_image(receipt, image_data)
            receipt_data['image_path'] = str(image_path)

        # Update index
        self._update_index(receipt, file_path, image_path)

        return file_path

    async def _store_image(self, receipt: Receipt, image_data: bytes) -> Path:
        """Store receipt image data."""
        # Create image directory structure
        year = receipt.date.year
        month = receipt.date.month
        image_dir = self.images_dir / str(year) / f"{month:02d}"
        image_dir.mkdir(parents=True, exist_ok=True)

        # Determine file extension (default to jpg)
        extension = "jpg"
        if receipt.metadata and receipt.metadata.file_type:
            if "png" in receipt.metadata.file_type.lower():
                extension = "png"
            elif "pdf" in receipt.metadata.file_type.lower():
                extension = "pdf"

        # Create filename
        date_str = receipt.date.strftime('%Y%m%d')
        vendor_slug = self._create_vendor_slug(receipt.vendor.name)
        filename = f"{date_str}_{vendor_slug}_{receipt.receipt_id[:8]}.{extension}"

        image_path = image_dir / filename

        # Write image data
        with open(image_path, 'wb') as f:
            f.write(image_data)

        return image_path

    def _update_index(self, receipt: Receipt, file_path: Path, image_path: Optional[Path] = None) -> None:
        """Update the search index with receipt information."""
        index_entry = {
            'receipt_id': receipt.receipt_id,
            'vendor_name': receipt.vendor.name,
            'date': receipt.date.isoformat(),
            'total_amount': float(receipt.total_amount),
            'receipt_type': receipt.receipt_type.value,
            'status': receipt.status.value,
            'file_path': str(file_path),
            'image_path': str(image_path) if image_path else None,
            'created_at': receipt.created_at.isoformat(),
            'updated_at': receipt.updated_at.isoformat()
        }

        self.index[receipt.receipt_id] = index_entry
        self._save_index()

    async def get_receipt(self, receipt_id: str) -> Optional[Receipt]:
        """
        Retrieve a receipt by ID.

        Args:
            receipt_id: Receipt ID

        Returns:
            Receipt object or None if not found
        """
        if receipt_id not in self.index:
            return None

        file_path = Path(self.index[receipt_id]['file_path'])
        if not file_path.exists():
            # Remove from index if file doesn't exist
            del self.index[receipt_id]
            self._save_index()
            return None

        try:
            with open(file_path, 'r') as f:
                receipt_data = json.load(f)
            return Receipt.from_dict(receipt_data)
        except Exception as e:
            print(f"Failed to load receipt {receipt_id}: {e}")
            return None

    async def search_receipts(
        self,
        vendor_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        receipt_type: Optional[ReceiptType] = None,
        status: Optional[ReceiptStatus] = None,
        limit: Optional[int] = None
    ) -> List[Receipt]:
        """
        Search receipts with various filters.

        Args:
            vendor_name: Filter by vendor name (partial match)
            date_from: Filter by date range start
            date_to: Filter by date range end
            min_amount: Minimum total amount
            max_amount: Maximum total amount
            receipt_type: Filter by receipt type
            status: Filter by receipt status
            limit: Maximum number of results

        Returns:
            List of matching receipts
        """
        matching_receipts = []

        for receipt_id, entry in self.index.items():
            # Apply filters
            if vendor_name and vendor_name.lower() not in entry['vendor_name'].lower():
                continue

            if date_from:
                receipt_date = datetime.fromisoformat(entry['date'])
                if receipt_date < date_from:
                    continue

            if date_to:
                receipt_date = datetime.fromisoformat(entry['date'])
                if receipt_date > date_to:
                    continue

            if min_amount and entry['total_amount'] < min_amount:
                continue

            if max_amount and entry['total_amount'] > max_amount:
                continue

            if receipt_type and entry['receipt_type'] != receipt_type.value:
                continue

            if status and entry['status'] != status.value:
                continue

            # Load the full receipt
            receipt = await self.get_receipt(receipt_id)
            if receipt:
                matching_receipts.append(receipt)

            # Check limit
            if limit and len(matching_receipts) >= limit:
                break

        # Sort by date (most recent first)
        matching_receipts.sort(key=lambda r: r.date, reverse=True)

        return matching_receipts

    async def get_receipts_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Receipt]:
        """Get all receipts within a date range."""
        return await self.search_receipts(date_from=start_date, date_to=end_date)

    async def get_receipts_by_vendor(self, vendor_name: str) -> List[Receipt]:
        """Get all receipts for a specific vendor."""
        return await self.search_receipts(vendor_name=vendor_name)

    async def update_receipt(self, receipt: Receipt) -> bool:
        """
        Update an existing receipt.

        Args:
            receipt: Updated receipt object

        Returns:
            True if update successful, False otherwise
        """
        if receipt.receipt_id not in self.index:
            return False

        try:
            # Update the receipt file
            file_path = Path(self.index[receipt.receipt_id]['file_path'])
            receipt.updated_at = datetime.utcnow()

            with open(file_path, 'w') as f:
                json.dump(receipt.to_dict(), f, indent=2, default=str)

            # Update index
            self._update_index(receipt, file_path)

            return True

        except Exception as e:
            print(f"Failed to update receipt {receipt.receipt_id}: {e}")
            return False

    async def delete_receipt(self, receipt_id: str, delete_image: bool = True) -> bool:
        """
        Delete a receipt and optionally its image.

        Args:
            receipt_id: Receipt ID to delete
            delete_image: Whether to delete associated image

        Returns:
            True if deletion successful, False otherwise
        """
        if receipt_id not in self.index:
            return False

        try:
            entry = self.index[receipt_id]

            # Delete receipt file
            file_path = Path(entry['file_path'])
            if file_path.exists():
                file_path.unlink()

            # Delete image if requested
            if delete_image and entry.get('image_path'):
                image_path = Path(entry['image_path'])
                if image_path.exists():
                    image_path.unlink()

            # Remove from index
            del self.index[receipt_id]
            self._save_index()

            return True

        except Exception as e:
            print(f"Failed to delete receipt {receipt_id}: {e}")
            return False

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_receipts = len(self.index)
        total_size = 0
        image_count = 0

        # Calculate storage size
        for entry in self.index.values():
            file_path = Path(entry['file_path'])
            if file_path.exists():
                total_size += file_path.stat().st_size

            if entry.get('image_path'):
                image_path = Path(entry['image_path'])
                if image_path.exists():
                    total_size += image_path.stat().st_size
                    image_count += 1

        # Get date range
        dates = [datetime.fromisoformat(entry['date']) for entry in self.index.values()]
        date_range = {
            'earliest': min(dates).date() if dates else None,
            'latest': max(dates).date() if dates else None
        }

        # Get vendor statistics
        vendors = {}
        receipt_types = {}
        for entry in self.index.values():
            vendor = entry['vendor_name']
            vendors[vendor] = vendors.get(vendor, 0) + 1

            receipt_type = entry['receipt_type']
            receipt_types[receipt_type] = receipt_types.get(receipt_type, 0) + 1

        return {
            'total_receipts': total_receipts,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'image_count': image_count,
            'date_range': date_range,
            'top_vendors': sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:10],
            'receipt_types': receipt_types,
            'storage_path': str(self.storage_root)
        }

    async def export_receipts(
        self,
        format: str = "json",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        output_file: Optional[Path] = None
    ) -> Path:
        """
        Export receipts to a file.

        Args:
            format: Export format ("json", "csv")
            date_from: Start date for export
            date_to: End date for export
            output_file: Output file path

        Returns:
            Path to exported file
        """
        # Get receipts to export
        receipts = await self.search_receipts(date_from=date_from, date_to=date_to)

        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"receipts_export_{timestamp}.{format}"
            output_file = self.exports_dir / filename

        # Export based on format
        if format.lower() == "json":
            await self._export_json(receipts, output_file)
        elif format.lower() == "csv":
            await self._export_csv(receipts, output_file)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        return output_file

    async def _export_json(self, receipts: List[Receipt], output_file: Path) -> None:
        """Export receipts to JSON format."""
        receipts_data = [receipt.to_dict() for receipt in receipts]

        with open(output_file, 'w') as f:
            json.dump({
                'exported_at': datetime.utcnow().isoformat(),
                'total_receipts': len(receipts),
                'receipts': receipts_data
            }, f, indent=2, default=str)

    async def _export_csv(self, receipts: List[Receipt], output_file: Path) -> None:
        """Export receipts to CSV format."""
        import csv

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                'Receipt ID', 'Date', 'Vendor', 'Total Amount', 'Tax Amount',
                'Receipt Type', 'Payment Method', 'Status', 'Line Items Count'
            ])

            # Write data
            for receipt in receipts:
                writer.writerow([
                    receipt.receipt_id,
                    receipt.date.strftime('%Y-%m-%d'),
                    receipt.vendor.name,
                    float(receipt.total_amount),
                    float(receipt.tax_amount),
                    receipt.receipt_type.value,
                    receipt.payment_method.value,
                    receipt.status.value,
                    len(receipt.line_items)
                ])

    async def backup_storage(self, backup_name: Optional[str] = None) -> Path:
        """
        Create a backup of all receipt data.

        Args:
            backup_name: Optional backup name

        Returns:
            Path to backup file
        """
        if not backup_name:
            backup_name = f"receipt_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = self.backups_dir / f"{backup_name}.tar.gz"

        # Create tar.gz archive
        import tarfile

        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(self.receipts_dir, arcname="receipts")
            tar.add(self.images_dir, arcname="images")
            tar.add(self.index_file, arcname="receipt_index.json")

        return backup_path

    async def cleanup_old_receipts(self, days_old: int = 365) -> int:
        """
        Clean up receipts older than specified days.

        Args:
            days_old: Number of days after which to clean up

        Returns:
            Number of receipts cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0

        receipts_to_delete = []
        for receipt_id, entry in self.index.items():
            receipt_date = datetime.fromisoformat(entry['date'])
            if receipt_date < cutoff_date:
                receipts_to_delete.append(receipt_id)

        for receipt_id in receipts_to_delete:
            if await self.delete_receipt(receipt_id):
                cleaned_count += 1

        return cleaned_count