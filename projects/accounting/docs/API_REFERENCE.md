# Accounting Module API Reference

**Date:** 2025-01-08
**Module:** LiMOS Accounting
**Version:** 1.0

---

## Table of Contents

1. [Models](#models)
2. [Services](#services)
3. [Enums](#enums)
4. [Examples](#examples)

---

## Models

### Journal Entries

#### `Distribution`
Single line item in a journal entry representing money flow.

**Fields:**
```python
distribution_id: str              # Auto-generated UUID
account_id: str                   # Account being affected
account_type: AccountType         # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
flow_direction: FlowDirection     # FROM (out) or TO (in)
amount: float                     # Always positive
multiplier: int                   # +1 or -1 (auto-calculated)
debit_credit: DebitCredit         # "Dr" or "Cr" (auto-calculated)
description: Optional[str]
budget_envelope_id: Optional[str] # Links to budget envelope
payment_envelope_id: Optional[str]# Links to payment envelope
status: DistributionStatus        # PENDING, POSTED, VOID
created_at: datetime
updated_at: datetime
```

**Methods:**
```python
calculate_balance_impact() -> float
    # Returns: amount × multiplier

calculate_multiplier(account_type, flow_direction) -> int
    # Static method: Calculate multiplier from account type and flow

calculate_debit_credit_indicator() -> DebitCredit
    # Calculate "Dr" or "Cr" from multiplier and account type

get_debit_amount() -> float
    # Returns amount if Dr, 0 if Cr

get_credit_amount() -> float
    # Returns amount if Cr, 0 if Dr
```

**Example:**
```python
dist = Distribution(
    account_id="1000-Cash",
    account_type=AccountType.ASSET,
    flow_direction=FlowDirection.FROM,
    amount=500.00,
    multiplier=-1,  # Calculated: Asset + FROM = -1
    debit_credit=DebitCredit.CREDIT  # Calculated: Asset + (-1) = Cr
)
print(dist.calculate_balance_impact())  # -500.00
```

---

#### `JournalEntry`
Container for distributions, enforces double-entry balancing.

**Fields:**
```python
journal_entry_id: str              # Auto-generated UUID
entry_number: Optional[str]        # e.g., "JE-2025-001"
entry_type: JournalEntryType       # STANDARD, ADJUSTING, CLOSING, etc.
entry_date: date
posting_date: Optional[date]
distributions: List[Distribution]
description: str
status: JournalEntryStatus         # DRAFT, PENDING, POSTED, VOID
created_at: datetime
posted_at: Optional[datetime]
```

**Methods:**
```python
is_balanced() -> bool
    # Check if FROM total == TO total

get_balance_total() -> float
    # FROM total - TO total (should be 0)

add_distribution(account_id, account_type, flow_direction, amount, **kwargs) -> Distribution
    # Add distribution with auto-calculated multiplier

get_from_distributions() -> List[Distribution]
    # Get all FROM (outflow) distributions

get_to_distributions() -> List[Distribution]
    # Get all TO (inflow) distributions

get_total_debits() -> float
    # Sum of debit amounts

get_total_credits() -> float
    # Sum of credit amounts

is_balanced_traditional() -> bool
    # Check if debits == credits

format_t_account() -> str
    # Format as traditional T-account display

create_ledger_entries(account_balances: Dict) -> List[AccountLedger]
    # Create ledger entries with running balances
```

**Example:**
```python
entry = JournalEntry(
    entry_date=date(2025, 1, 15),
    description="Pay vendor"
)

entry.add_distribution(
    account_id="1000-Cash",
    account_type=AccountType.ASSET,
    flow_direction=FlowDirection.FROM,
    amount=500.00
)

entry.add_distribution(
    account_id="2000-AccountsPayable",
    account_type=AccountType.LIABILITY,
    flow_direction=FlowDirection.TO,
    amount=500.00
)

print(entry.is_balanced())  # True
print(entry.get_total_debits())  # 500.00
print(entry.get_total_credits())  # 500.00
```

---

#### `ChartOfAccounts`
Account definition in the chart of accounts.

**Fields:**
```python
account_id: str                    # Auto-generated UUID
account_number: str                # e.g., "1000", "6300"
account_name: str                  # e.g., "Cash", "Groceries"
account_type: AccountType
parent_account_id: Optional[str]   # For hierarchical accounts
budget_envelope_id: Optional[str]  # For expense accounts
payment_envelope_id: Optional[str] # For liability accounts
current_balance: float
opening_balance: float
is_active: bool
created_at: datetime
```

**Methods:**
```python
get_normal_balance_type() -> str
    # Returns "Debit" or "Credit"
```

**Example:**
```python
account = ChartOfAccounts(
    account_number="6300",
    account_name="Grocery Stores",
    account_type=AccountType.EXPENSE,
    budget_envelope_id="1500-Groceries",
    opening_balance=0.0
)
print(account.get_normal_balance_type())  # "Debit"
```

---

#### `AccountBalance`
Period balance summary for an account.

**Fields:**
```python
balance_id: str
account_id: str
account_number: str
account_name: str
account_type: AccountType
period_start: date
period_end: date
period_label: str                  # e.g., "2025-01"
opening_balance: float
total_from_amount: float           # Money OUT
total_to_amount: float             # Money IN
transaction_count: int
total_debits: float
total_credits: float
net_change: float
closing_balance: float
is_reconciled: bool
```

**Methods:**
```python
calculate_closing_balance() -> float
    # Calculate from opening + activity

verify_balance() -> bool
    # Verify closing matches calculated
```

---

#### `AccountLedger`
Transaction-level detail with running balance.

**Fields:**
```python
ledger_entry_id: str
account_id: str
journal_entry_id: str
distribution_id: str
transaction_date: date
posting_date: date
description: str
flow_direction: FlowDirection
amount: float
debit_credit: DebitCredit
debit_amount: float
credit_amount: float
multiplier: int
balance_impact: float              # amount × multiplier
balance_before: float
balance_after: float
posted_at: datetime
```

---

### Budget Envelopes

#### `BudgetEnvelope`
Virtual envelope for tracking expense category budgets.

**Fields:**
```python
envelope_id: str
envelope_number: str               # e.g., "1500"
envelope_name: str                 # e.g., "Groceries"
envelope_type: EnvelopeType        # BUDGET
category: Optional[str]
monthly_allocation: float
rollover_policy: RolloverPolicy    # RESET, ACCUMULATE, CAP
rollover_cap: Optional[float]
current_balance: float             # Virtual balance
allocated_this_period: float
spent_this_period: float
period_start: Optional[date]
period_end: Optional[date]
is_active: bool
```

**Methods:**
```python
remaining_budget() -> float
    # Returns current_balance

spent_percentage() -> float
    # (spent / monthly_allocation) × 100

is_overspent() -> bool
    # True if current_balance < 0

overspent_amount() -> float
    # Abs(min(0, current_balance))

apply_monthly_allocation(allocation_date: date) -> float
    # Apply allocation based on rollover policy

record_expense(amount: float) -> float
    # Decrease balance, return new balance

record_refund(amount: float) -> float
    # Increase balance, return new balance
```

**Example:**
```python
envelope = BudgetEnvelope(
    envelope_number="1500",
    envelope_name="Groceries",
    monthly_allocation=800.00,
    rollover_policy=RolloverPolicy.ACCUMULATE,
    current_balance=345.23
)

envelope.record_expense(125.50)
print(envelope.current_balance)  # 219.73
print(envelope.spent_this_period)  # 125.50
print(envelope.spent_percentage())  # 15.69%
```

---

#### `PaymentEnvelope`
Virtual envelope for tracking liability payment reserves.

**Fields:**
```python
envelope_id: str
envelope_number: str
envelope_name: str
envelope_type: EnvelopeType        # PAYMENT
linked_account_id: str             # Liability account ID
current_balance: float             # Amount reserved
is_active: bool
```

**Methods:**
```python
record_charge(amount: float) -> float
    # Increase reserve when liability increases

record_payment(amount: float) -> float
    # Decrease reserve when liability is paid

record_credit(amount: float) -> float
    # Decrease reserve when credit/refund applied
```

**Example:**
```python
envelope = PaymentEnvelope(
    envelope_number="1600",
    envelope_name="Credit Card A - Payment Reserve",
    linked_account_id="2100-CreditCard-A",
    current_balance=1245.67
)

envelope.record_charge(150.00)
print(envelope.current_balance)  # 1395.67

envelope.record_payment(500.00)
print(envelope.current_balance)  # 895.67
```

---

#### `BudgetAllocation`
Record of a budget allocation event.

**Fields:**
```python
allocation_id: str
source_account_id: str             # Bank account
envelope_id: str
envelope_type: EnvelopeType
allocation_date: date
amount: float
period_label: str                  # e.g., "2025-01"
description: Optional[str]
is_automatic: bool
created_at: datetime
```

---

#### `EnvelopeTransaction`
Audit trail of envelope balance changes.

**Fields:**
```python
envelope_transaction_id: str
envelope_id: str
envelope_type: EnvelopeType
journal_entry_id: Optional[str]
distribution_id: Optional[str]
allocation_id: Optional[str]
transaction_date: date
transaction_type: str              # "expense", "refund", "charge", "payment", "allocation"
amount: float                      # Positive or negative
balance_before: float
balance_after: float
description: str
created_at: datetime
```

---

#### `BankAccountView`
Display view of bank balance with envelope breakdown.

**Fields:**
```python
account_id: str
account_name: str
bank_balance: float                # Real cash
budget_allocated: float            # Sum of budget envelopes
payment_reserved: float            # Sum of payment envelopes
total_allocated: float             # budget + payment
available_to_allocate: float       # bank - total_allocated
as_of_date: date
budget_envelopes: List[Dict]
payment_envelopes: List[Dict]
```

**Methods:**
```python
is_balanced() -> bool
    # Verify Bank = Budget + Payment + Available

validate_equation() -> Dict
    # Return detailed breakdown and validation
```

**Example:**
```python
view = BankAccountView(
    account_id="1000",
    account_name="Checking",
    bank_balance=12500.00,
    budget_allocated=2345.67,
    payment_reserved=1899.00,
    total_allocated=4244.67,
    available_to_allocate=8255.33,
    as_of_date=date.today(),
    budget_envelopes=[...],
    payment_envelopes=[...]
)

print(view.is_balanced())  # True
validation = view.validate_equation()
print(validation['difference'])  # 0.00
```

---

## Services

### EnvelopeService

Core business logic for virtual envelope management.

#### Constructor
```python
envelope_service = EnvelopeService()
```

---

#### `post_journal_entry(journal_entry: JournalEntry) -> List[EnvelopeTransaction]`

Post a journal entry and update envelope balances.

**Args:**
- `journal_entry`: JournalEntry to post

**Returns:**
- List of EnvelopeTransaction records created

**Example:**
```python
entry = JournalEntry(...)
envelope_txns = envelope_service.post_journal_entry(entry)
for txn in envelope_txns:
    print(f"Envelope {txn.envelope_id}: {txn.balance_before} → {txn.balance_after}")
```

---

#### `apply_monthly_allocations(source_account_id: str, allocation_date: date, period_label: str) -> List[BudgetAllocation]`

Apply monthly allocations to all active budget envelopes.

**Args:**
- `source_account_id`: Bank account providing funds
- `allocation_date`: Date of allocation
- `period_label`: Period identifier (e.g., "2025-01")

**Returns:**
- List of BudgetAllocation records

**Example:**
```python
allocations = envelope_service.apply_monthly_allocations(
    source_account_id="1000-Cash",
    allocation_date=date(2025, 2, 1),
    period_label="2025-02"
)
print(f"Allocated to {len(allocations)} envelopes")
```

---

#### `validate_allocation(bank_account_id: str, allocation_amount: float, current_bank_balance: float) -> Tuple[bool, Optional[str]]`

Validate that allocation won't exceed available funds.

**Args:**
- `bank_account_id`: Bank account
- `allocation_amount`: Amount to allocate
- `current_bank_balance`: Current bank balance

**Returns:**
- Tuple of (is_valid, error_message)

**Example:**
```python
is_valid, error = envelope_service.validate_allocation(
    bank_account_id="1000",
    allocation_amount=1500.00,
    current_bank_balance=5000.00
)
if not is_valid:
    print(error)
```

---

#### `validate_expense(budget_envelope_id: str, expense_amount: float, allow_overspend: bool = False) -> Tuple[bool, Optional[str]]`

Validate expense won't overspend budget.

**Args:**
- `budget_envelope_id`: Envelope to charge
- `expense_amount`: Expense amount
- `allow_overspend`: Allow exceeding budget

**Returns:**
- Tuple of (is_valid, warning_message)

**Example:**
```python
is_valid, warning = envelope_service.validate_expense(
    budget_envelope_id="1500-Groceries",
    expense_amount=950.00,
    allow_overspend=False
)
if not is_valid:
    print(f"Warning: {warning}")
```

---

#### `get_bank_account_view(account_id: str, account_name: str, bank_balance: float, as_of_date: date) -> BankAccountView`

Get complete bank account view with envelope breakdown.

**Args:**
- `account_id`: Bank account ID
- `account_name`: Account name
- `bank_balance`: Current balance
- `as_of_date`: Date for view

**Returns:**
- BankAccountView

**Example:**
```python
view = envelope_service.get_bank_account_view(
    account_id="1000",
    account_name="Main Checking",
    bank_balance=12500.00,
    as_of_date=date.today()
)
print(f"Available: ${view.available_to_allocate:,.2f}")
```

---

#### `get_total_budget_allocated() -> float`

Get sum of all budget envelope balances.

**Returns:**
- Total budget allocated

---

#### `get_total_payment_reserved() -> float`

Get sum of all payment envelope balances.

**Returns:**
- Total payment reserved

---

#### `forecast_envelope_balance(envelope_id: str, target_date: date, scheduled_expenses: List[Dict]) -> Dict`

Forecast budget envelope balance on future date.

**Args:**
- `envelope_id`: Budget envelope
- `target_date`: Date to forecast to
- `scheduled_expenses`: List of {date, amount, description}

**Returns:**
- Dict with forecast details

**Example:**
```python
forecast = envelope_service.forecast_envelope_balance(
    envelope_id="1500",
    target_date=date(2025, 3, 31),
    scheduled_expenses=[
        {"date": date(2025, 2, 15), "amount": 150.00, "description": "Groceries"}
    ]
)
print(f"Projected: ${forecast['projected_balance']:,.2f}")
```

---

#### `create_budget_envelope(envelope: BudgetEnvelope) -> BudgetEnvelope`

Create a new budget envelope.

---

#### `create_payment_envelope(envelope: PaymentEnvelope) -> PaymentEnvelope`

Create a new payment envelope.

---

#### `get_budget_envelope(envelope_id: str) -> Optional[BudgetEnvelope]`

Get budget envelope by ID.

---

#### `get_payment_envelope(envelope_id: str) -> Optional[PaymentEnvelope]`

Get payment envelope by ID.

---

#### `list_budget_envelopes(active_only: bool = True) -> List[BudgetEnvelope]`

List all budget envelopes.

---

#### `list_payment_envelopes(active_only: bool = True) -> List[PaymentEnvelope]`

List all payment envelopes.

---

## Enums

### `AccountType`
```python
ASSET = "asset"
LIABILITY = "liability"
EQUITY = "equity"
REVENUE = "revenue"
EXPENSE = "expense"
```

### `FlowDirection`
```python
FROM = "from"  # Money flowing OUT
TO = "to"      # Money flowing IN
```

### `DebitCredit`
```python
DEBIT = "Dr"
CREDIT = "Cr"
```

### `JournalEntryType`
```python
STANDARD = "standard"
ADJUSTING = "adjusting"
CLOSING = "closing"
REVERSING = "reversing"
RECURRING = "recurring"
```

### `JournalEntryStatus`
```python
DRAFT = "draft"
PENDING = "pending"
POSTED = "posted"
VOID = "void"
REVERSED = "reversed"
```

### `DistributionStatus`
```python
PENDING = "pending"
POSTED = "posted"
VOID = "void"
```

### `EnvelopeType`
```python
BUDGET = "budget"
PAYMENT = "payment"
```

### `RolloverPolicy`
```python
RESET = "reset"              # Zero out at month end
ACCUMULATE = "accumulate"    # Keep balance, add allocation
CAP = "cap"                  # Keep balance up to cap
```

---

## Examples

### Complete Transaction Workflow

```python
from datetime import date
from projects.accounting.models import (
    JournalEntry, ChartOfAccounts, BudgetEnvelope, PaymentEnvelope,
    AccountType, FlowDirection, RolloverPolicy
)
from projects.accounting.services.envelope_service import EnvelopeService

# 1. Setup
envelope_service = EnvelopeService()

# Create budget envelope
groceries_env = BudgetEnvelope(
    envelope_number="1500",
    envelope_name="Groceries",
    monthly_allocation=800.00,
    rollover_policy=RolloverPolicy.ACCUMULATE
)
envelope_service.create_budget_envelope(groceries_env)

# Create expense account linked to envelope
grocery_acct = ChartOfAccounts(
    account_number="6300",
    account_name="Grocery Stores",
    account_type=AccountType.EXPENSE,
    budget_envelope_id="1500"
)

# 2. Apply monthly allocation
envelope_service.apply_monthly_allocations(
    source_account_id="1000-Cash",
    allocation_date=date(2025, 1, 1),
    period_label="2025-01"
)

# 3. Check view before purchase
view_before = envelope_service.get_bank_account_view(
    account_id="1000",
    account_name="Checking",
    bank_balance=10000.00,
    as_of_date=date.today()
)
print(f"Before - Available: ${view_before.available_to_allocate:,.2f}")

# 4. Record expense
entry = JournalEntry(
    entry_date=date(2025, 1, 15),
    description="Whole Foods"
)
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
    amount=125.50,
    budget_envelope_id="1500"
)

envelope_txns = envelope_service.post_journal_entry(entry)
print(f"Updated {len(envelope_txns)} envelopes")

# 5. Check view after purchase
view_after = envelope_service.get_bank_account_view(
    account_id="1000",
    account_name="Checking",
    bank_balance=9874.50,  # 10000 - 125.50
    as_of_date=date.today()
)
print(f"After - Available: ${view_after.available_to_allocate:,.2f}")

# 6. Forecast future balance
forecast = envelope_service.forecast_envelope_balance(
    envelope_id="1500",
    target_date=date(2025, 3, 31),
    scheduled_expenses=[
        {"date": date(2025, 2, 15), "amount": 150.00, "description": "Groceries"},
        {"date": date(2025, 3, 15), "amount": 175.00, "description": "Groceries"}
    ]
)
print(f"Projected balance on 2025-03-31: ${forecast['projected_balance']:,.2f}")
```

---

## Error Handling

All services raise standard Python exceptions:

- `ValueError`: Invalid input parameters
- `KeyError`: Missing required data
- Validation methods return `(bool, Optional[str])` instead of raising exceptions

**Example:**
```python
try:
    envelope_service.post_journal_entry(entry)
except ValueError as e:
    print(f"Error: {e}")
```
