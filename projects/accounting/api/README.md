# Accounting Module API

FastAPI REST API for the LiMOS Accounting Module with 6 specialized agents.

## Features

- **Transaction Management** - Create, search, and manage transactions with recurring schedules
- **Cash Flow Forecasting** - Project account balances with confidence intervals
- **Budget Management** - Track budgets with real-time alerts and variance analysis
- **Reconciliation** - Match statements and process payments
- **Reporting & Analytics** - Generate financial reports, insights, and KPIs
- **Net Worth Tracking** - Track assets, liabilities, and financial goals

## Installation

```bash
cd projects/accounting/api
pip install -r requirements.txt
```

## Running the API

```bash
# Development server with auto-reload
uvicorn projects.accounting.api.app:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn projects.accounting.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Quick Start Examples

### 1. Create a Transaction

```bash
curl -X POST "http://localhost:8000/api/v1/transactions/" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "checking_001",
    "date": "2025-10-07",
    "merchant": "Grocery Store",
    "amount": 45.67,
    "transaction_type": "expense",
    "category": "Groceries"
  }'
```

### 2. Create Recurring Transaction (Paycheck)

```bash
curl -X POST "http://localhost:8000/api/v1/transactions/recurring" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "Bi-Weekly Paycheck",
    "account_id": "checking_001",
    "merchant": "Employer Inc",
    "base_amount": 2500.00,
    "transaction_type": "income",
    "category": "Salary",
    "recurrence_rule": {
      "frequency": "monthly",
      "interval": 1,
      "day_of_month": [1, 15]
    },
    "start_date": "2025-01-01"
  }'
```

### 3. Create Cash Flow Forecast

```bash
curl -X POST "http://localhost:8000/api/v1/forecasting/" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "checking_001",
    "start_date": "2025-10-01",
    "end_date": "2025-12-31",
    "reference_date": "2025-10-07",
    "reference_balance": 5000.00,
    "interest_rate": 0.02,
    "confidence_level": "medium"
  }'
```

### 4. Create Budget

```bash
curl -X POST "http://localhost:8000/api/v1/budgets/" \
  -H "Content-Type: application/json" \
  -d '{
    "budget_name": "October 2025",
    "budget_type": "monthly",
    "start_date": "2025-10-01",
    "end_date": "2025-10-31",
    "current_period": "2025-10",
    "categories": [
      {"category": "Groceries", "allocated_amount": 600.00},
      {"category": "Dining", "allocated_amount": 300.00},
      {"category": "Transportation", "allocated_amount": 400.00}
    ]
  }'
```

### 5. Generate Income Statement

```bash
curl -X POST "http://localhost:8000/api/v1/reporting/income-statement" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-01",
    "end_date": "2025-10-31"
  }'
```

### 6. Create Net Worth Snapshot

```bash
curl -X POST "http://localhost:8000/api/v1/networth/snapshots"
```

## API Endpoints Overview

### Transactions (`/api/v1/transactions`)
- `POST /` - Create transaction
- `GET /{id}` - Get transaction
- `GET /` - Search transactions
- `POST /recurring` - Create recurring template
- `GET /recurring/{id}` - Get recurring template
- `POST /recurring/{id}/occurrences` - Calculate next occurrences
- `POST /recurring/generate` - Generate scheduled transactions

### Forecasting (`/api/v1/forecasting`)
- `POST /` - Create forecast
- `GET /{id}` - Get forecast
- `GET /` - List forecasts
- `GET /{id}/critical-dates` - Get critical dates

### Budgets (`/api/v1/budgets`)
- `POST /` - Create budget
- `GET /{id}` - Get budget
- `GET /` - List budgets
- `GET /alerts` - Get budget alerts
- `POST /alerts/{id}/acknowledge` - Acknowledge alert
- `POST /{id}/variance-report` - Generate variance report
- `POST /{id}/project-spending` - Project spending

### Reconciliation (`/api/v1/reconciliation`)
- `POST /statements` - Import statement
- `GET /statements/{id}` - Get statement
- `POST /reconciliations` - Start reconciliation
- `POST /reconciliations/{id}/match` - Auto-match transactions
- `POST /reconciliations/{id}/complete` - Complete reconciliation
- `POST /payments` - Schedule payment
- `POST /payments/process` - Process payments
- `POST /payments/{id}/cancel` - Cancel payment

### Reporting (`/api/v1/reporting`)
- `POST /income-statement` - Generate P&L
- `POST /balance-sheet` - Generate balance sheet
- `POST /cash-flow-statement` - Generate cash flow
- `POST /analyze/spending` - Analyze spending
- `POST /analyze/income` - Analyze income
- `POST /analyze/trends` - Analyze trends
- `POST /compare-periods` - Compare periods
- `POST /insights/generate` - Generate insights
- `GET /insights` - Get insights
- `POST /kpis/calculate` - Calculate KPIs
- `POST /tax-summary` - Generate tax summary

### Net Worth (`/api/v1/networth`)
- `POST /assets` - Create asset
- `GET /assets` - List assets
- `PUT /assets/{id}` - Update asset
- `POST /liabilities` - Create liability
- `GET /liabilities` - List liabilities
- `POST /snapshots` - Create snapshot
- `GET /snapshots` - List snapshots
- `POST /analyze/trends` - Analyze trends
- `GET /analyze/allocation` - Analyze allocation
- `POST /goals` - Create goal
- `GET /goals` - List goals
- `POST /payoff-plans` - Create debt payoff plan
- `POST /report` - Generate net worth report

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                 (app.py with lifespan)                      │
└─────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┼────────────┬─────────────┐
                │            │            │             │
                ▼            ▼            ▼             ▼
         ┌───────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
         │Transaction│ │Forecasting│ │ Budget  │ │Reporting│
         │  Router   │ │  Router   │ │ Router  │ │ Router  │
         └───────────┘ └──────────┘ └─────────┘ └──────────┘
                │            │            │             │
                ▼            ▼            ▼             ▼
         ┌───────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
         │Transaction│ │   Cash   │ │ Budget  │ │Reporting│
         │   Agent   │ │   Flow   │ │  Agent  │ │  Agent  │
         │           │ │  Agent   │ │         │ │         │
         └───────────┘ └──────────┘ └─────────┘ └──────────┘
                │            │            │             │
                └────────────┴────────────┴─────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   SQLite Database    │
                  │   (accounting.db)    │
                  └──────────────────────┘
```

## Event-Driven Integration

Agents communicate via message bus for real-time updates:
- Transactions trigger budget updates
- Budget alerts generate insights
- Statement imports trigger reconciliation

## Response Format

All endpoints return:
```json
{
  "status": "success",
  "result": { ... }
}
```

Errors return:
```json
{
  "detail": "Error message"
}
```

## Production Considerations

1. **Authentication**: Add JWT/OAuth2 authentication
2. **Rate Limiting**: Implement rate limiting middleware
3. **CORS**: Configure allowed origins appropriately
4. **Database**: Consider PostgreSQL for production
5. **Caching**: Add Redis for frequently accessed data
6. **Logging**: Configure structured logging
7. **Monitoring**: Add Prometheus/Grafana metrics

## Testing

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest tests/
```

## License

Part of the LiMOS project.
