"""
Receipt Processing Agent

This module implements a specialized agent for processing receipts,
extracting structured data, and managing receipt workflows.
"""

import asyncio
import base64
import json
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from anthropic import Anthropic
from PIL import Image
import io

from core.agents.base import BaseAgent, AgentCapability, AgentConfig
from core.agents.memory import AgentMemory, FileBackend

from ..features.receipts.models.receipt import (
    Receipt,
    ReceiptProcessingRequest,
    ReceiptProcessingResult,
    ReceiptStatus,
    ReceiptType,
    PaymentMethod,
    ReceiptVendor,
    ReceiptLineItem,
    ReceiptTax,
    ReceiptMetadata
)


class ReceiptAgent(BaseAgent):
    """
    Specialized agent for processing receipt images and extracting structured data.

    This agent uses Claude's vision capabilities to analyze receipt images,
    extract key information, and create structured receipt records.
    """

    SYSTEM_PROMPT = """You are a specialized receipt processing agent. Your task is to analyze receipt images and extract structured data accurately.

Key responsibilities:
1. Extract merchant/vendor information (name, address, phone, etc.)
2. Identify transaction details (date, time, receipt number)
3. Extract all line items with descriptions, quantities, and prices
4. Calculate taxes, discounts, and totals
5. Determine payment method and card information
6. Categorize the receipt type and line items
7. Validate mathematical accuracy

Guidelines:
- Be extremely accurate with numerical values
- Extract ALL line items, not just a summary
- Identify specific product names and categories
- Handle multiple tax rates and discount types
- Preserve original formatting for reference numbers
- Flag any inconsistencies or unclear items
- Provide confidence scores for extracted data

Return data in the specified JSON format with high precision."""

    def __init__(self, config: AgentConfig, anthropic_client: Optional[Anthropic] = None):
        """Initialize the receipt processing agent."""
        super().__init__(config, anthropic_client)
        self.memory: Optional[AgentMemory] = None
        self.processed_receipts = 0
        self.storage_path: Optional[Path] = None

    async def _initialize(self) -> None:
        """Initialize agent-specific resources."""
        # Set up receipt storage
        self.storage_path = Path("storage/processed_data/receipts")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Set up persistent memory
        memory_path = f"storage/agents/{self.agent_id}/memory"
        backend = FileBackend(memory_path)
        self.memory = AgentMemory(self.agent_id, backend)

        # Load previous processing count
        self.processed_receipts = await self.memory.get("processed_receipts", 0)

        # Store agent metadata
        self.set_memory("agent_type", "ReceiptAgent")
        self.set_memory("initialization_time", datetime.utcnow().isoformat())

        print(f"ReceiptAgent {self.name} initialized successfully")

    async def _execute(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute receipt processing."""
        start_time = datetime.utcnow()

        try:
            # Parse the processing request
            request = ReceiptProcessingRequest(**input_data)

            # Process the receipt
            result = await self._process_receipt(request)

            # Store the result
            if result.processing_success:
                await self._store_receipt(result.receipt)

            # Update counters
            self.processed_receipts += 1
            await self.memory.set("processed_receipts", self.processed_receipts)

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time

            return {
                "success": result.processing_success,
                "receipt": result.receipt.model_dump() if result.receipt else None,
                "result": result.model_dump(),
                "agent_stats": {
                    "total_processed": self.processed_receipts,
                    "processing_time": processing_time
                }
            }

        except Exception as e:
            error_msg = f"Receipt processing failed: {str(e)}"
            return {
                "success": False,
                "error": error_msg,
                "receipt": None,
                "agent_stats": {
                    "total_processed": self.processed_receipts,
                    "processing_time": (datetime.utcnow() - start_time).total_seconds()
                }
            }

    async def _process_receipt(self, request: ReceiptProcessingRequest) -> ReceiptProcessingResult:
        """Process a receipt image and extract structured data."""
        try:
            # Prepare image data
            image_data = await self._prepare_image_data(request)
            if not image_data:
                return ReceiptProcessingResult(
                    receipt=self._create_empty_receipt(),
                    processing_success=False,
                    error_message="Failed to load or process image data",
                    processing_time=0.0
                )

            # Extract data using Claude Vision
            extraction_result = await self._extract_with_claude_vision(image_data, request)

            # Create receipt object
            receipt = await self._create_receipt_from_extraction(extraction_result, request)

            # Validate the receipt
            validation_result = await self._validate_receipt(receipt, request)

            # Create processing result
            result = ReceiptProcessingResult(
                receipt=receipt,
                processing_success=True,
                warnings=validation_result.get("warnings", []),
                validation_errors=validation_result.get("errors", []),
                processing_time=0.0,  # Will be set by caller
                confidence_breakdown=extraction_result.get("confidence", {}),
                extraction_confidence=extraction_result.get("overall_confidence", 0.0)
            )

            return result

        except Exception as e:
            return ReceiptProcessingResult(
                receipt=self._create_empty_receipt(),
                processing_success=False,
                error_message=str(e),
                processing_time=0.0
            )

    async def _prepare_image_data(self, request: ReceiptProcessingRequest) -> Optional[Dict[str, Any]]:
        """Prepare image data for processing."""
        try:
            if request.file_data:
                # Use provided file data
                image_bytes = request.file_data
                filename = request.file_name or "receipt.jpg"
            elif request.file_path:
                # Load from file path
                file_path = Path(request.file_path)
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")

                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
                filename = file_path.name
            else:
                raise ValueError("Either file_data or file_path must be provided")

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type or not mime_type.startswith('image/'):
                mime_type = 'image/jpeg'  # Default fallback

            # Get image metadata
            try:
                image = Image.open(io.BytesIO(image_bytes))
                dimensions = image.size
                image.close()
            except Exception:
                dimensions = None

            # Encode for Claude
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            return {
                'image_data': image_base64,
                'mime_type': mime_type,
                'filename': filename,
                'file_size': len(image_bytes),
                'dimensions': dimensions
            }

        except Exception as e:
            print(f"Error preparing image data: {e}")
            return None

    async def _extract_with_claude_vision(
        self,
        image_data: Dict[str, Any],
        request: ReceiptProcessingRequest
    ) -> Dict[str, Any]:
        """Extract structured data using Claude Vision API."""

        # Create the extraction prompt
        extraction_prompt = self._create_extraction_prompt(request)

        try:
            # Make API call to Claude
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model="claude-3-5-sonnet-20241022",  # Use latest Claude with vision
                max_tokens=4000,
                temperature=0.1,  # Low temperature for accuracy
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": extraction_prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_data['mime_type'],
                                    "data": image_data['image_data']
                                }
                            }
                        ]
                    }
                ],
                system=self.SYSTEM_PROMPT
            )

            # Parse the response
            response_text = response.content[0].text

            # Extract JSON from response
            extracted_data = self._parse_claude_response(response_text)

            # Add metadata
            extracted_data['metadata'] = {
                'file_name': image_data['filename'],
                'file_size': image_data['file_size'],
                'file_type': image_data['mime_type'],
                'image_dimensions': image_data['dimensions'],
                'claude_model': "claude-3-5-sonnet-20241022",
                'api_tokens_used': response.usage.input_tokens + response.usage.output_tokens
            }

            return extracted_data

        except Exception as e:
            print(f"Claude extraction error: {e}")
            return {
                'error': str(e),
                'metadata': {
                    'file_name': image_data['filename'],
                    'file_size': image_data['file_size'],
                    'file_type': image_data['mime_type']
                }
            }

    def _create_extraction_prompt(self, request: ReceiptProcessingRequest) -> str:
        """Create the extraction prompt for Claude."""

        base_prompt = """
Please analyze this receipt image and extract all relevant information into a structured JSON format.

Extract the following information:
1. Vendor Information:
   - Business name
   - Address (full address if available)
   - Phone number
   - Website/email if visible

2. Transaction Details:
   - Date (in YYYY-MM-DD format)
   - Time (if available)
   - Receipt/transaction number
   - Store number (if applicable)

3. Financial Information:
   - All line items with descriptions, quantities, unit prices, and totals
   - Subtotal
   - Tax amount(s) and types
   - Discounts or coupons applied
   - Tips (if applicable)
   - Final total amount

4. Payment Information:
   - Payment method (cash, credit card, debit card, etc.)
   - Last 4 digits of card (if visible)

5. Classification:
   - Receipt type (grocery, restaurant, gas, retail, etc.)
   - Business category

Please return the data in this exact JSON structure:
"""

        json_schema = """{
  "vendor": {
    "name": "Business Name",
    "address": "Full address",
    "phone": "Phone number",
    "email": "Email if available",
    "tax_id": "Tax ID if visible"
  },
  "transaction": {
    "date": "YYYY-MM-DD",
    "time": "HH:MM:SS or HH:MM",
    "receipt_number": "Receipt number",
    "store_number": "Store number if applicable"
  },
  "financial": {
    "line_items": [
      {
        "description": "Item description",
        "quantity": 1.0,
        "unit_price": 0.00,
        "total_price": 0.00,
        "category": "Item category",
        "tax_amount": 0.00
      }
    ],
    "subtotal": 0.00,
    "tax_amount": 0.00,
    "tip_amount": 0.00,
    "discount_amount": 0.00,
    "total_amount": 0.00
  },
  "payment": {
    "method": "credit_card",
    "card_last_four": "1234"
  },
  "classification": {
    "receipt_type": "grocery",
    "category": "Food & Dining"
  },
  "confidence": {
    "vendor": 0.95,
    "amounts": 0.98,
    "line_items": 0.90,
    "overall": 0.94
  }
}"""

        # Add processing preferences
        preferences = []
        if request.extract_line_items:
            preferences.append("- Extract ALL individual line items with full details")
        if request.categorize_items:
            preferences.append("- Categorize each line item appropriately")
        if request.validate_totals:
            preferences.append("- Ensure mathematical accuracy of all totals")

        if preferences:
            base_prompt += "\n\nSpecial instructions:\n" + "\n".join(preferences)

        if request.business_context:
            base_prompt += f"\n\nBusiness context: {request.business_context}"

        base_prompt += f"\n\nJSON Schema:\n{json_schema}\n\nBe extremely precise with numerical values and ensure all amounts are accurate to 2 decimal places."

        return base_prompt

    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's response and extract JSON data."""
        try:
            # Find JSON in the response (Claude often wraps it in text)
            import re

            # Look for JSON block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Look for standalone JSON
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    raise ValueError("No JSON found in response")

            # Parse the JSON
            data = json.loads(json_str)
            return data

        except Exception as e:
            print(f"Error parsing Claude response: {e}")
            # Return minimal data structure
            return {
                'vendor': {'name': 'Unknown'},
                'transaction': {'date': datetime.now().strftime('%Y-%m-%d')},
                'financial': {'total_amount': 0.00, 'line_items': []},
                'payment': {'method': 'other'},
                'classification': {'receipt_type': 'other'},
                'confidence': {'overall': 0.0},
                'parse_error': str(e)
            }

    async def _create_receipt_from_extraction(
        self,
        extraction_data: Dict[str, Any],
        request: ReceiptProcessingRequest
    ) -> Receipt:
        """Create a Receipt object from extracted data."""

        try:
            # Create vendor
            vendor_data = extraction_data.get('vendor', {})
            vendor = ReceiptVendor(
                name=vendor_data.get('name', 'Unknown Vendor'),
                address=vendor_data.get('address'),
                phone=vendor_data.get('phone'),
                email=vendor_data.get('email'),
                tax_id=vendor_data.get('tax_id')
            )

            # Parse transaction data
            transaction_data = extraction_data.get('transaction', {})
            date_str = transaction_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            try:
                receipt_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                receipt_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # Parse financial data
            financial_data = extraction_data.get('financial', {})

            # Create line items
            line_items = []
            for item_data in financial_data.get('line_items', []):
                line_item = ReceiptLineItem(
                    description=item_data.get('description', 'Unknown Item'),
                    quantity=item_data.get('quantity', 1.0),
                    unit_price=item_data.get('unit_price'),
                    total_price=item_data.get('total_price', 0.0),
                    category=item_data.get('category'),
                    tax_amount=item_data.get('tax_amount')
                )
                line_items.append(line_item)

            # Parse payment data
            payment_data = extraction_data.get('payment', {})
            payment_method = payment_data.get('method', 'other')
            if payment_method not in [pm.value for pm in PaymentMethod]:
                payment_method = PaymentMethod.OTHER.value

            # Parse classification
            classification_data = extraction_data.get('classification', {})
            receipt_type = classification_data.get('receipt_type', 'other')
            if receipt_type not in [rt.value for rt in ReceiptType]:
                receipt_type = ReceiptType.OTHER.value

            # Create metadata
            metadata_dict = extraction_data.get('metadata', {})
            metadata = ReceiptMetadata(**metadata_dict)

            # Calculate confidence
            confidence_data = extraction_data.get('confidence', {})
            overall_confidence = confidence_data.get('overall', 0.0)

            # Create receipt
            receipt = Receipt(
                vendor=vendor,
                receipt_number=transaction_data.get('receipt_number'),
                date=receipt_date,
                time=transaction_data.get('time'),
                subtotal=financial_data.get('subtotal', 0.0),
                tax_amount=financial_data.get('tax_amount', 0.0),
                tip_amount=financial_data.get('tip_amount'),
                discount_amount=financial_data.get('discount_amount'),
                total_amount=financial_data.get('total_amount', 0.0),
                payment_method=PaymentMethod(payment_method),
                card_last_four=payment_data.get('card_last_four'),
                receipt_type=ReceiptType(receipt_type),
                category=classification_data.get('category'),
                line_items=line_items,
                status=ReceiptStatus.PROCESSED,
                confidence_score=overall_confidence,
                metadata=metadata,
                processed_at=datetime.utcnow()
            )

            # Calculate totals if requested
            if request.validate_totals:
                receipt.calculate_totals()

            return receipt

        except Exception as e:
            print(f"Error creating receipt from extraction: {e}")
            return self._create_empty_receipt()

    def _create_empty_receipt(self) -> Receipt:
        """Create an empty receipt for error cases."""
        return Receipt(
            vendor=ReceiptVendor(name="Unknown"),
            date=datetime.now(),
            subtotal=0.0,
            total_amount=0.0,
            payment_method=PaymentMethod.OTHER,
            receipt_type=ReceiptType.OTHER,
            status=ReceiptStatus.FAILED
        )

    async def _validate_receipt(self, receipt: Receipt, request: ReceiptProcessingRequest) -> Dict[str, List[str]]:
        """Validate receipt data and return warnings/errors."""
        warnings = []
        errors = []

        # Validate totals
        if request.validate_totals and not receipt.validate_totals():
            errors.append("Mathematical totals do not match")

        # Validate required fields
        if not receipt.vendor.name or receipt.vendor.name == "Unknown":
            warnings.append("Vendor name could not be determined")

        if receipt.total_amount <= 0:
            errors.append("Total amount must be positive")

        # Validate confidence scores
        if receipt.confidence_score < 0.5:
            warnings.append("Low confidence in data extraction")

        # Validate line items
        if request.extract_line_items and not receipt.line_items:
            warnings.append("No line items extracted")

        # Validate date
        if receipt.date > datetime.now():
            warnings.append("Receipt date is in the future")

        return {"warnings": warnings, "errors": errors}

    async def _store_receipt(self, receipt: Receipt) -> Path:
        """Store receipt data to persistent storage."""
        # Create filename based on receipt data
        date_str = receipt.date.strftime('%Y%m%d')
        vendor_slug = receipt.vendor.name.lower().replace(' ', '_').replace('/', '_')[:20]
        filename = f"{date_str}_{vendor_slug}_{receipt.receipt_id[:8]}.json"

        file_path = self.storage_path / filename

        # Save receipt data
        with open(file_path, 'w') as f:
            json.dump(receipt.to_dict(), f, indent=2, default=str)

        # Store in memory for quick lookup
        await self.memory.set(
            f"receipt_{receipt.receipt_id}",
            str(file_path),
            ttl_seconds=86400,  # 24 hours
            tags=["receipt", "storage"]
        )

        return file_path

    async def get_receipt_stats(self) -> Dict[str, Any]:
        """Get comprehensive receipt processing statistics."""
        base_stats = self.get_status_info()

        # Get memory stats
        memory_stats = await self.memory.get_stats() if self.memory else {}

        # Calculate recent processing metrics
        recent_receipts = await self.memory.find_by_tags(["receipt"])

        custom_stats = {
            "processed_receipts": self.processed_receipts,
            "memory_stats": memory_stats,
            "recent_receipts_count": len(recent_receipts),
            "storage_path": str(self.storage_path) if self.storage_path else None
        }

        return {**base_stats, **custom_stats}

    async def _cleanup(self) -> None:
        """Clean up agent resources."""
        if self.memory:
            # Clean up old entries
            await self.memory.cleanup_expired()
            print(f"ReceiptAgent {self.name} cleaned up successfully")