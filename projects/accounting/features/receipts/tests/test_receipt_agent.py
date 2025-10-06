"""
Tests for Receipt Agent and related components.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil

# Import the components to test
from core.agents.base import AgentConfig, AgentCapability
from ..models.receipt import (
    Receipt,
    ReceiptLineItem,
    ReceiptVendor,
    ReceiptType,
    PaymentMethod,
    ReceiptStatus,
    ReceiptProcessingRequest,
    ReceiptProcessingResult
)
from ..functions.processing import (
    ReceiptValidator,
    ReceiptEnhancer,
    ReceiptParser,
    process_receipt_batch
)
from ..services.storage import ReceiptStorageService
from ...agents.receipt_agent import ReceiptAgent


@pytest.fixture
def sample_receipt():
    """Create a sample receipt for testing."""
    vendor = ReceiptVendor(
        name="Test Store",
        address="123 Main St, Test City, TC 12345",
        phone="555-123-4567"
    )

    line_items = [
        ReceiptLineItem(
            description="Test Item 1",
            quantity=2.0,
            unit_price=Decimal('5.99'),
            total_price=Decimal('11.98')
        ),
        ReceiptLineItem(
            description="Test Item 2",
            quantity=1.0,
            unit_price=Decimal('3.50'),
            total_price=Decimal('3.50')
        )
    ]

    return Receipt(
        vendor=vendor,
        date=datetime.now().replace(hour=12, minute=30, second=0, microsecond=0),
        subtotal=Decimal('15.48'),
        tax_amount=Decimal('1.24'),
        total_amount=Decimal('16.72'),
        payment_method=PaymentMethod.CREDIT_CARD,
        receipt_type=ReceiptType.GROCERY,
        line_items=line_items,
        status=ReceiptStatus.PROCESSED,
        confidence_score=0.95
    )


@pytest.fixture
def agent_config():
    """Create agent configuration for testing."""
    return AgentConfig(
        name="TestReceiptAgent",
        description="Test receipt processing agent",
        capabilities=[
            AgentCapability.TEXT_PROCESSING,
            AgentCapability.IMAGE_ANALYSIS,
            AgentCapability.DOCUMENT_PARSING,
            AgentCapability.DATA_EXTRACTION
        ],
        max_turns=5,
        timeout_seconds=30
    )


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestReceiptModels:
    """Test receipt data models."""

    def test_receipt_creation(self, sample_receipt):
        """Test creating a receipt object."""
        assert sample_receipt.vendor.name == "Test Store"
        assert sample_receipt.total_amount == Decimal('16.72')
        assert len(sample_receipt.line_items) == 2
        assert sample_receipt.confidence_score == 0.95

    def test_receipt_validation(self, sample_receipt):
        """Test receipt validation."""
        assert sample_receipt.validate_totals() is True

    def test_receipt_calculate_totals(self, sample_receipt):
        """Test total calculation."""
        sample_receipt.calculate_totals()
        expected_subtotal = Decimal('11.98') + Decimal('3.50')
        assert sample_receipt.subtotal == expected_subtotal

    def test_receipt_serialization(self, sample_receipt):
        """Test receipt to/from dict conversion."""
        receipt_dict = sample_receipt.to_dict()
        assert isinstance(receipt_dict, dict)
        assert 'vendor' in receipt_dict
        assert 'total_amount' in receipt_dict

        # Test deserialization
        recreated_receipt = Receipt.from_dict(receipt_dict)
        assert recreated_receipt.vendor.name == sample_receipt.vendor.name
        assert recreated_receipt.total_amount == sample_receipt.total_amount

    def test_line_item_validation(self):
        """Test line item validation."""
        # Valid line item
        item = ReceiptLineItem(
            description="Valid Item",
            quantity=2.0,
            unit_price=Decimal('5.00'),
            total_price=Decimal('10.00')
        )
        assert item.quantity == 2.0
        assert item.total_price == Decimal('10.00')

        # Invalid quantity
        with pytest.raises(ValueError):
            ReceiptLineItem(
                description="Invalid Item",
                quantity=-1.0,
                total_price=Decimal('10.00')
            )

    def test_receipt_processing_request(self):
        """Test receipt processing request model."""
        request = ReceiptProcessingRequest(
            file_path="test_receipt.jpg",
            extract_line_items=True,
            categorize_items=True,
            validate_totals=True
        )

        assert request.file_path == "test_receipt.jpg"
        assert request.extract_line_items is True
        assert request.validate_totals is True


class TestReceiptValidator:
    """Test receipt validation functions."""

    def test_validate_amounts(self, sample_receipt):
        """Test amount validation."""
        errors = ReceiptValidator.validate_amounts(sample_receipt)
        assert len(errors) == 0

        # Test negative amounts
        sample_receipt.total_amount = Decimal('-10.00')
        errors = ReceiptValidator.validate_amounts(sample_receipt)
        assert len(errors) > 0
        assert any("must be positive" in error for error in errors)

    def test_validate_totals(self, sample_receipt):
        """Test total validation."""
        errors = ReceiptValidator.validate_totals(sample_receipt)
        assert len(errors) == 0

        # Create invalid totals
        sample_receipt.total_amount = Decimal('100.00')  # Wrong total
        errors = ReceiptValidator.validate_totals(sample_receipt)
        assert len(errors) > 0
        assert any("mismatch" in error for error in errors)

    def test_validate_vendor_info(self, sample_receipt):
        """Test vendor information validation."""
        warnings = ReceiptValidator.validate_vendor_info(sample_receipt)
        assert len(warnings) == 0

        # Test missing vendor name
        sample_receipt.vendor.name = ""
        warnings = ReceiptValidator.validate_vendor_info(sample_receipt)
        assert len(warnings) > 0
        assert any("name is missing" in warning for warning in warnings)

    def test_validate_date(self, sample_receipt):
        """Test date validation."""
        errors = ReceiptValidator.validate_date(sample_receipt)
        assert len(errors) == 0

        # Test future date
        sample_receipt.date = datetime.now() + timedelta(days=10)
        errors = ReceiptValidator.validate_date(sample_receipt)
        assert len(errors) > 0
        assert any("future" in error for error in errors)


class TestReceiptEnhancer:
    """Test receipt enhancement functions."""

    def test_enhance_receipt_type(self, sample_receipt):
        """Test automatic receipt type detection."""
        # Test grocery store
        sample_receipt.vendor.name = "Walmart Supercenter"
        enhanced = ReceiptEnhancer.enhance_receipt_type(sample_receipt)
        assert enhanced.receipt_type == ReceiptType.GROCERY

        # Test restaurant
        sample_receipt.vendor.name = "McDonald's Restaurant"
        enhanced = ReceiptEnhancer.enhance_receipt_type(sample_receipt)
        assert enhanced.receipt_type == ReceiptType.RESTAURANT

    def test_categorize_line_items(self, sample_receipt):
        """Test automatic line item categorization."""
        # Add items with recognizable descriptions
        sample_receipt.line_items = [
            ReceiptLineItem(description="Bread", total_price=Decimal('2.99')),
            ReceiptLineItem(description="Coca Cola", total_price=Decimal('1.99')),
            ReceiptLineItem(description="Shampoo", total_price=Decimal('5.99'))
        ]

        enhanced = ReceiptEnhancer.categorize_line_items(sample_receipt)

        categories = [item.category for item in enhanced.line_items]
        assert "Food" in categories
        assert "Beverages" in categories
        assert "Personal Care" in categories

    def test_standardize_vendor_name(self):
        """Test vendor name standardization."""
        assert ReceiptEnhancer.standardize_vendor_name("walmart supercenter") == "Walmart"
        assert ReceiptEnhancer.standardize_vendor_name("MCDONALD'S") == "McDonald's"
        assert ReceiptEnhancer.standardize_vendor_name("random store") == "Random Store"


class TestReceiptParser:
    """Test receipt parsing utilities."""

    def test_parse_amount(self):
        """Test amount parsing."""
        assert ReceiptParser.parse_amount("$12.34") == Decimal('12.34')
        assert ReceiptParser.parse_amount("12,34") == Decimal('1234')  # Removes comma
        assert ReceiptParser.parse_amount("-$5.99") == Decimal('-5.99')
        assert ReceiptParser.parse_amount("invalid") is None

    def test_parse_date(self):
        """Test date parsing."""
        date1 = ReceiptParser.parse_date("2024-01-15")
        assert date1.year == 2024
        assert date1.month == 1
        assert date1.day == 15

        date2 = ReceiptParser.parse_date("01/15/2024")
        assert date2.year == 2024

        date3 = ReceiptParser.parse_date("January 15, 2024")
        assert date3.year == 2024

        assert ReceiptParser.parse_date("invalid date") is None

    def test_parse_time(self):
        """Test time parsing."""
        assert ReceiptParser.parse_time("14:30:25") == "14:30:25"
        assert ReceiptParser.parse_time("2:30 PM") == "2:30 PM"
        assert ReceiptParser.parse_time("invalid time") is None

    def test_extract_card_info(self):
        """Test card information extraction."""
        assert ReceiptParser.extract_card_info("Card ending in 1234") == "1234"
        assert ReceiptParser.extract_card_info("****1234") == "1234"
        assert ReceiptParser.extract_card_info("XXXX5678") == "5678"
        assert ReceiptParser.extract_card_info("no card info") is None


class TestReceiptStorageService:
    """Test receipt storage service."""

    @pytest.fixture
    def storage_service(self, temp_storage_dir):
        """Create storage service with temporary directory."""
        return ReceiptStorageService(temp_storage_dir)

    @pytest.mark.asyncio
    async def test_store_and_retrieve_receipt(self, storage_service, sample_receipt):
        """Test storing and retrieving a receipt."""
        # Store receipt
        file_path = await storage_service.store_receipt(sample_receipt)
        assert file_path.exists()

        # Retrieve receipt
        retrieved = await storage_service.get_receipt(sample_receipt.receipt_id)
        assert retrieved is not None
        assert retrieved.vendor.name == sample_receipt.vendor.name
        assert retrieved.total_amount == sample_receipt.total_amount

    @pytest.mark.asyncio
    async def test_search_receipts(self, storage_service, sample_receipt):
        """Test receipt search functionality."""
        # Store receipt
        await storage_service.store_receipt(sample_receipt)

        # Search by vendor
        results = await storage_service.search_receipts(vendor_name="Test Store")
        assert len(results) == 1
        assert results[0].vendor.name == "Test Store"

        # Search by amount range
        results = await storage_service.search_receipts(min_amount=10.0, max_amount=20.0)
        assert len(results) == 1

        # Search by receipt type
        results = await storage_service.search_receipts(receipt_type=ReceiptType.GROCERY)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_update_receipt(self, storage_service, sample_receipt):
        """Test receipt updates."""
        # Store original receipt
        await storage_service.store_receipt(sample_receipt)

        # Update receipt
        sample_receipt.vendor.name = "Updated Store Name"
        success = await storage_service.update_receipt(sample_receipt)
        assert success is True

        # Verify update
        retrieved = await storage_service.get_receipt(sample_receipt.receipt_id)
        assert retrieved.vendor.name == "Updated Store Name"

    @pytest.mark.asyncio
    async def test_delete_receipt(self, storage_service, sample_receipt):
        """Test receipt deletion."""
        # Store receipt
        await storage_service.store_receipt(sample_receipt)

        # Verify it exists
        retrieved = await storage_service.get_receipt(sample_receipt.receipt_id)
        assert retrieved is not None

        # Delete receipt
        success = await storage_service.delete_receipt(sample_receipt.receipt_id)
        assert success is True

        # Verify deletion
        retrieved = await storage_service.get_receipt(sample_receipt.receipt_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_storage_stats(self, storage_service, sample_receipt):
        """Test storage statistics."""
        # Store receipt
        await storage_service.store_receipt(sample_receipt)

        # Get stats
        stats = await storage_service.get_storage_stats()
        assert stats['total_receipts'] == 1
        assert 'total_size_bytes' in stats
        assert 'top_vendors' in stats


class TestReceiptAgent:
    """Test Receipt Agent functionality."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create mock Anthropic client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '''```json
{
  "vendor": {
    "name": "Test Store",
    "address": "123 Main St"
  },
  "transaction": {
    "date": "2024-01-15",
    "receipt_number": "12345"
  },
  "financial": {
    "line_items": [
      {
        "description": "Test Item",
        "quantity": 1.0,
        "total_price": 10.00
      }
    ],
    "subtotal": 10.00,
    "tax_amount": 0.80,
    "total_amount": 10.80
  },
  "payment": {
    "method": "credit_card"
  },
  "classification": {
    "receipt_type": "retail"
  },
  "confidence": {
    "overall": 0.90
  }
}
```'''
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client.messages.create.return_value = mock_response
        return mock_client

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent_config, temp_storage_dir):
        """Test agent initialization."""
        # Patch the storage path
        with patch('projects.accounting.agents.receipt_agent.Path') as mock_path:
            mock_path.return_value.mkdir = MagicMock()
            mock_path.return_value.__truediv__ = lambda self, other: mock_path.return_value

            agent = ReceiptAgent(agent_config)
            await agent.initialize()

            assert agent.is_initialized
            assert agent.processed_receipts == 0

    @pytest.mark.asyncio
    async def test_process_receipt_with_file_data(self, agent_config, mock_anthropic_client):
        """Test processing receipt with file data."""
        # Create mock image data
        mock_image_data = b"fake image data"

        with patch('projects.accounting.agents.receipt_agent.Path'), \
             patch('projects.accounting.agents.receipt_agent.FileBackend'), \
             patch('projects.accounting.agents.receipt_agent.AgentMemory'):

            agent = ReceiptAgent(agent_config, mock_anthropic_client)
            await agent.initialize()

            # Mock image processing
            with patch.object(agent, '_prepare_image_data') as mock_prepare:
                mock_prepare.return_value = {
                    'image_data': 'base64_encoded_data',
                    'mime_type': 'image/jpeg',
                    'filename': 'test.jpg',
                    'file_size': 1024,
                    'dimensions': (800, 600)
                }

                result = await agent.execute({
                    'file_data': mock_image_data,
                    'file_name': 'test_receipt.jpg',
                    'extract_line_items': True,
                    'validate_totals': True
                })

                assert result['success'] is True
                assert result['receipt'] is not None
                assert 'agent_stats' in result

    @pytest.mark.asyncio
    async def test_claude_response_parsing(self, agent_config):
        """Test parsing Claude API responses."""
        agent = ReceiptAgent(agent_config)

        # Test valid JSON response
        valid_response = '''Here's the extracted data:
```json
{
  "vendor": {"name": "Test Store"},
  "financial": {"total_amount": 15.99}
}
```
'''
        parsed = agent._parse_claude_response(valid_response)
        assert parsed['vendor']['name'] == "Test Store"
        assert parsed['financial']['total_amount'] == 15.99

        # Test invalid response
        invalid_response = "No JSON here"
        parsed = agent._parse_claude_response(invalid_response)
        assert 'parse_error' in parsed

    @pytest.mark.asyncio
    async def test_receipt_creation_from_extraction(self, agent_config):
        """Test creating receipt from extraction data."""
        agent = ReceiptAgent(agent_config)

        extraction_data = {
            'vendor': {'name': 'Test Vendor', 'address': '123 Main St'},
            'transaction': {'date': '2024-01-15', 'receipt_number': '12345'},
            'financial': {
                'subtotal': 10.00,
                'tax_amount': 0.80,
                'total_amount': 10.80,
                'line_items': [
                    {
                        'description': 'Test Item',
                        'quantity': 1.0,
                        'total_price': 10.00
                    }
                ]
            },
            'payment': {'method': 'credit_card', 'card_last_four': '1234'},
            'classification': {'receipt_type': 'grocery'},
            'confidence': {'overall': 0.95}
        }

        request = ReceiptProcessingRequest()
        receipt = await agent._create_receipt_from_extraction(extraction_data, request)

        assert receipt.vendor.name == 'Test Vendor'
        assert receipt.total_amount == Decimal('10.80')
        assert receipt.payment_method == PaymentMethod.CREDIT_CARD
        assert receipt.card_last_four == '1234'
        assert len(receipt.line_items) == 1


# Integration tests
class TestReceiptProcessingIntegration:
    """Integration tests for receipt processing workflow."""

    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, temp_storage_dir):
        """Test complete receipt processing workflow."""
        # This would require actual image data and API access
        # For now, we'll test the workflow with mocked components
        pass

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test processing multiple receipts."""
        # Mock agent for batch processing
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = {
            'success': True,
            'receipt': {'receipt_id': 'test_id'}
        }

        # Create test files
        test_files = [Path(f"test_{i}.jpg") for i in range(3)]

        # Test batch processing
        results = await process_receipt_batch(test_files, mock_agent, max_concurrent=2)

        assert len(results) == 3
        assert all(result.get('success') for result in results)


if __name__ == "__main__":
    pytest.main([__file__])