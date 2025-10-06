# Receipt Processing API

A comprehensive FastAPI-based REST API for processing receipt images using Claude Vision AI.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Anthropic API Key
- FastAPI and dependencies installed

### Running the API

```bash
# Navigate to API directory
cd projects/accounting/features/receipts/api

# Start the server
python main.py
```

The API will be available at:
- **Base URL**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📋 API Endpoints

### Health & Status
- `GET /health` - System health check and status
- `GET /` - API information and available endpoints

### Receipt Processing
- `POST /receipts/process` - Process a single receipt image
- `GET /receipts/{receipt_id}` - Get receipt by ID
- `PUT /receipts/{receipt_id}` - Update receipt information
- `DELETE /receipts/{receipt_id}` - Delete receipt

### Search & Discovery
- `POST /receipts/search` - Advanced search with filters
- `GET /receipts` - List receipts with optional filters

### Batch Processing
- `POST /batch/process` - Process multiple receipts
- `GET /batch/jobs/{job_id}/status` - Check batch job status
- `GET /batch/jobs/{job_id}/results` - Get batch results
- `GET /batch/jobs` - List all batch jobs
- `DELETE /batch/jobs/{job_id}` - Cancel batch job
- `POST /batch/jobs/{job_id}/retry` - Retry failed batch job

### Export & Analytics
- `GET /receipts/stats` - Storage statistics
- `POST /receipts/export` - Export receipts data

## 🔐 Authentication

The API supports two authentication methods:

### JWT Tokens
```bash
curl -H "Authorization: Bearer your_jwt_token" \
     http://localhost:8000/receipts
```

### API Keys
```bash
curl -H "X-API-Key: your_api_key" \
     http://localhost:8000/receipts
```

## 📝 Usage Examples

### Process a Receipt

```python
import httpx
import asyncio

async def process_receipt():
    async with httpx.AsyncClient() as client:
        # Upload and process receipt
        with open("receipt.jpg", "rb") as f:
            response = await client.post(
                "http://localhost:8000/receipts/process",
                files={"file": f},
                data={
                    "extract_line_items": True,
                    "categorize_items": True,
                    "validate_totals": True
                }
            )

        result = response.json()
        if result["success"]:
            print(f"Receipt ID: {result['receipt']['receipt_id']}")
            print(f"Vendor: {result['receipt']['vendor']['name']}")
            print(f"Total: ${result['receipt']['total_amount']}")
        else:
            print(f"Error: {result['error_message']}")

asyncio.run(process_receipt())
```

### Search Receipts

```python
import httpx

# Search for receipts from a specific vendor
search_params = {
    "vendor_name": "Walmart",
    "min_amount": 10.0,
    "max_amount": 100.0,
    "limit": 20
}

response = httpx.post(
    "http://localhost:8000/receipts/search",
    json=search_params
)

results = response.json()
print(f"Found {results['total_count']} receipts")
for receipt in results['receipts']:
    print(f"- {receipt['vendor']['name']}: ${receipt['total_amount']}")
```

### Batch Processing

```python
import httpx

# Process multiple receipts
files = [
    ("files", open("receipt1.jpg", "rb")),
    ("files", open("receipt2.jpg", "rb")),
    ("files", open("receipt3.jpg", "rb"))
]

response = httpx.post(
    "http://localhost:8000/batch/process",
    files=files,
    data={"max_concurrent": 2}
)

job = response.json()
job_id = job["job_id"]

# Check status
status_response = httpx.get(f"http://localhost:8000/batch/jobs/{job_id}/status")
status = status_response.json()
print(f"Progress: {status['progress_percentage']}%")
```

## 📊 Request/Response Models

### Receipt Processing Response
```json
{
  "success": true,
  "receipt": {
    "receipt_id": "uuid",
    "vendor": {
      "name": "Store Name",
      "address": "123 Main St",
      "phone": "555-0123"
    },
    "date": "2024-01-15T10:30:00Z",
    "total_amount": 45.67,
    "subtotal": 42.50,
    "tax_amount": 3.17,
    "payment_method": "credit_card",
    "line_items": [
      {
        "description": "Item 1",
        "quantity": 2,
        "unit_price": 10.00,
        "total_price": 20.00
      }
    ]
  },
  "processing_time": 2.5,
  "confidence_breakdown": {
    "vendor_confidence": 0.95,
    "total_confidence": 0.98
  }
}
```

### Search Request
```json
{
  "vendor_name": "Walmart",
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "min_amount": 10.0,
  "max_amount": 100.0,
  "receipt_type": "grocery",
  "limit": 50,
  "offset": 0
}
```

## ⚙️ Configuration

### File Upload Limits
- **Max file size**: 10MB
- **Supported formats**: JPEG, PNG, TIFF, PDF
- **Max batch size**: 20 files

### Rate Limits
- **Default**: 100 requests/hour
- **Upload**: 20 requests/hour
- **Batch**: 5 requests/hour

## 🧪 Testing

Run the comprehensive test suite:

```bash
# All tests
python -m pytest test_api.py -v

# Specific test class
python -m pytest test_api.py::TestReceiptProcessing -v

# With coverage
python -m pytest test_api.py --cov=. --cov-report=html
```

## 🐛 Error Handling

The API returns detailed error responses:

```json
{
  "error": "Validation failed",
  "detail": "File too large. Maximum size is 10MB",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "uuid"
}
```

### Common Error Codes
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **413**: Payload Too Large (file size limits)
- **415**: Unsupported Media Type (invalid file format)
- **422**: Unprocessable Entity (malformed data)
- **429**: Too Many Requests (rate limit exceeded)
- **503**: Service Unavailable (agent not ready)

## 📚 Additional Resources

- [API Client Examples](examples/client_examples.py) - Complete usage examples
- [System Architecture](../../../../system/docs/architecture/overview.md) - Overall system design
- [Agent Development](../../../../core/agents/README.md) - Creating new agents

## 🤝 Contributing

1. Add new endpoints to `main.py`
2. Update models in `models.py`
3. Add authentication to `auth.py`
4. Write tests in `test_api.py`
5. Update this documentation

## 📞 Support

For issues or questions:
1. Check the [test examples](test_api.py) for expected behavior
2. Review [client examples](examples/client_examples.py) for usage patterns
3. Open an issue in the main repository