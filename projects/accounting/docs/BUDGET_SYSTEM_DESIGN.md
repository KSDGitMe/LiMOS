# Budget System Design - Virtual Envelope Accounting

**Date:** 2025-01-08
**Status:** Design Phase - Not Yet Implemented
**System:** LiMOS Accounting Module

---

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [FROM/TO Accounting System](#fromto-accounting-system)
4. [Virtual Envelope Architecture](#virtual-envelope-architecture)
5. [Transaction Flows](#transaction-flows)
6. [Data Models](#data-models)
7. [Display & Reporting](#display--reporting)
8. [Implementation Notes](#implementation-notes)

---

## Overview

### Goal
Create a budgeting system where you can see **expected account balances on any future date**, using a virtual envelope allocation system that prevents double-spending while maintaining clear separation between budgeted and available funds.

### Key Innovation
**Budgets and Payment Reserves are virtual accumulators, not physical money movements.**

Money stays in the bank account. Virtual envelopes are metadata that track:
- **Budget Envelopes**: How much you've allocated for different expense categories
- **Payment Envelopes**: How much you've committed to paying future liabilities (credit cards, loans)

### Core Formula
```
Bank Balance = Budget Allocated + Payment Reserved + Available to Allocate
```

---

## Core Concepts

### 1. Virtual Envelopes vs Physical Money

**Traditional (Wrong) Approach:**
```
Transfer $800 from Checking → Budget Envelope "Groceries"
(Creates fake money movement transactions)
```

**Our Approach:**
```
Checking Balance: $5,000 (real money stays here)

Virtual Allocations (metadata only):
  - Budget: Groceries = $800
  - Budget: Dining = $300
  - Payment: Credit Card = $245

Available: $3,655 = $5,000 - $800 - $300 - $245
```

### 2. Two Types of Virtual Envelopes

#### Budget Envelopes (Expense Tracking)
- Purpose: Track spending by category
- When they decrease: When an expense is recorded (regardless of payment method)
- Examples: Groceries, Dining, Gas, Entertainment

#### Payment Envelopes (Liability Tracking)
- Purpose: Reserve money for future liability payments
- When they increase: When you use credit (create a liability)
- When they decrease: When you pay the liability
- Examples: Credit Card A, Credit Card B, Auto Loan, Mortgage

### 3. Budget → Expense Account Relationship

**Budget Envelopes have 1-to-Many relationship with Expense Accounts:**

```
Budget Envelope "Food & Dining" (1500)
    ↑ referenced by
    ├── Expense Account "Grocery Stores" (6300)
    ├── Expense Account "Farmers Markets" (6301)
    ├── Expense Account "Restaurants" (6310)
    └── Expense Account "Fast Food" (6311)
```

**Expense accounts reference their budget envelope:**
```json
{
  "account_id": "6300",
  "account_name": "Grocery Stores",
  "account_type": "expense",
  "budget_envelope_id": "1500"
}
```

---

## FROM/TO Accounting System

### Quick Reference

Our system uses **FROM/TO flow direction** instead of traditional Debit/Credit, with automatic Dr/Cr calculation.

### Every Distribution Has:

| Field | Description | Example |
|-------|-------------|---------|
| `account_id` | Account being affected | "1000-Cash" |
| `account_type` | Asset, Liability, Equity, Revenue, Expense | "asset" |
| `flow_direction` | FROM (out) or TO (in) | "from" |
| `amount` | Always positive | 245.67 |
| `multiplier` | +1 or -1 (auto-calculated) | -1 |
| `debit_credit` | Dr or Cr (auto-calculated) | "Cr" |

### Balance Calculation Formula
```
new_balance = old_balance + (amount × multiplier)
```

### Multiplier Rules

| Account Type | Flow Direction | Multiplier | Effect | Dr/Cr |
|--------------|----------------|------------|--------|-------|
| Asset        | TO (in)        | +1         | Increase | Dr |
| Asset        | FROM (out)     | -1         | Decrease | Cr |
| Liability    | TO (in)        | -1         | Decrease | Dr |
| Liability    | FROM (out)     | +1         | Increase | Cr |
| Equity       | TO (in)        | -1         | Decrease | Dr |
| Equity       | FROM (out)     | +1         | Increase | Cr |
| Revenue      | TO (in)        | -1         | Decrease | Dr |
| Revenue      | FROM (out)     | +1         | Increase | Cr |
| Expense      | TO (in)        | +1         | Increase | Dr |
| Expense      | FROM (out)     | -1         | Decrease | Cr |

### Example: Pay Vendor $500

```json
{
  "description": "Payment to ABC Vendor",
  "distributions": [
    {
      "account_id": "1000-Cash",
      "account_type": "asset",
      "flow_direction": "from",
      "amount": 500.00,
      "multiplier": -1,
      "debit_credit": "Cr"
    },
    {
      "account_id": "2000-Accounts-Payable",
      "account_type": "liability",
      "flow_direction": "to",
      "amount": 500.00,
      "multiplier": -1,
      "debit_credit": "Dr"
    }
  ]
}
```

**Result:** Both Cash (asset) and A/P (liability) decrease by $500.

---

## Virtual Envelope Architecture

### Account Structure

```
Chart of Accounts:
├── 1000-1499: Regular Assets (Cash, Savings, A/R)
├── 2000-2999: Liabilities (A/P, Credit Cards, Loans)
├── 3000-3999: Equity
├── 4000-4999: Revenue
└── 5000-9999: Expenses

Virtual Envelopes (NOT in Chart of Accounts):
├── Budget Envelopes (1500-1599)
│   ├── 1500: Budget - Groceries
│   ├── 1501: Budget - Dining
│   ├── 1502: Budget - Gas/Auto
│   ├── 1503: Budget - Entertainment
│   └── 1504: Budget - Utilities
│
└── Payment Envelopes (1600-1699)
    ├── 1600: Payment - Credit Card A
    ├── 1601: Payment - Credit Card B
    ├── 1602: Payment - Auto Loan
    └── 1603: Payment - Mortgage
```

### Key Design Decision

**Budget and Payment Envelopes are NOT accounts in the Chart of Accounts.**

They are separate entities that:
- Track virtual allocations of real money
- Reference real bank accounts where money actually sits
- Are modified through transaction metadata, not direct transactions

---

## Transaction Flows

### Flow 1: Month Start - Allocate Budget

**Action:** Allocate $800 to Groceries budget

```json
{
  "allocation_id": "alloc-2025-04-groceries",
  "allocation_date": "2025-04-01",
  "bank_account_id": "1000-Checking",
  "budget_envelope_id": "1500-Budget-Groceries",
  "allocated_amount": 800.00,
  "allocation_type": "monthly_funding"
}
```

**This is NOT a journal entry transaction!** It's pure metadata.

**Effects:**
```
Checking Balance:     $5,000.00 (unchanged)
Budget "Groceries":   $  800.00 (new allocation)
Available:            $4,200.00 (decreased)
```

---

### Flow 2: Cash/Debit Purchase

**Transaction:** Buy groceries with debit card ($245.67)

```json
{
  "journal_entry_id": "je-001",
  "description": "Groceries - Whole Foods (debit card)",
  "entry_date": "2025-04-15",
  "distributions": [
    {
      "account_id": "1000-Checking",
      "account_type": "asset",
      "flow_direction": "from",
      "amount": 245.67,
      "multiplier": -1,
      "debit_credit": "Cr",
      "description": "Cash out"
    },
    {
      "account_id": "6300-Groceries-Expense",
      "account_type": "expense",
      "flow_direction": "to",
      "amount": 245.67,
      "multiplier": 1,
      "debit_credit": "Dr",
      "budget_envelope_id": "1500-Budget-Groceries",
      "description": "Grocery expense"
    }
  ]
}
```

**Effects:**
```
Checking Balance:     $5,000.00 → $4,754.33 (REAL money out)
Budget "Groceries":   $  800.00 → $  554.33 (virtual decrease)
Expense Account:      $    0.00 → $  245.67 (tracking actual spending)
Available:            $4,200.00 → $4,200.00 (unchanged - was pre-allocated)
```

**Key Point:** Budget envelope decreases when expense is recorded, triggered by `budget_envelope_id` in the distribution.

---

### Flow 3: Credit Card Purchase

**Transaction:** Buy dinner on credit card ($87.50)

```json
{
  "journal_entry_id": "je-002",
  "description": "Dining - Italian Restaurant (credit card)",
  "entry_date": "2025-04-18",
  "distributions": [
    {
      "account_id": "2100-CreditCard-A",
      "account_type": "liability",
      "flow_direction": "from",
      "amount": 87.50,
      "multiplier": 1,
      "debit_credit": "Cr",
      "payment_envelope_id": "1600-Payment-CreditCard-A",
      "description": "Credit card balance increases"
    },
    {
      "account_id": "6310-Dining-Expense",
      "account_type": "expense",
      "flow_direction": "to",
      "amount": 87.50,
      "multiplier": 1,
      "debit_credit": "Dr",
      "budget_envelope_id": "1501-Budget-Dining",
      "description": "Dining expense"
    }
  ]
}
```

**Effects:**
```
Checking Balance:           $4,754.33 (unchanged - haven't paid yet!)
Credit Card Liability:      $    0.00 → $   87.50 (debt increases)
Budget "Dining":            $  300.00 → $  212.50 (virtual decrease)
Payment "Credit Card A":    $    0.00 → $   87.50 (virtual increase)
Expense Account:            $    0.00 → $   87.50 (tracking spending)
Available:                  $4,200.00 (unchanged - was pre-allocated)
```

**Key Point:**
- Budget envelope decreases (spending tracked)
- Payment envelope increases (obligation reserved)
- Bank unchanged (cash not spent yet)

**The Virtual Movement:**
Money "moved" from Budget Envelope → Payment Envelope, but it's still physically in the bank!

---

### Flow 4: Pay Credit Card

**Scenario:**
Credit Card has charges totaling $1,500 from various budget categories:
- Groceries: $600
- Dining: $400
- Gas: $300
- Entertainment: $200

Payment Envelope "Credit Card A" has accumulated $1,500 from those purchases.

**Transaction:** Pay credit card bill

```json
{
  "journal_entry_id": "je-cc-payment",
  "description": "Credit Card A - Monthly Payment",
  "entry_date": "2025-05-01",
  "distributions": [
    {
      "account_id": "1000-Checking",
      "account_type": "asset",
      "flow_direction": "from",
      "amount": 1500.00,
      "multiplier": -1,
      "debit_credit": "Cr",
      "description": "Cash payment to credit card"
    },
    {
      "account_id": "2100-CreditCard-A",
      "account_type": "liability",
      "flow_direction": "to",
      "amount": 1500.00,
      "multiplier": -1,
      "debit_credit": "Dr",
      "payment_envelope_id": "1600-Payment-CreditCard-A",
      "description": "Pay down credit card balance"
    }
  ]
}
```

**Effects:**
```
Checking Balance:           $4,754.33 → $3,254.33 (REAL money out)
Credit Card Liability:      $1,500.00 → $    0.00 (debt paid off)
Payment "Credit Card A":    $1,500.00 → $    0.00 (virtual decrease)
Budget Envelopes:           (unchanged - already decreased when purchases made)
Available:                  $4,200.00 → $4,200.00 (unchanged)
```

**Key Point:** Payment envelope is decremented by the `payment_envelope_id` reference in the distribution.

---

### Summary: Three Transaction Types

| Type | FROM Account | TO Account | Budget Effect | Payment Effect | Cash Effect |
|------|-------------|------------|---------------|----------------|-------------|
| **Cash Purchase** | Bank | Expense | Decrease | None | Immediate decrease |
| **Credit Purchase** | Liability | Expense | Decrease | Increase | No change (yet) |
| **Pay Liability** | Bank | Liability | None | Decrease | Decrease |

---

## Data Models

### BudgetEnvelope

```json
{
  "budget_envelope_id": "1500",
  "envelope_name": "Groceries",
  "envelope_type": "budget",

  "linked_bank_account_id": "1000",
  "linked_expense_accounts": ["6300", "6301", "6302"],

  "monthly_allocation": 800.00,
  "current_balance": 554.33,

  "period_start": "2025-04-01",
  "period_end": "2025-04-30",
  "period_label": "2025-04",

  "rollover_policy": "accumulate",
  "rollover_cap": 1600.00,

  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-04-15T14:30:00Z"
}
```

**Fields:**
- `budget_envelope_id`: Unique identifier (e.g., "1500", "1501")
- `envelope_name`: Display name
- `envelope_type`: Always "budget" for budget envelopes
- `linked_bank_account_id`: Where the REAL money sits (e.g., "1000-Checking")
- `linked_expense_accounts`: Array of expense account IDs that use this budget
- `monthly_allocation`: Default amount to allocate each month
- `current_balance`: Current virtual balance (how much is left)
- `period_start/end`: Current budget period
- `rollover_policy`: "accumulate", "reset", or "cap"
- `rollover_cap`: Maximum balance if using "cap" policy

---

### PaymentEnvelope

```json
{
  "payment_envelope_id": "1600",
  "envelope_name": "Credit Card A Payment",
  "envelope_type": "payment",

  "linked_bank_account_id": "1000",
  "linked_liability_account_id": "2100",

  "current_balance": 245.67,

  "payment_due_date": "2025-05-01",
  "minimum_payment": 35.00,
  "auto_pay_enabled": false,

  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-04-18T16:45:00Z"
}
```

**Fields:**
- `payment_envelope_id`: Unique identifier (e.g., "1600", "1601")
- `envelope_name`: Display name
- `envelope_type`: Always "payment" for payment envelopes
- `linked_bank_account_id`: Where the REAL money sits
- `linked_liability_account_id`: The liability this envelope tracks
- `current_balance`: Amount reserved for paying this liability
- `payment_due_date`: When payment is due
- `minimum_payment`: Minimum payment amount
- `auto_pay_enabled`: Whether to auto-generate payment transactions

---

### BudgetAllocation

```json
{
  "allocation_id": "alloc-2025-04-groceries",
  "allocation_date": "2025-04-01",

  "bank_account_id": "1000",
  "budget_envelope_id": "1500",

  "allocated_amount": 800.00,
  "allocation_type": "monthly_funding",

  "notes": "April grocery budget",
  "created_at": "2025-04-01T00:00:00Z",
  "created_by": "system"
}
```

**Purpose:** Records when money is allocated to a budget envelope.

**This is NOT a journal entry!** It's metadata that affects the virtual envelope balance.

---

### Distribution (Enhanced)

```json
{
  "distribution_id": "dist-001",
  "account_id": "6300-Groceries-Expense",
  "account_type": "expense",
  "flow_direction": "to",
  "amount": 245.67,
  "multiplier": 1,
  "debit_credit": "Dr",

  "budget_envelope_id": "1500",
  "payment_envelope_id": null,

  "description": "Grocery expense",
  "memo": "Whole Foods",
  "cost_center": null,
  "department": null
}
```

**New Fields:**
- `budget_envelope_id`: If present, this distribution affects a budget envelope
- `payment_envelope_id`: If present, this distribution affects a payment envelope

**Processing Logic:**

When a transaction is posted:
1. Apply the distribution to the actual account (update ledger, balance)
2. If `budget_envelope_id` exists:
   - Decrease budget envelope by `amount`
3. If `payment_envelope_id` exists:
   - If FROM a liability: Increase payment envelope by `amount`
   - If TO a liability: Decrease payment envelope by `amount`

---

### EnvelopeTransaction

```json
{
  "envelope_transaction_id": "env-txn-001",
  "envelope_id": "1500",
  "envelope_type": "budget",

  "transaction_date": "2025-04-15",
  "amount": -245.67,
  "balance_before": 800.00,
  "balance_after": 554.33,

  "journal_entry_id": "je-001",
  "distribution_id": "dist-001",

  "description": "Groceries - Whole Foods",
  "created_at": "2025-04-15T14:30:00Z"
}
```

**Purpose:** Audit trail of all changes to envelope balances.

Similar to AccountLedger but for virtual envelopes.

---

## Display & Reporting

### Bank Account Display

```
┌──────────────────────────────────────────────────────────┐
│ Checking Account (1000)                                  │
├──────────────────────────────────────────────────────────┤
│ Bank Balance:                                 $5,000.00  │
│                                                           │
│ Budget Allocations:                                      │
│   Groceries                    $ 554.33                  │
│   Dining                       $ 212.50                  │
│   Gas                          $ 148.00                  │
│   Entertainment                $ 150.00                  │
│   Utilities                    $ 400.00                  │
│                              ─────────────                │
│ Budget Allocated:                            -$1,464.83  │
│                                                           │
│ Payment Obligations:                                     │
│   Credit Card A                $ 333.17                  │
│   Credit Card B                $   0.00                  │
│   Auto Loan                    $ 345.00                  │
│                              ─────────────                │
│ Payment Reserved:                            -$  678.17  │
│ ═════════════════════════════════════════════════════    │
│ Total Allocated:                             -$2,143.00  │
│ Available to Allocate:                        $2,857.00  │
└──────────────────────────────────────────────────────────┘
```

**Key Formula:**
```
Available = Bank Balance - Budget Allocated - Payment Reserved
```

---

### Budget Envelope Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│ Budget Envelopes - April 2025                                       │
├─────────────────────────────────────────────────────────────────────┤
│ Envelope          Allocated    Spent    Remaining    %Used  Status  │
├─────────────────────────────────────────────────────────────────────┤
│ Groceries         $  800.00  $ 245.67  $  554.33    31%    ✅ OK   │
│ Dining            $  300.00  $  87.50  $  212.50    29%    ✅ OK   │
│ Gas               $  200.00  $  52.00  $  148.00    26%    ✅ OK   │
│ Entertainment     $  150.00  $   0.00  $  150.00     0%    ✅ OK   │
│ Utilities         $  400.00  $   0.00  $  400.00     0%    ✅ OK   │
├─────────────────────────────────────────────────────────────────────┤
│ TOTALS           $1,850.00  $ 385.17  $1,464.83    21%             │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Payment Envelope Dashboard

```
┌──────────────────────────────────────────────────────────────────────┐
│ Payment Obligations - Current                                        │
├──────────────────────────────────────────────────────────────────────┤
│ Payment For          Balance    Reserved    Short/Over    Due Date   │
├──────────────────────────────────────────────────────────────────────┤
│ Credit Card A        $ 333.17   $ 333.17    $   0.00     2025-05-01 │
│ Credit Card B        $   0.00   $   0.00    $   0.00     2025-05-01 │
│ Auto Loan            $ 345.00   $ 345.00    $   0.00     2025-05-03 │
│ Mortgage             $1,439.00  $1,439.00   $   0.00     2025-05-01 │
├──────────────────────────────────────────────────────────────────────┤
│ TOTALS              $2,117.17   $2,117.17   $   0.00                │
└──────────────────────────────────────────────────────────────────────┘
```

**Validation:**
```
Payment Envelope Balance should equal Liability Balance
(for tracked liabilities)
```

---

### Spending by Budget Category (Month-to-Date)

```
┌──────────────────────────────────────────────────────────┐
│ Spending Report - April 2025 (MTD)                       │
├──────────────────────────────────────────────────────────┤
│ Category          Budget    Actual    Variance    %Used  │
├──────────────────────────────────────────────────────────┤
│ Groceries         $ 800   $ 245.67   $ 554.33      31%  │
│ Dining            $ 300   $  87.50   $ 212.50      29%  │
│ Gas               $ 200   $  52.00   $ 148.00      26%  │
│ Entertainment     $ 150   $   0.00   $ 150.00       0%  │
│ Utilities         $ 400   $   0.00   $ 400.00       0%  │
├──────────────────────────────────────────────────────────┤
│ TOTALS           $1,850  $ 385.17   $1,464.83      21%  │
└──────────────────────────────────────────────────────────┘

Days Elapsed: 15 of 30 (50%)
Average Daily Spend: $25.68
Projected Month End: $770.33
On Track: ✅ Yes (below 50% usage at mid-month)
```

---

## Implementation Notes

### Transaction Posting Logic

```python
def post_journal_entry(journal_entry):
    """
    Post a journal entry and update virtual envelopes.
    """

    # Step 1: Validate entry is balanced
    if not journal_entry.is_balanced():
        raise ValueError("Entry not balanced")

    # Step 2: Post distributions to actual accounts (ledger)
    for dist in journal_entry.distributions:
        post_to_ledger(dist)
        update_account_balance(dist)

    # Step 3: Update budget envelopes
    for dist in journal_entry.distributions:
        if dist.budget_envelope_id:
            update_budget_envelope(
                envelope_id=dist.budget_envelope_id,
                amount=-dist.amount,  # Always decreases
                journal_entry_id=journal_entry.journal_entry_id,
                distribution_id=dist.distribution_id
            )

    # Step 4: Update payment envelopes
    for dist in journal_entry.distributions:
        if dist.payment_envelope_id:
            # Determine if increase or decrease
            if dist.account_type == "liability":
                if dist.flow_direction == "from":
                    # Liability increasing (credit card charge)
                    change_amount = +dist.amount
                else:
                    # Liability decreasing (payment)
                    change_amount = -dist.amount

                update_payment_envelope(
                    envelope_id=dist.payment_envelope_id,
                    amount=change_amount,
                    journal_entry_id=journal_entry.journal_entry_id,
                    distribution_id=dist.distribution_id
                )

    # Step 5: Create envelope transaction records (audit trail)
    create_envelope_transactions(journal_entry)

    return {"success": True, "journal_entry_id": journal_entry.journal_entry_id}
```

---

### Monthly Budget Reset/Rollover

```python
def process_month_end_budget_reset(period_end_date):
    """
    Process month-end for all budget envelopes.
    """

    budget_envelopes = get_all_active_budget_envelopes()

    for envelope in budget_envelopes:
        current_balance = envelope.current_balance

        if envelope.rollover_policy == "reset":
            # Zero out, money goes back to available
            new_balance = 0

        elif envelope.rollover_policy == "accumulate":
            # Keep current balance, add next month's allocation
            new_balance = current_balance

        elif envelope.rollover_policy == "cap":
            # Cap at maximum
            new_balance = min(current_balance, envelope.rollover_cap)

        # Record the reset/rollover
        record_budget_period_end(
            envelope_id=envelope.budget_envelope_id,
            period_end=period_end_date,
            ending_balance=current_balance,
            rollover_amount=new_balance,
            policy=envelope.rollover_policy
        )

        # Set up for next period
        envelope.period_start = period_end_date + timedelta(days=1)
        envelope.period_end = get_last_day_of_month(envelope.period_start)
        envelope.current_balance = new_balance
        envelope.save()
```

---

### Expected Balance Calculation (Future Projection)

```python
def get_expected_balance(account_id, target_date):
    """
    Calculate expected balance for any account on a future date.

    This works by:
    1. Getting current actual balance
    2. Projecting all scheduled recurring transactions
    3. Including any future-dated transactions already entered
    """

    # Get current actual balance
    current_balance = get_current_account_balance(account_id)
    last_transaction_date = get_last_transaction_date(account_id)

    # Get all scheduled recurring transactions
    scheduled_transactions = generate_scheduled_transactions(
        start_date=last_transaction_date,
        end_date=target_date
    )

    # Get future transactions already entered
    future_transactions = get_future_transactions(
        account_id=account_id,
        start_date=last_transaction_date,
        end_date=target_date
    )

    # Project balance forward
    projected_balance = current_balance

    all_transactions = sorted(
        scheduled_transactions + future_transactions,
        key=lambda t: t.entry_date
    )

    for txn in all_transactions:
        for dist in txn.distributions:
            if dist.account_id == account_id:
                impact = dist.amount * dist.multiplier
                projected_balance += impact

    return {
        "account_id": account_id,
        "target_date": target_date,
        "current_balance": current_balance,
        "projected_balance": projected_balance,
        "net_change": projected_balance - current_balance,
        "transaction_count": len(all_transactions)
    }
```

---

### Budget Allocation Validation

```python
def validate_budget_allocation(bank_account_id, allocation_amount):
    """
    Ensure we don't over-allocate money that doesn't exist.
    """

    # Get bank balance
    bank_balance = get_account_balance(bank_account_id)

    # Get current allocations
    budget_allocated = sum_budget_envelope_balances(bank_account_id)
    payment_reserved = sum_payment_envelope_balances(bank_account_id)

    # Calculate available
    available = bank_balance - budget_allocated - payment_reserved

    # Validate
    if allocation_amount > available:
        raise ValueError(
            f"Cannot allocate ${allocation_amount:.2f}. "
            f"Only ${available:.2f} available. "
            f"(Bank: ${bank_balance:.2f}, "
            f"Budget: ${budget_allocated:.2f}, "
            f"Payment: ${payment_reserved:.2f})"
        )

    return True
```

---

## Key Design Principles

### 1. Budgets are for Expenses Only (and Essential for Forecasting)

- Budget envelopes only track expense categories
- Budget envelopes are CRITICAL for forecasting future expected balances on any date
  - Current recurring transactions show what WILL happen (mortgage, utilities)
  - Budget allocations show what COULD happen (groceries, dining, discretionary)
  - Together they provide complete future balance projections
- Revenue, asset changes, liability payments use different mechanisms (recurring transactions, future-dated entries)

### 2. Virtual Not Physical

- No money "moves" between envelopes and bank accounts
- Envelopes are metadata/accumulators
- Bank account balance is always the real cash amount

### 3. Dual Envelope System

- **Budget Envelopes**: Track spending categories (decrease when expense recorded)
- **Payment Envelopes**: Track liability obligations (increase with debt, decrease with payment)

### 4. The Fundamental Equation

```
Bank Balance = Budget Allocated + Payment Reserved + Available
```

This must ALWAYS be true.

### 5. Reconciliation at Payment Time

When paying a liability:
- Bank account decreases (real cash out)
- Liability decreases (debt paid)
- Payment envelope decreases (reservation released)
- Budget envelopes unchanged (already decreased when expense recorded)

### 6. Prevents Double-Spending

Money allocated to budgets or reserved for payments cannot be spent twice because:
- "Available" calculation subtracts both allocations
- Visual displays show committed vs available
- Validation prevents over-allocation

---

## Open Questions / Future Decisions

### 1. Budget Overspending
**Question:** What happens if an expense exceeds the budget envelope balance?

**Options:**
- A) Allow negative balance (warn user)
- B) Block transaction (require reallocation first)
- C) Auto-pull from "Available" with warning

**Decision:** TBD

---

### 2. Partial Payments
**Question:** What if you only pay part of a credit card balance?

**Example:**
- Credit Card Balance: $1,500
- Payment Envelope: $1,500
- You pay: $500

**Options:**
- A) Proportionally reduce all budget contributions
- B) User manually specifies which budgets to "release"
- C) FIFO/LIFO order of charges

**Decision:** TBD

---

### 3. Split Transactions
**Question:** How to handle expense split across multiple budgets?

**Example:** Shopping trip with groceries + household items

**Options:**
- A) Single transaction, multiple expense distributions with different budget_envelope_ids
- B) Require splitting into separate transactions

**Decision:** TBD

---

### 4. Monthly Reset Timing
**Question:** When does budget reset happen?

**Options:**
- A) Midnight on 1st of month (automatic)
- B) Manual trigger by user
- C) Batch process (run once daily)

**Decision:** TBD

---

### 5. Income Allocation
**Question:** How to allocate incoming money to budgets?

**Options:**
- A) Manual allocation after deposit
- B) Automatic allocation based on template
- C) Hybrid (auto-allocate recurring income, manual for other)

**Decision:** TBD

---

## Implementation Phases

### Phase 1: Core Virtual Envelopes (MVP)
1. ✅ BudgetEnvelope model
2. ✅ PaymentEnvelope model
3. ✅ BudgetAllocation model
4. ✅ Enhanced Distribution with envelope references
5. ✅ Transaction posting logic to update envelopes
6. ✅ Basic validation (prevent over-allocation)

### Phase 2: Display & Reporting
7. ✅ Bank account display with allocations
8. ✅ Budget envelope dashboard
9. ✅ Payment envelope dashboard
10. ✅ Spending vs budget reports

### Phase 3: Automation
11. ✅ Auto-generate monthly budget allocations
12. ✅ Month-end reset/rollover processing
13. ✅ Budget from recurring transactions

### Phase 4: Forecasting
14. ✅ Expected balance calculation
15. ✅ Cash flow projections
16. ✅ "What-if" scenarios

### Phase 5: Advanced Features
17. ❓ Budget approval workflow
18. ❓ Budget templates (copy last year)
19. ❓ Budget alerts & notifications
20. ❓ Historical budget comparisons

---

## Related Documentation

- [FROM/TO Accounting System](./FROMTO_ACCOUNTING.md) - Details on the FROM/TO flow system
- [Transaction Models](../models/journal_entries.py) - Data models for journal entries
- [Test Data](../test_data/) - Sample 3-month dataset

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-01-08 | Initial design document created | Design Session |

---

**Status:** Ready for Implementation Review

