"""
Receipt Processing API Client Examples

This module demonstrates how to use the Receipt Processing API
with various client libraries and use cases.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx
import requests
from dataclasses import dataclass


@dataclass
class APIConfig:
    """Configuration for API client."""
    base_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    jwt_token: Optional[str] = None
    timeout: int = 30


class ReceiptAPIClient:
    """
    Client for the Receipt Processing API.

    Provides high-level methods for interacting with the API endpoints.
    """

    def __init__(self, config: APIConfig):
        """Initialize the API client."""
        self.config = config
        self.session = requests.Session()

        # Set up authentication headers
        if config.api_key:
            self.session.headers.update({"X-API-Key": config.api_key})
        elif config.jwt_token:
            self.session.headers.update({"Authorization": f"Bearer {config.jwt_token}"})

        self.session.headers.update({"User-Agent": "LiMOS-Receipt-Client/1.0"})

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        response = self.session.get(f"{self.config.base_url}/health")
        response.raise_for_status()
        return response.json()

    def process_receipt(
        self,
        file_path: Path,
        extract_line_items: bool = True,
        categorize_items: bool = True,
        validate_totals: bool = True,
        business_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single receipt image.

        Args:
            file_path: Path to receipt image file
            extract_line_items: Whether to extract individual line items
            categorize_items: Whether to categorize line items
            validate_totals: Whether to validate mathematical totals
            business_context: Optional business context for categorization

        Returns:
            Processing result dictionary
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'rb') as f:
            files = {"file": (file_path.name, f, "image/jpeg")}
            data = {
                "extract_line_items": extract_line_items,
                "categorize_items": categorize_items,
                "validate_totals": validate_totals,
            }

            if business_context:
                data["business_context"] = business_context

            response = self.session.post(
                f"{self.config.base_url}/receipts/process",
                files=files,
                data=data,
                timeout=self.config.timeout
            )

        response.raise_for_status()
        return response.json()

    def get_receipt(self, receipt_id: str) -> Dict[str, Any]:
        """Get a receipt by ID."""
        response = self.session.get(f"{self.config.base_url}/receipts/{receipt_id}")
        response.raise_for_status()
        return response.json()

    def search_receipts(
        self,
        vendor_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        receipt_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search receipts with filters.

        Args:
            vendor_name: Filter by vendor name
            date_from: Start date for search
            date_to: End date for search
            min_amount: Minimum total amount
            max_amount: Maximum total amount
            receipt_type: Filter by receipt type
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            Search results dictionary
        """
        search_params = {
            "limit": limit,
            "offset": offset
        }

        if vendor_name:
            search_params["vendor_name"] = vendor_name
        if date_from:
            search_params["date_from"] = date_from.isoformat()
        if date_to:
            search_params["date_to"] = date_to.isoformat()
        if min_amount is not None:
            search_params["min_amount"] = min_amount
        if max_amount is not None:
            search_params["max_amount"] = max_amount
        if receipt_type:
            search_params["receipt_type"] = receipt_type

        response = self.session.post(
            f"{self.config.base_url}/receipts/search",
            json=search_params
        )
        response.raise_for_status()
        return response.json()

    def update_receipt(self, receipt_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a receipt."""
        response = self.session.put(
            f"{self.config.base_url}/receipts/{receipt_id}",
            json=updates
        )
        response.raise_for_status()
        return response.json()

    def delete_receipt(self, receipt_id: str, delete_image: bool = True) -> Dict[str, Any]:
        """Delete a receipt."""
        params = {"delete_image": delete_image}
        response = self.session.delete(
            f"{self.config.base_url}/receipts/{receipt_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def start_batch_processing(
        self,
        file_paths: List[Path],
        **processing_options
    ) -> Dict[str, Any]:
        """
        Start batch processing of multiple receipts.

        Args:
            file_paths: List of receipt image file paths
            **processing_options: Processing options (extract_line_items, etc.)

        Returns:
            Batch job information
        """
        files = []
        for file_path in file_paths:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            files.append(("files", (file_path.name, open(file_path, 'rb'), "image/jpeg")))

        try:
            response = self.session.post(
                f"{self.config.base_url}/batch/process",
                files=files,
                data=processing_options,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()

        finally:
            # Close file handles
            for _, (_, file_handle, _) in files:
                file_handle.close()

    def get_batch_status(self, job_id: str) -> Dict[str, Any]:
        """Get batch processing job status."""
        response = self.session.get(f"{self.config.base_url}/batch/jobs/{job_id}/status")
        response.raise_for_status()
        return response.json()

    def get_batch_results(self, job_id: str) -> Dict[str, Any]:
        """Get batch processing job results."""
        response = self.session.get(f"{self.config.base_url}/batch/jobs/{job_id}/results")
        response.raise_for_status()
        return response.json()

    def export_receipts(
        self,
        format: str = "json",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        **filters
    ) -> Dict[str, Any]:
        """
        Export receipts to file.

        Args:
            format: Export format ("json" or "csv")
            date_from: Start date for export
            date_to: End date for export
            **filters: Additional filters

        Returns:
            Export result information
        """
        export_params = {"format": format, **filters}

        if date_from:
            export_params["date_from"] = date_from.isoformat()
        if date_to:
            export_params["date_to"] = date_to.isoformat()

        response = self.session.post(
            f"{self.config.base_url}/receipts/export",
            json=export_params
        )
        response.raise_for_status()
        return response.json()

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        response = self.session.get(f"{self.config.base_url}/receipts/stats")
        response.raise_for_status()
        return response.json()


class AsyncReceiptAPIClient:
    """
    Async version of the Receipt Processing API client.

    Provides better performance for concurrent operations.
    """

    def __init__(self, config: APIConfig):
        """Initialize the async API client."""
        self.config = config
        self.headers = {}

        if config.api_key:
            self.headers["X-API-Key"] = config.api_key
        elif config.jwt_token:
            self.headers["Authorization"] = f"Bearer {config.jwt_token}"

        self.headers["User-Agent"] = "LiMOS-Receipt-Client-Async/1.0"

    async def process_receipt(self, file_path: Path, **options) -> Dict[str, Any]:
        """Process a single receipt asynchronously."""
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                files = {"file": (file_path.name, f, "image/jpeg")}

                response = await client.post(
                    f"{self.config.base_url}/receipts/process",
                    files=files,
                    data=options,
                    headers=self.headers,
                    timeout=self.config.timeout
                )

            response.raise_for_status()
            return response.json()

    async def process_multiple_receipts(
        self,
        file_paths: List[Path],
        max_concurrent: int = 3,
        **options
    ) -> List[Dict[str, Any]]:
        """Process multiple receipts concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single(file_path: Path):
            async with semaphore:
                try:
                    return await self.process_receipt(file_path, **options)
                except Exception as e:
                    return {"error": str(e), "file_path": str(file_path)}

        tasks = [process_single(fp) for fp in file_paths]
        return await asyncio.gather(*tasks)


def example_single_receipt_processing():
    """Example: Process a single receipt."""
    print("=== Single Receipt Processing Example ===")

    # Initialize client
    config = APIConfig(base_url="http://localhost:8000")
    client = ReceiptAPIClient(config)

    # Check API health
    try:
        health = client.health_check()
        print(f"API Status: {health['status']}")
    except Exception as e:
        print(f"API not available: {e}")
        return

    # Process a receipt (you'd need an actual image file)
    receipt_file = Path("sample_receipt.jpg")
    if receipt_file.exists():
        try:
            result = client.process_receipt(
                receipt_file,
                extract_line_items=True,
                categorize_items=True,
                business_context="Personal grocery shopping"
            )

            if result["success"]:
                receipt = result["receipt"]
                print(f"Receipt processed successfully!")
                print(f"Vendor: {receipt['vendor']['name']}")
                print(f"Total: ${receipt['total_amount']}")
                print(f"Line items: {len(receipt['line_items'])}")
                print(f"Confidence: {receipt['confidence_score']:.2%}")

                # Store receipt ID for later operations
                receipt_id = receipt["receipt_id"]
                print(f"Receipt ID: {receipt_id}")

            else:
                print(f"Processing failed: {result.get('error_message')}")

        except Exception as e:
            print(f"Error processing receipt: {e}")
    else:
        print("Sample receipt file not found")


def example_batch_processing():
    """Example: Process multiple receipts in batch."""
    print("\n=== Batch Processing Example ===")

    config = APIConfig(base_url="http://localhost:8000")
    client = ReceiptAPIClient(config)

    # Collect receipt files
    receipt_files = list(Path(".").glob("*.jpg"))[:5]  # Limit to 5 files

    if not receipt_files:
        print("No receipt files found for batch processing")
        return

    try:
        # Start batch processing
        batch_result = client.start_batch_processing(
            receipt_files,
            extract_line_items=True,
            max_concurrent=3
        )

        job_id = batch_result["job_id"]
        print(f"Batch job started: {job_id}")
        print(f"Total files: {batch_result['total_files']}")

        # Monitor progress
        while True:
            status = client.get_batch_status(job_id)
            print(f"Progress: {status['progress_percentage']:.1f}% "
                  f"({status['processed_files']}/{status['total_files']})")

            if status["status"] in ["completed", "failed"]:
                break

            time.sleep(2)

        # Get results
        if status["status"] == "completed":
            results = client.get_batch_results(job_id)
            print(f"Batch completed successfully!")
            print(f"Success rate: {results['summary']['success_rate']:.1f}%")
            print(f"Average processing time: {results['summary']['avg_processing_time']:.2f}s")

    except Exception as e:
        print(f"Batch processing error: {e}")


def example_search_and_analytics():
    """Example: Search receipts and generate analytics."""
    print("\n=== Search and Analytics Example ===")

    config = APIConfig(base_url="http://localhost:8000")
    client = ReceiptAPIClient(config)

    try:
        # Search for grocery receipts from last month
        date_from = datetime.now() - timedelta(days=30)

        search_results = client.search_receipts(
            receipt_type="grocery",
            date_from=date_from,
            limit=100
        )

        receipts = search_results["receipts"]
        print(f"Found {len(receipts)} grocery receipts from last month")

        if receipts:
            # Calculate analytics
            total_spent = sum(r["total_amount"] for r in receipts)
            avg_amount = total_spent / len(receipts)
            vendors = {}

            for receipt in receipts:
                vendor = receipt["vendor_name"]
                vendors[vendor] = vendors.get(vendor, 0) + receipt["total_amount"]

            print(f"Total spent: ${total_spent:.2f}")
            print(f"Average per receipt: ${avg_amount:.2f}")
            print("Top vendors:")
            for vendor, amount in sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {vendor}: ${amount:.2f}")

        # Get storage statistics
        stats = client.get_storage_stats()
        print(f"\nStorage Statistics:")
        print(f"Total receipts: {stats['total_receipts']}")
        print(f"Storage size: {stats['total_size_mb']:.1f} MB")

    except Exception as e:
        print(f"Search/analytics error: {e}")


def example_receipt_management():
    """Example: Manage receipt data (CRUD operations)."""
    print("\n=== Receipt Management Example ===")

    config = APIConfig(base_url="http://localhost:8000")
    client = ReceiptAPIClient(config)

    # This example assumes you have a receipt ID from previous processing
    # In practice, you'd get this from search results or processing
    receipt_id = "sample_receipt_id"

    try:
        # Get receipt details
        receipt = client.get_receipt(receipt_id)
        print(f"Retrieved receipt: {receipt['vendor']['name']}")

        # Update receipt information
        updates = {
            "notes": "Business lunch with client",
            "is_business_expense": True,
            "category": "Business Meals"
        }

        updated_receipt = client.update_receipt(receipt_id, updates)
        print(f"Updated receipt notes: {updated_receipt['notes']}")

        # Delete receipt (commented out to avoid accidental deletion)
        # client.delete_receipt(receipt_id)
        # print("Receipt deleted")

    except Exception as e:
        print(f"Receipt management error: {e}")


async def example_async_processing():
    """Example: Async processing for better performance."""
    print("\n=== Async Processing Example ===")

    config = APIConfig(base_url="http://localhost:8000")
    client = AsyncReceiptAPIClient(config)

    # Process multiple receipts concurrently
    receipt_files = list(Path(".").glob("*.jpg"))[:3]

    if receipt_files:
        try:
            results = await client.process_multiple_receipts(
                receipt_files,
                max_concurrent=2,
                extract_line_items=True
            )

            successful = [r for r in results if "error" not in r]
            failed = [r for r in results if "error" in r]

            print(f"Processed {len(successful)} receipts successfully")
            print(f"Failed to process {len(failed)} receipts")

        except Exception as e:
            print(f"Async processing error: {e}")
    else:
        print("No receipt files found for async processing")


def example_export_data():
    """Example: Export receipt data."""
    print("\n=== Data Export Example ===")

    config = APIConfig(base_url="http://localhost:8000")
    client = ReceiptAPIClient(config)

    try:
        # Export all receipts from last quarter to JSON
        date_from = datetime.now() - timedelta(days=90)

        export_result = client.export_receipts(
            format="json",
            date_from=date_from,
            include_line_items=True
        )

        if export_result["success"]:
            print(f"Export successful!")
            print(f"File: {export_result['file_path']}")
            print(f"Records: {export_result['record_count']}")
            print(f"Size: {export_result['file_size']} bytes")
        else:
            print(f"Export failed: {export_result['error_message']}")

    except Exception as e:
        print(f"Export error: {e}")


def main():
    """Run all examples."""
    print("Receipt Processing API Client Examples")
    print("=" * 50)

    # Run synchronous examples
    example_single_receipt_processing()
    example_batch_processing()
    example_search_and_analytics()
    example_receipt_management()
    example_export_data()

    # Run async example
    print("\nRunning async example...")
    asyncio.run(example_async_processing())

    print("\n✅ All examples completed!")
    print("\nTo use these examples:")
    print("1. Start the API server: uvicorn main:app --reload")
    print("2. Add your API key or JWT token to the config")
    print("3. Place some receipt images in the current directory")
    print("4. Run: python client_examples.py")


if __name__ == "__main__":
    main()