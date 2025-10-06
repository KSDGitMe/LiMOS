"""
Receipt Agent Demo Script

This script demonstrates the complete functionality of the Receipt Agent,
including processing receipt images, storing data, and performing queries.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from core.agents.base import AgentConfig, AgentCapability
from core.agents.base.config import config_manager
from projects.accounting.agents.receipt_agent import ReceiptAgent
from projects.accounting.features.receipts.services.storage import ReceiptStorageService
from projects.accounting.features.receipts.functions.processing import process_receipt_batch


async def create_receipt_agent() -> ReceiptAgent:
    """Create and initialize a Receipt Agent."""
    print("🤖 Creating Receipt Agent...")

    # Create agent configuration
    config = config_manager.create_agent_config(
        name="DemoReceiptAgent",
        description="Demo agent for processing receipt images",
        capabilities=[
            AgentCapability.TEXT_PROCESSING,
            AgentCapability.IMAGE_ANALYSIS,
            AgentCapability.DOCUMENT_PARSING,
            AgentCapability.DATA_EXTRACTION,
            AgentCapability.API_INTEGRATION,
            AgentCapability.FILE_OPERATIONS
        ],
        environment="development",
        max_turns=15,
        timeout_seconds=120
    )

    # Create and initialize agent
    agent = ReceiptAgent(config)
    await agent.initialize()

    print(f"✅ Receipt Agent '{agent.name}' initialized successfully")
    print(f"   Agent ID: {agent.agent_id}")
    print(f"   Status: {agent.status}")

    return agent


async def demo_single_receipt_processing(agent: ReceiptAgent) -> None:
    """Demo processing a single receipt."""
    print("\n📄 === Single Receipt Processing Demo ===")

    # For demo purposes, we'll simulate processing with sample data
    # In real usage, you would provide actual image files
    sample_processing_request = {
        "file_data": b"fake_image_data_for_demo",  # In real usage: actual image bytes
        "file_name": "sample_grocery_receipt.jpg",
        "extract_line_items": True,
        "categorize_items": True,
        "validate_totals": True,
        "business_context": "Personal grocery shopping"
    }

    print("Processing receipt image...")
    print(f"  File: {sample_processing_request['file_name']}")
    print(f"  Extract line items: {sample_processing_request['extract_line_items']}")
    print(f"  Categorize items: {sample_processing_request['categorize_items']}")

    try:
        # NOTE: This will fail without actual image data and Claude API key
        # In a real demo, you would provide actual receipt images
        result = await agent.execute(sample_processing_request)

        if result.get('success'):
            receipt = result['receipt']
            print("✅ Receipt processed successfully!")
            print(f"   Vendor: {receipt['vendor']['name']}")
            print(f"   Date: {receipt['date']}")
            print(f"   Total: ${receipt['total_amount']}")
            print(f"   Line items: {len(receipt['line_items'])}")
            print(f"   Confidence: {receipt['confidence_score']:.2%}")
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Demo processing failed (expected without real image data): {e}")
        print("💡 To run with real data, provide actual receipt images and Claude API key")


async def demo_storage_operations(agent: ReceiptAgent) -> None:
    """Demo storage and retrieval operations."""
    print("\n💾 === Storage Operations Demo ===")

    # Create storage service
    storage_service = ReceiptStorageService("demo_storage")

    # Create sample receipt data for demo
    from projects.accounting.features.receipts.models.receipt import (
        Receipt, ReceiptVendor, ReceiptLineItem, ReceiptType, PaymentMethod, ReceiptStatus
    )
    from decimal import Decimal

    sample_receipts = [
        Receipt(
            vendor=ReceiptVendor(name="Demo Grocery Store", address="123 Demo St"),
            date=datetime.now() - timedelta(days=1),
            subtotal=Decimal('45.67'),
            tax_amount=Decimal('3.65'),
            total_amount=Decimal('49.32'),
            payment_method=PaymentMethod.CREDIT_CARD,
            receipt_type=ReceiptType.GROCERY,
            line_items=[
                ReceiptLineItem(description="Bananas", total_price=Decimal('3.99')),
                ReceiptLineItem(description="Milk", total_price=Decimal('4.29')),
                ReceiptLineItem(description="Bread", total_price=Decimal('2.89'))
            ],
            status=ReceiptStatus.PROCESSED,
            confidence_score=0.92
        ),
        Receipt(
            vendor=ReceiptVendor(name="Demo Restaurant", address="456 Food Ave"),
            date=datetime.now() - timedelta(days=2),
            subtotal=Decimal('28.50'),
            tax_amount=Decimal('2.28'),
            tip_amount=Decimal('5.70'),
            total_amount=Decimal('36.48'),
            payment_method=PaymentMethod.CREDIT_CARD,
            receipt_type=ReceiptType.RESTAURANT,
            line_items=[
                ReceiptLineItem(description="Burger", total_price=Decimal('15.99')),
                ReceiptLineItem(description="Fries", total_price=Decimal('4.99')),
                ReceiptLineItem(description="Drink", total_price=Decimal('3.99'))
            ],
            status=ReceiptStatus.PROCESSED,
            confidence_score=0.88
        )
    ]

    # Store receipts
    print("Storing sample receipts...")
    stored_paths = []
    for i, receipt in enumerate(sample_receipts):
        file_path = await storage_service.store_receipt(receipt)
        stored_paths.append(file_path)
        print(f"  Receipt {i+1} stored: {file_path.name}")

    # Search operations
    print("\nPerforming search operations...")

    # Search by vendor
    grocery_receipts = await storage_service.search_receipts(vendor_name="Grocery")
    print(f"  Found {len(grocery_receipts)} grocery receipts")

    # Search by date range
    recent_receipts = await storage_service.search_receipts(
        date_from=datetime.now() - timedelta(days=7)
    )
    print(f"  Found {len(recent_receipts)} receipts from last 7 days")

    # Search by amount range
    expensive_receipts = await storage_service.search_receipts(min_amount=30.0)
    print(f"  Found {len(expensive_receipts)} receipts over $30")

    # Get storage statistics
    stats = await storage_service.get_storage_stats()
    print(f"\nStorage Statistics:")
    print(f"  Total receipts: {stats['total_receipts']}")
    print(f"  Storage size: {stats['total_size_mb']} MB")
    print(f"  Top vendors: {[vendor for vendor, count in stats['top_vendors'][:3]]}")

    # Export receipts
    print("\nExporting receipts...")
    export_path = await storage_service.export_receipts(format="json")
    print(f"  Exported to: {export_path}")

    # Cleanup demo storage
    print("\nCleaning up demo storage...")
    import shutil
    shutil.rmtree("demo_storage", ignore_errors=True)
    print("  Demo storage cleaned up")


async def demo_batch_processing(agent: ReceiptAgent) -> None:
    """Demo batch processing multiple receipts."""
    print("\n📦 === Batch Processing Demo ===")

    # Create some dummy file paths for demo
    # In real usage, these would be actual receipt image files
    demo_files = [
        Path(f"demo_receipt_{i}.jpg") for i in range(5)
    ]

    print(f"Simulating batch processing of {len(demo_files)} receipts...")
    print("Files to process:")
    for file_path in demo_files:
        print(f"  - {file_path}")

    try:
        # NOTE: This will fail without actual files
        # results = await process_receipt_batch(demo_files, agent, max_concurrent=3)
        print("💡 In real usage, this would process all files concurrently")
        print("   Each file would be analyzed and structured data extracted")
        print("   Results would include success/failure status for each file")
        print("   Failed processing would include error details for debugging")

    except Exception as e:
        print(f"❌ Batch processing demo failed (expected without real files): {e}")


async def demo_agent_statistics(agent: ReceiptAgent) -> None:
    """Demo agent statistics and monitoring."""
    print("\n📊 === Agent Statistics Demo ===")

    # Get comprehensive agent stats
    stats = await agent.get_receipt_stats()

    print("Agent Performance Metrics:")
    print(f"  Agent ID: {stats['agent_id']}")
    print(f"  Status: {stats['status']}")
    print(f"  Receipts processed: {stats['processed_receipts']}")
    print(f"  Initialization time: {stats.get('memory_stats', {}).get('created_at', 'N/A')}")

    # Get base agent stats
    base_stats = agent.get_status_info()
    print(f"\nAgent Configuration:")
    print(f"  Max turns: {base_stats['config']['max_turns']}")
    print(f"  Timeout: {base_stats['config']['timeout_seconds']}s")
    print(f"  Capabilities: {len(base_stats['config']['capabilities'])}")

    # Memory statistics
    if agent.memory:
        memory_stats = await agent.memory.get_stats()
        print(f"\nMemory Usage:")
        print(f"  Total entries: {memory_stats['total_entries']}")
        print(f"  Active entries: {memory_stats['active_entries']}")


async def demo_error_handling() -> None:
    """Demo error handling and recovery scenarios."""
    print("\n⚠️  === Error Handling Demo ===")

    print("Testing various error scenarios:")
    print("  1. Invalid image format")
    print("  2. Corrupted image data")
    print("  3. API timeout scenarios")
    print("  4. Storage failures")
    print("  5. Validation errors")

    print("💡 The Receipt Agent includes comprehensive error handling:")
    print("   - Graceful fallbacks for failed OCR")
    print("   - Retry logic for transient failures")
    print("   - Detailed error reporting")
    print("   - Automatic cleanup on failures")


async def main():
    """Main demo function."""
    print("🎯 Receipt Agent Comprehensive Demo")
    print("=" * 50)

    try:
        # Create and initialize agent
        agent = await create_receipt_agent()

        # Run demo sections
        await demo_single_receipt_processing(agent)
        await demo_storage_operations(agent)
        await demo_batch_processing(agent)
        await demo_agent_statistics(agent)
        await demo_error_handling()

        # Cleanup
        print("\n🧹 Cleaning up agent resources...")
        await agent.cleanup()
        print("✅ Agent cleanup completed")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\n💡 To run this demo successfully, you need:")
        print("   1. Valid Anthropic API key in environment")
        print("   2. Actual receipt image files")
        print("   3. Proper storage permissions")

    print("\n🎉 Demo completed!")
    print("\nNext steps:")
    print("   1. Add your Anthropic API key to system/config/.env")
    print("   2. Place receipt images in a test directory")
    print("   3. Run: python demo_receipt_agent.py")


if __name__ == "__main__":
    asyncio.run(main())