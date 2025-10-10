# API & CLI Quick Start Guide

**Date:** 2025-01-08
**Version:** 1.0.0

---

## Overview

LiMOS Accounting provides two interfaces for users:

1. **REST API** - For web apps, mobile apps, integrations
2. **CLI Tool** - For command-line users, scripts, automation

Both interfaces provide full access to:
- Journal entries and transactions
- Budget and payment envelopes
- Recurring transaction templates
- Account balance forecasting
- Chart of accounts

---

## Installation

### 1. Install Dependencies

```bash
cd /Users/ksd/Projects/LiMOS/projects/accounting
pip install -r requirements.txt
```

### 2. Make CLI Executable (Optional)

```bash
chmod +x cli/limos.py
ln -s $(pwd)/cli/limos.py /usr/local/bin/limos
```

---

## Quick Start: API

### Start the Server

```bash
# Method 1: Using CLI
limos serve

# Method 2: Direct uvicorn
python -m uvicorn projects.accounting.api.main:app --reload

# Method 3: Python script
cd projects/accounting/api
python main.py
```

Server starts on: **http://localhost:8000**

### Interactive Documentation

Open in browser:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# List accounts
curl http://localhost:8000/api/accounts

# Get statistics
curl http://localhost:8000/api/stats/summary
```

---

## Quick Start: CLI

### Basic Commands

```bash
# Show help
limos --help

# Show statistics
limos stats

# List accounts
limos accounts list

# List transactions
limos tx list --limit 10

# List budget envelopes
limos budget list

# List recurring templates
limos recurring list
```

---

## Complete API Reference

### Journal Entries

#### Create Transaction
```bash
POST /api/journal-entries
Content-Type: application/json

{
  "entry_date": "2025-01-15",
  "description": "Groceries at Whole Foods",
  "distributions": [
    {
      "account_id": "1000",
      "account_type": "asset",
      "flow_direction": "from",
      "amount": 125.50,
      "multiplier": -1,
      "debit_credit": "Cr"
    },
    {
      "account_id": "6300",
      "account_type": "expense",
      "flow_direction": "to",
      "amount": 125.50,
      "multiplier": 1,
      "debit_credit": "Dr",
      "budget_envelope_id": "1500"
    }
  ],
  "status": "posted"
}
```

**Response:**
```json
{
  "journal_entry_id": "abc123...",
  "entry_date": "2025-01-15",
  "description": "Groceries at Whole Foods",
  "status": "posted",
  "distributions": [...]
}
```

#### List Transactions
```bash
GET /api/journal-entries?start_date=2025-01-01&end_date=2025-01-31&limit=20
```

#### Get Transaction
```bash
GET /api/journal-entries/{entry_id}
```

#### Post Transaction
```bash
POST /api/journal-entries/{entry_id}/post
```

#### Void Transaction
```bash
DELETE /api/journal-entries/{entry_id}
```

---

### Chart of Accounts

#### List Accounts
```bash
GET /api/accounts?account_type=asset&is_active=true
```

#### Get Account
```bash
GET /api/accounts/{account_id}
```

#### Create Account
```bash
POST /api/accounts
Content-Type: application/json

{
  "account_number": "1150",
  "account_name": "Investment Account",
  "account_type": "asset",
  "current_balance": 50000.00,
  "is_active": true
}
```

#### Get Account View (with Envelopes)
```bash
GET /api/accounts/{account_id}/view?as_of_date=2025-01-15
```

**Response:**
```json
{
  "account_id": "1000",
  "account_name": "Cash - Checking",
  "bank_balance": 25000.00,
  "budget_allocated": 1767.40,
  "payment_reserved": 21621.93,
  "available_to_allocate": 1610.67,
  "as_of_date": "2025-01-15",
  "budget_envelopes": [...],
  "payment_envelopes": [...],
  "is_balanced": true
}
```

---

### Budget Envelopes

#### List Budget Envelopes
```bash
GET /api/envelopes/budget?active_only=true
```

#### List Payment Envelopes
```bash
GET /api/envelopes/payment?active_only=true
```

#### Create Budget Envelope
```bash
POST /api/envelopes/budget
Content-Type: application/json

{
  "envelope_number": "1580",
  "envelope_name": "Vacation Fund",
  "envelope_type": "budget",
  "monthly_allocation": 500.00,
  "rollover_policy": "accumulate",
  "is_active": true
}
```

#### Apply Monthly Allocations
```bash
POST /api/envelopes/allocate?source_account_id=1000&allocation_date=2025-02-01&period_label=2025-02
```

---

### Recurring Templates

#### List Templates
```bash
GET /api/recurring-templates?active_only=true
```

#### Get Template
```bash
GET /api/recurring-templates/{template_id}
```

#### Create Template
```bash
POST /api/recurring-templates
Content-Type: application/json

{
  "template_name": "Cell Phone Bill",
  "description": "Monthly cell phone payment",
  "frequency": "monthly",
  "day_of_month": 10,
  "start_date": "2025-01-10",
  "distribution_template": [
    {
      "account_id": "1000",
      "account_type": "asset",
      "flow_direction": "from",
      "amount": 85.00
    },
    {
      "account_id": "6230",
      "account_type": "expense",
      "flow_direction": "to",
      "amount": 85.00
    }
  ],
  "is_active": true
}
```

#### Expand Templates
```bash
POST /api/recurring-templates/expand?start_date=2025-01-01&end_date=2025-12-31&auto_post=false
```

**Response:** Array of generated JournalEntry objects

---

### Forecasting

#### Forecast Account Balance
```bash
GET /api/forecast/account/{account_id}?target_date=2025-06-15
```

**Response:**
```json
{
  "account_id": "1000",
  "account_name": "Cash - Checking",
  "current_balance": 25000.00,
  "as_of_date": "2025-01-08",
  "target_date": "2025-06-15",
  "projected_balance": 49316.00,
  "balance_change": 24316.00,
  "transactions_applied": 87
}
```

#### Forecast Envelope Balance
```bash
GET /api/forecast/envelope/{envelope_id}?target_date=2025-06-15
```

---

### Statistics

#### Get Summary
```bash
GET /api/stats/summary
```

**Response:**
```json
{
  "chart_of_accounts": {
    "total": 15,
    "by_type": {
      "assets": 2,
      "liabilities": 3,
      "equity": 1,
      "revenue": 1,
      "expenses": 8
    }
  },
  "journal_entries": {
    "total": 234,
    "posted": 234,
    "draft": 0
  },
  "envelopes": {
    "budget": 8,
    "payment": 3,
    "total_budget_allocated": 1767.40,
    "total_payment_reserved": 21621.93
  },
  "recurring_templates": {
    "total": 11,
    "active": 11
  }
}
```

---

## Complete CLI Reference

### Transaction Commands

#### Add Transaction
```bash
limos tx add "Groceries at Whole Foods" \
  --from 1000:125.50 \
  --to 6300:125.50 \
  --date 2025-01-15 \
  --post
```

**Multiple Distributions:**
```bash
limos tx add "Split purchase" \
  --from 1000:150.00 \
  --to 6300:100.00 \
  --to 6310:50.00 \
  --post
```

#### List Transactions
```bash
# Recent 20
limos tx list

# Filter by date
limos tx list --start 2025-01-01 --end 2025-01-31

# Filter by status
limos tx list --status posted --limit 50
```

---

### Budget Commands

#### List Envelopes
```bash
limos budget list
```

**Output:**
```
Envelope                        Monthly       Balance     Policy
Groceries                       $800.00       $366.90     accumulate
Dining Out                      $300.00       $210.50     reset
Gas & Auto                      $250.00       $185.00     accumulate
```

#### Apply Monthly Allocations
```bash
limos budget allocate --month 2025-02 --source 1000
```

---

### Forecast Commands

#### Forecast Account
```bash
limos forecast account --account 1000 --date 2025-06-15
```

**Output:**
```
📊 Account Forecast: Cash - Checking
   Current Balance:    $   25,000.00  (as of 2025-01-08)
   Projected Balance:  $   49,316.00  (on 2025-06-15)
   Change:             $   24,316.00
   Transactions:                  87 recurring entries applied
```

---

### Recurring Commands

#### List Templates
```bash
limos recurring list
```

**Output:**
```
Template                                  Frequency      Start Date   Status
Salary - Biweekly Paycheck               biweekly       2025-01-03   Active
Mortgage Payment                         monthly        2025-01-01   Active
Property Tax Payment                     quarterly      2025-01-15   Active
```

#### Expand Templates
```bash
limos recurring expand \
  --start 2025-01-01 \
  --end 2025-12-31 \
  --post
```

---

### Account Commands

#### List Accounts
```bash
# All accounts
limos accounts list

# By type
limos accounts list --type asset
limos accounts list --type expense
```

**Output:**
```
Number  Name                                Type        Balance
1000    Cash - Checking                     asset       $25,000.00
1100    Cash - Savings                      asset       $50,000.00
2100    Credit Card A                       liability   $1,876.93
```

#### View Account (with Envelopes)
```bash
limos accounts view 1000
```

**Output:**
```
💰 Cash - Checking
   Bank Balance:       $   25,000.00
   Budget Allocated:   $    1,767.40
   Payment Reserved:   $   21,621.93
   Available:          $    1,610.67
   Balanced: ✓
```

---

### Statistics

```bash
limos stats
```

**Output:**
```
📊 LiMOS Accounting System Statistics

Chart of Accounts:
   Total: 15
   - Assets: 2
   - Liabilities: 3
   - Equity: 1
   - Revenue: 1
   - Expenses: 8

Journal Entries:
   Total: 234
   - Posted: 234
   - Draft: 0

Envelopes:
   Budget Envelopes: 8
   Payment Envelopes: 3
   Total Budget Allocated: $1,767.40
   Total Payment Reserved: $21,621.93

Recurring Templates:
   Total: 11
   Active: 11
```

---

## Common Workflows

### Workflow 1: Daily Expense Entry

```bash
# Morning coffee
limos tx add "Starbucks" --from 1000:5.50 --to 6310:5.50 --post

# Lunch
limos tx add "Chipotle" --from 2100:12.00 --to 6310:12.00 --post

# Gas
limos tx add "Shell gas station" --from 1000:45.00 --to 6400:45.00 --post

# Check remaining budgets
limos budget list
```

---

### Workflow 2: Month-End Close

```bash
# 1. Apply next month's allocations
limos budget allocate --month 2025-02

# 2. Generate recurring transactions for next month
limos recurring expand --start 2025-02-01 --end 2025-02-28 --post

# 3. Check stats
limos stats

# 4. Forecast next month end
limos forecast account --account 1000 --date 2025-02-28
```

---

### Workflow 3: Plan a Large Purchase

```bash
# Forecast balance 3 months out
limos forecast account --account 1000 --date 2025-04-15

# Check available after allocations
limos accounts view 1000

# Decision: Can I afford $5,000 purchase?
# Compare projected balance + available to purchase amount
```

---

### Workflow 4: API Integration (Python)

```python
import requests

API_URL = "http://localhost:8000"

# Create transaction via API
def create_expense(description, amount, account_from, account_to):
    entry = {
        "entry_date": "2025-01-15",
        "description": description,
        "distributions": [
            {
                "account_id": account_from,
                "account_type": "asset",
                "flow_direction": "from",
                "amount": amount,
                "multiplier": -1,
                "debit_credit": "Cr"
            },
            {
                "account_id": account_to,
                "account_type": "expense",
                "flow_direction": "to",
                "amount": amount,
                "multiplier": 1,
                "debit_credit": "Dr"
            }
        ],
        "status": "posted"
    }

    response = requests.post(f"{API_URL}/api/journal-entries", json=entry)
    return response.json()

# Use it
result = create_expense("Groceries", 125.50, "1000", "6300")
print(f"Created entry: {result['journal_entry_id']}")
```

---

## Troubleshooting

### API Won't Start

**Problem:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install fastapi uvicorn pydantic click requests tabulate
```

---

### CLI Can't Connect to API

**Problem:** `Connection refused` error

**Solution:**
```bash
# Make sure API is running
limos serve

# Or start manually in separate terminal
python -m uvicorn projects.accounting.api.main:app --reload
```

---

### Transaction Not Balanced

**Problem:** `Journal entry is not balanced` error

**Solution:**
```bash
# Make sure FROM total = TO total
limos tx add "Test" \
  --from 1000:100.00 \
  --to 6300:100.00    # Must match!
```

---

## Next Steps

1. **Try the Examples** - Run through the workflows above
2. **Explore the API** - Visit http://localhost:8000/docs
3. **Build Automation** - Write scripts using CLI or API
4. **Mobile App?** - Use the API to build a mobile interface
5. **Voice Entry?** - Integrate with speech-to-text
6. **Bank Import?** - Connect to Plaid or bank APIs

---

**Ready to brainstorm other options now!** 🚀
