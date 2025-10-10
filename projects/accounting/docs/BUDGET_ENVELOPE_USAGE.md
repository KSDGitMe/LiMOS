# Budget Envelope System - Usage Guide

**Date:** 2025-01-08
**Status:** Implemented
**System:** LiMOS Accounting Module

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Setting Up Envelopes](#setting-up-envelopes)
4. [Recording Transactions](#recording-transactions)
5. [Monthly Allocations](#monthly-allocations)
6. [Viewing Balances](#viewing-balances)
7. [Forecasting](#forecasting)
8. [Common Scenarios](#common-scenarios)
9. [API Reference](#api-reference)

---

## Quick Start

### The 30-Second Overview

**Traditional envelope budgeting** involves physically moving money into envelopes. This creates fake transactions.

**Our virtual envelope system** keeps all money in your bank account. Envelopes are just metadata that tracks how much you've "allocated" to different purposes.

**The Fundamental Equation:**
```
Bank Balance = Budget Allocated + Payment Reserved + Available to Spend
```

Example:
```
Bank Account: $5,000
  - Budget Envelopes: $1,200 (Groceries, Gas, Dining, etc.)
  - Payment Reserves: $800 (Credit card payment due)
  = Available: $3,000
```

---

## Core Concepts

### 1. Virtual Envelopes

Envelopes are **NOT** accounts in your Chart of Accounts. They are separate entities that track allocations.

**Two Types:**

#### Budget Envelopes (Expense Categories)
- Track spending by category
- Decrease when you record an expense
- Used for: Groceries, Dining, Gas, Entertainment, etc.
- Purpose: Prevent overspending, forecast variable expenses

#### Payment Envelopes (Liability Reserves)
- Track money reserved for future liability payments
- Increase when you charge on credit
- Decrease when you pay the liability
- Used for: Credit Cards, Auto Loans, Mortgages
- Purpose: Ensure cash is available when payments are due

### 2. Money Never Moves

```
❌ WRONG (Traditional):
Transfer $800 from Checking → Groceries Envelope
(Creates fake transaction, cash "leaves" bank account)

✅ RIGHT (Virtual):
Bank Balance: $5,000 (cash stays here)
Virtual Allocation: Groceries = $800 (metadata only)
Available: $4,200 (calculated: $5,000 - $800)
```

### 3. Transaction Flow Example

**Cash Purchase:**
```
Buy groceries for $50 cash
1. Bank Account (Asset): FROM $50 → decreases by $50
2. Grocery Expense: TO $50 → increases by $50
3. Budget Envelope "Groceries": -$50 (virtual)
```

**Credit Card Purchase:**
```
Buy groceries for $50 on credit card
1. Credit Card Liability: FROM $50 → increases by $50
2. Grocery Expense: TO $50 → increases by $50
3. Budget Envelope "Groceries": -$50 (virtual)
4. Payment Envelope "Credit Card A": +$50 (virtual)

Result:
- Bank Balance: UNCHANGED (haven't paid yet)
- Total Allocated: UNCHANGED (budget decreased, payment increased equally)
- Available: UNCHANGED
```

**Pay Credit Card:**
```
Pay credit card $500
1. Bank Account: FROM $500 → decreases by $500
2. Credit Card Liability: TO $500 → decreases by $500
3. Payment Envelope "Credit Card A": -$500 (virtual)

Result:
- Bank Balance: -$500
- Total Allocated: -$500 (payment reserve released)
- Available: UNCHANGED (lost $500 from bank, freed $500 from reserves)
```

---

## Setting Up Envelopes

### Create a Budget Envelope

```python
from projects.accounting.models import BudgetEnvelope, RolloverPolicy

groceries_envelope = BudgetEnvelope(
    envelope_number="1500",
    envelope_name="Groceries",
    category="Food & Dining",
    monthly_allocation=800.00,
    rollover_policy=RolloverPolicy.ACCUMULATE,
    is_active=True,
    display_order=1
)
```

**Rollover Policies:**

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `RESET` | Zero out at month end, start fresh | Strict budgets (Dining Out) |
| `ACCUMULATE` | Keep balance, add next month's allocation | Build up funds (Vacation, Car Repair) |
| `CAP` | Keep balance up to max, excess returns to Available | Prevent over-accumulation |

### Create a Payment Envelope

```python
from projects.accounting.models import PaymentEnvelope

cc_payment_envelope = PaymentEnvelope(
    envelope_number="1600",
    envelope_name="Credit Card A - Payment Reserve",
    linked_account_id="2100-CreditCard-A",
    is_active=True,
    display_order=1
)
```

### Link Expense Account to Budget Envelope

```python
from projects.accounting.models import ChartOfAccounts, AccountType

grocery_account = ChartOfAccounts(
    account_number="6300",
    account_name="Grocery Stores",
    account_type=AccountType.EXPENSE,
    budget_envelope_id="1500"  # Links to Groceries envelope
)
```

### Link Liability Account to Payment Envelope

```python
credit_card_account = ChartOfAccounts(
    account_number="2100",
    account_name="Credit Card A",
    account_type=AccountType.LIABILITY,
    payment_envelope_id="1600"  # Links to CC Payment envelope
)
```

---

## Recording Transactions

### Method 1: Automatic Envelope Updates (Recommended)

Link envelope IDs at the **account level** (ChartOfAccounts), and the system automatically updates envelopes when transactions post.

```python
from projects.accounting.models import JournalEntry, Distribution, FlowDirection, AccountType
from projects.accounting.services.envelope_service import EnvelopeService

# Create journal entry
entry = JournalEntry(
    entry_date=date(2025, 1, 15),
    description="Groceries at Whole Foods"
)

# Add distributions (envelope_id comes from account's budget_envelope_id)
entry.add_distribution(
    account_id="1000-Cash",
    account_type=AccountType.ASSET,
    flow_direction=FlowDirection.FROM,
    amount=125.50
)

entry.add_distribution(
    account_id="6300-Groceries",
    account_type=AccountType.EXPENSE,
    flow_direction=FlowDirection.TO,
    amount=125.50
)

# Post transaction and update envelopes
envelope_service = EnvelopeService()
envelope_txns = envelope_service.post_journal_entry(entry)
# Budget Envelope "1500-Groceries" automatically decreases by $125.50
```

### Method 2: Explicit Envelope References

Specify envelope IDs directly in the distribution (overrides account-level settings).

```python
entry.add_distribution(
    account_id="6300-Groceries",
    account_type=AccountType.EXPENSE,
    flow_direction=FlowDirection.TO,
    amount=125.50,
    budget_envelope_id="1500"  # Explicit envelope reference
)
```

---

## Monthly Allocations

### Apply Monthly Budget Allocations

Run this at the beginning of each month to "fund" your budget envelopes:

```python
from datetime import date
from projects.accounting.services.envelope_service import EnvelopeService

envelope_service = EnvelopeService()

allocations = envelope_service.apply_monthly_allocations(
    source_account_id="1000-Cash-Checking",
    allocation_date=date(2025, 2, 1),
    period_label="2025-02"
)

# Each active budget envelope receives its monthly_allocation
# Rollover policies are applied automatically
```

**What Happens:**

1. For each active budget envelope:
   - Gets its `monthly_allocation` amount
   - Rollover policy determines new balance:
     - **RESET**: Balance = monthly_allocation
     - **ACCUMULATE**: Balance = old_balance + monthly_allocation
     - **CAP**: Balance = min(old_balance + monthly_allocation, rollover_cap)

2. Creates `BudgetAllocation` audit records

3. Creates `EnvelopeTransaction` records for tracking

**No physical money moves** - this is just updating virtual allocations.

---

## Viewing Balances

### Get Bank Account View

See your complete financial picture:

```python
from projects.accounting.services.envelope_service import EnvelopeService

envelope_service = EnvelopeService()

view = envelope_service.get_bank_account_view(
    account_id="1000-Cash-Checking",
    account_name="Main Checking Account",
    bank_balance=12500.00,  # Current balance from account ledger
    as_of_date=date.today()
)

print(f"Bank Balance: ${view.bank_balance:,.2f}")
print(f"Budget Allocated: ${view.budget_allocated:,.2f}")
print(f"Payment Reserved: ${view.payment_reserved:,.2f}")
print(f"Available to Allocate: ${view.available_to_allocate:,.2f}")
print(f"\nBalanced: {view.is_balanced()}")

# Envelope breakdown
for envelope in view.budget_envelopes:
    print(f"  {envelope['envelope_name']}: ${envelope['balance']:,.2f}")
```

**Output:**
```
Bank Balance: $12,500.00
Budget Allocated: $2,345.67
Payment Reserved: $1,899.00
Available to Allocate: $8,255.33

Balanced: True

Budget Envelopes:
  Groceries: $345.23
  Dining Out: $120.00
  Gas & Auto: $200.00
  Entertainment: $85.44
  ...

Payment Reserves:
  Credit Card A - Payment Reserve: $1,245.67
  Auto Loan - Payment Reserve: $653.33
```

### Validate the Fundamental Equation

```python
validation = view.validate_equation()

print(validation)
# {
#     "bank_balance": 12500.00,
#     "budget_allocated": 2345.67,
#     "payment_reserved": 1899.00,
#     "available_to_allocate": 8255.33,
#     "calculated_total": 12500.00,
#     "difference": 0.00,
#     "is_balanced": True
# }
```

---

## Forecasting

### Forecast Budget Envelope Balance

Project what a budget envelope's balance will be on a future date:

```python
from datetime import date

envelope_service = EnvelopeService()

# Define scheduled expenses
scheduled_expenses = [
    {"date": date(2025, 2, 15), "amount": 150.00, "description": "Groceries"},
    {"date": date(2025, 3, 1), "amount": 175.00, "description": "Groceries"},
    {"date": date(2025, 3, 15), "amount": 160.00, "description": "Groceries"}
]

forecast = envelope_service.forecast_envelope_balance(
    envelope_id="1500-Groceries",
    target_date=date(2025, 3, 31),
    scheduled_expenses=scheduled_expenses
)

print(forecast)
# {
#     "envelope_id": "1500-Groceries",
#     "envelope_name": "Groceries",
#     "current_balance": 345.23,
#     "as_of_date": "2025-01-15",
#     "target_date": "2025-03-31",
#     "months_until_target": 2,
#     "monthly_allocation": 800.00,
#     "rollover_policy": "accumulate",
#     "scheduled_expenses": 485.00,
#     "projected_balance": 1460.23
# }
```

**Calculation:**
```
Current Balance: $345.23
+ 2 months allocations: $1,600.00 (2 × $800)
- Scheduled expenses: -$485.00
= Projected Balance: $1,460.23
```

### Forecast Account Balance (Future Enhancement)

For forecasting actual account balances on future dates, combine:
1. Current account balance
2. Recurring transactions (mortgage, utilities)
3. Budget envelope allocations (forecasted spending)
4. Future-dated transactions

This gives complete visibility into expected cash position at any future date.

---

## Common Scenarios

### Scenario 1: Monthly Budget Setup

```python
# 1. Create budget envelopes
groceries = BudgetEnvelope(
    envelope_number="1500",
    envelope_name="Groceries",
    monthly_allocation=800.00,
    rollover_policy=RolloverPolicy.ACCUMULATE
)

dining = BudgetEnvelope(
    envelope_number="1510",
    envelope_name="Dining Out",
    monthly_allocation=300.00,
    rollover_policy=RolloverPolicy.RESET
)

# 2. Link expense accounts
grocery_account = ChartOfAccounts(
    account_number="6300",
    account_name="Grocery Stores",
    account_type=AccountType.EXPENSE,
    budget_envelope_id="1500"
)

# 3. Apply monthly allocations
envelope_service.apply_monthly_allocations(
    source_account_id="1000-Cash-Checking",
    allocation_date=date(2025, 1, 1),
    period_label="2025-01"
)
```

### Scenario 2: Credit Card Purchase and Payment

```python
# Purchase on credit card
purchase_entry = JournalEntry(
    entry_date=date(2025, 1, 10),
    description="Amazon purchase"
)
purchase_entry.add_distribution(
    account_id="2100-CreditCard",
    account_type=AccountType.LIABILITY,
    flow_direction=FlowDirection.FROM,
    amount=245.67
)
purchase_entry.add_distribution(
    account_id="6400-Shopping",
    account_type=AccountType.EXPENSE,
    flow_direction=FlowDirection.TO,
    amount=245.67
)
envelope_service.post_journal_entry(purchase_entry)
# Budget envelope "Shopping" -$245.67
# Payment envelope "Credit Card" +$245.67

# Pay credit card
payment_entry = JournalEntry(
    entry_date=date(2025, 2, 1),
    description="Credit card payment"
)
payment_entry.add_distribution(
    account_id="1000-Cash",
    account_type=AccountType.ASSET,
    flow_direction=FlowDirection.FROM,
    amount=500.00
)
payment_entry.add_distribution(
    account_id="2100-CreditCard",
    account_type=AccountType.LIABILITY,
    flow_direction=FlowDirection.TO,
    amount=500.00
)
envelope_service.post_journal_entry(payment_entry)
# Payment envelope "Credit Card" -$500.00
```

### Scenario 3: Overspending Detection

```python
# Validate before recording expense
is_valid, warning = envelope_service.validate_expense(
    budget_envelope_id="1510-Dining",
    expense_amount=350.00,
    allow_overspend=False
)

if not is_valid:
    print(f"Warning: {warning}")
    # "Expense $350.00 exceeds budget 'Dining Out' balance $300.00 by $50.00"
```

### Scenario 4: Check Available Funds

```python
# Validate allocation won't exceed available funds
is_valid, error = envelope_service.validate_allocation(
    bank_account_id="1000-Cash",
    allocation_amount=1500.00,
    current_bank_balance=5000.00
)

if not is_valid:
    print(f"Error: {error}")
    # Shows current bank balance, allocated amounts, and available
```

---

## API Reference

### EnvelopeService

#### `post_journal_entry(journal_entry: JournalEntry) -> List[EnvelopeTransaction]`
Post a transaction and update envelope balances.

#### `apply_monthly_allocations(source_account_id, allocation_date, period_label) -> List[BudgetAllocation]`
Apply monthly budget allocations to all active envelopes.

#### `validate_allocation(bank_account_id, allocation_amount, current_bank_balance) -> Tuple[bool, Optional[str]]`
Validate allocation won't exceed available funds.

#### `validate_expense(budget_envelope_id, expense_amount, allow_overspend) -> Tuple[bool, Optional[str]]`
Validate expense won't overspend budget.

#### `get_bank_account_view(account_id, account_name, bank_balance, as_of_date) -> BankAccountView`
Get complete view of bank balance with envelope breakdown.

#### `forecast_envelope_balance(envelope_id, target_date, scheduled_expenses) -> Dict`
Forecast budget envelope balance on future date.

#### `get_total_budget_allocated() -> float`
Sum of all budget envelope balances.

#### `get_total_payment_reserved() -> float`
Sum of all payment envelope balances.

### Models

**BudgetEnvelope**
- `envelope_id`: Unique identifier
- `envelope_number`: Display number (e.g., "1500")
- `envelope_name`: Display name (e.g., "Groceries")
- `monthly_allocation`: Amount to allocate each month
- `rollover_policy`: RESET, ACCUMULATE, or CAP
- `current_balance`: Current virtual balance
- Methods: `record_expense()`, `record_refund()`, `apply_monthly_allocation()`

**PaymentEnvelope**
- `envelope_id`: Unique identifier
- `linked_account_id`: Liability account this tracks
- `current_balance`: Amount reserved for payment
- Methods: `record_charge()`, `record_payment()`, `record_credit()`

**BankAccountView**
- `bank_balance`: Real cash in bank
- `budget_allocated`: Sum of budget envelopes
- `payment_reserved`: Sum of payment envelopes
- `available_to_allocate`: Bank - Budget - Payment
- Methods: `is_balanced()`, `validate_equation()`

---

## Best Practices

### 1. Always Link Envelopes at Account Level
Set `budget_envelope_id` and `payment_envelope_id` on accounts in Chart of Accounts. This ensures automatic envelope updates.

### 2. Run Monthly Allocations on Schedule
Set up a recurring job to run `apply_monthly_allocations()` on the 1st of each month.

### 3. Validate Before Posting
Use `validate_expense()` before creating transactions to warn users about overspending.

### 4. Review Bank Account View Regularly
Use `get_bank_account_view()` to ensure the fundamental equation always balances.

### 5. Use Rollover Policies Strategically
- **RESET**: Strict budgets (prevent overspending)
- **ACCUMULATE**: Savings goals (vacation, emergency fund)
- **CAP**: Prevent excessive accumulation while allowing some flexibility

### 6. Forecast Before Committing
Use `forecast_envelope_balance()` to see if future expenses will fit within budget.

---

## Troubleshooting

### "Bank account not balanced"
Run `validate_equation()` to see where the discrepancy is. Check for:
- Envelope balances manually edited
- Transactions posted without updating envelopes
- Bank balance not current

### "Envelope not found"
Ensure:
- Envelope ID exists in the system
- Envelope is active
- Account's envelope_id references are correct

### "Cannot allocate - insufficient funds"
Check `get_bank_account_view()` to see current allocations. You may need to:
- Release unused budget allocations
- Pay down liabilities to free payment reserves
- Increase bank balance

---

## Summary

The virtual envelope system provides:

✅ **Clear visibility** - See exactly where your money is allocated
✅ **No fake transactions** - Money stays in bank accounts
✅ **Automatic tracking** - Envelopes update when transactions post
✅ **Forecasting** - Project future balances based on budgets
✅ **Overspending prevention** - Validate before posting
✅ **Dual tracking** - Budget categories + liability payment reserves

**The fundamental equation always holds:**
```
Bank Balance = Budget Allocated + Payment Reserved + Available
```
