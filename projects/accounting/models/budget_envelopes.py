"""
Budget Envelope Models - Virtual Allocation Tracking

This module implements a virtual envelope budgeting system where money stays in
bank accounts but is "allocated" to virtual envelopes for tracking purposes.

KEY CONCEPTS:
1. Virtual Envelopes: Metadata accumulators, NOT physical accounts in Chart of Accounts
2. Money Never Moves: All cash stays in bank accounts; envelopes track allocations
3. Dual Envelope System:
   - Budget Envelopes: Track expense category allocations
   - Payment Envelopes: Track liability payment obligations
4. Fundamental Equation: Bank Balance = Budget Allocated + Payment Reserved + Available

BUDGET ENVELOPES:
- Purpose: Track spending by expense category (Groceries, Dining, Gas, etc.)
- Decrease when: Expense is recorded (regardless of payment method)
- Used for: Preventing overspending and forecasting future expenses

PAYMENT ENVELOPES:
- Purpose: Reserve money for future liability payments (Credit Cards, Loans)
- Increase when: Liability increases (charge on credit card)
- Decrease when: Liability is paid
- Used for: Ensuring cash is available to pay debts

TRANSACTION FLOW EXAMPLE - Credit Card Purchase:
1. Purchase groceries for $245.67 on credit card
2. Credit Card Liability: +$245.67 (FROM account, multiplier +1)
3. Grocery Expense: +$245.67 (TO account, multiplier +1)
4. Budget Envelope "Groceries": -$245.67 (virtual)
5. Payment Envelope "Credit Card A": +$245.67 (virtual)
6. Bank Balance: UNCHANGED (haven't paid yet)
7. Available: Reduced by 0 (budget decreased, payment increased equally)

FORECASTING:
Budget envelopes are CRITICAL for projecting future balances:
- Recurring transactions show what WILL happen (mortgage, utilities)
- Budget allocations show what COULD happen (groceries, discretionary)
- Together they provide complete future balance projections for any date
"""

import uuid
from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from .journal_entries import AccountType


class EnvelopeType(str, Enum):
    """Type of virtual envelope."""
    BUDGET = "budget"      # Expense category tracking
    PAYMENT = "payment"    # Liability payment tracking


class RolloverPolicy(str, Enum):
    """
    Policy for handling unused budget at period end.

    RESET: Zero out envelope, unused funds return to Available
    ACCUMULATE: Keep balance, add next period's allocation on top
    CAP: Keep balance up to a maximum limit, excess returns to Available
    """
    RESET = "reset"
    ACCUMULATE = "accumulate"
    CAP = "cap"


class BudgetEnvelope(BaseModel):
    """
    Virtual budget envelope for tracking expense category allocations.

    Budget envelopes are NOT accounts in the Chart of Accounts. They are
    metadata that tracks how much of your bank balance is "allocated" to
    different spending categories.

    Example:
        Envelope: "Groceries"
        - Monthly allocation: $800
        - Current balance: $345.23 (started at $800, spent $454.77)
        - Linked expense accounts: [6300-Grocery Stores, 6301-Farmers Markets]

    When an expense is recorded:
        - The linked Budget Envelope decreases by the expense amount
        - If using credit, a Payment Envelope increases simultaneously
        - Bank balance unchanged until payment is made
    """
    envelope_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Identification
    envelope_number: str  # e.g., "1500", "1510" (numbering like accounts but separate)
    envelope_name: str    # e.g., "Groceries", "Dining Out", "Gas & Auto"
    envelope_type: EnvelopeType = EnvelopeType.BUDGET

    # Categorization
    category: Optional[str] = None  # e.g., "Food & Dining", "Transportation"
    parent_envelope_id: Optional[str] = None  # For hierarchical budgets

    # Budget configuration
    monthly_allocation: float = 0.0  # How much to allocate each month
    is_active: bool = True
    rollover_policy: RolloverPolicy = RolloverPolicy.RESET
    rollover_cap: Optional[float] = None  # Max balance if using CAP policy

    # Current state (Virtual balance - NOT real money)
    current_balance: float = 0.0  # How much is currently allocated
    allocated_this_period: float = 0.0
    spent_this_period: float = 0.0

    # Period tracking
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    last_reset_date: Optional[date] = None

    # Display
    display_order: int = 0
    color_code: Optional[str] = None  # For UI display
    icon: Optional[str] = None
    description: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    def remaining_budget(self) -> float:
        """
        Get remaining budget for the current period.

        Returns: Current balance (positive means money still allocated)
        """
        return self.current_balance

    def spent_percentage(self) -> float:
        """
        Calculate what percentage of the monthly allocation has been spent.

        Returns: Percentage (0-100+)
        """
        if self.monthly_allocation == 0:
            return 0.0
        return (self.spent_this_period / self.monthly_allocation) * 100

    def is_overspent(self) -> bool:
        """Check if envelope has been overspent (balance is negative)."""
        return self.current_balance < 0

    def overspent_amount(self) -> float:
        """Get amount overspent (positive number if overspent, 0 otherwise)."""
        return abs(min(0, self.current_balance))

    def apply_monthly_allocation(self, allocation_date: date) -> float:
        """
        Apply monthly allocation to envelope based on rollover policy.

        Args:
            allocation_date: Date of the allocation

        Returns: Amount actually allocated
        """
        old_balance = self.current_balance

        if self.rollover_policy == RolloverPolicy.RESET:
            # Reset to monthly allocation
            self.current_balance = self.monthly_allocation
            amount_allocated = self.monthly_allocation

        elif self.rollover_policy == RolloverPolicy.ACCUMULATE:
            # Add to existing balance
            self.current_balance += self.monthly_allocation
            amount_allocated = self.monthly_allocation

        elif self.rollover_policy == RolloverPolicy.CAP:
            # Add but cap at maximum
            new_balance = self.current_balance + self.monthly_allocation
            if self.rollover_cap and new_balance > self.rollover_cap:
                self.current_balance = self.rollover_cap
                amount_allocated = self.rollover_cap - old_balance
            else:
                self.current_balance = new_balance
                amount_allocated = self.monthly_allocation
        else:
            amount_allocated = 0.0

        self.allocated_this_period = amount_allocated
        self.spent_this_period = 0.0
        self.last_reset_date = allocation_date
        self.updated_at = datetime.utcnow()

        return amount_allocated

    def record_expense(self, amount: float) -> float:
        """
        Decrease envelope balance when expense is recorded.

        Args:
            amount: Expense amount (positive)

        Returns: New balance after expense
        """
        self.current_balance -= amount
        self.spent_this_period += amount
        self.updated_at = datetime.utcnow()
        return self.current_balance

    def record_refund(self, amount: float) -> float:
        """
        Increase envelope balance when expense is refunded.

        Args:
            amount: Refund amount (positive)

        Returns: New balance after refund
        """
        self.current_balance += amount
        self.spent_this_period -= amount
        self.updated_at = datetime.utcnow()
        return self.current_balance

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class PaymentEnvelope(BaseModel):
    """
    Virtual payment envelope for tracking liability payment obligations.

    Payment envelopes track how much money should be "reserved" to pay
    upcoming liability obligations (credit cards, loans, etc.).

    Example:
        Envelope: "Credit Card A - Payment Reserve"
        - Linked liability: 2100-Credit-Card-A
        - Current balance: $1,245.67 (amount owed, reserved for payment)

    Flow:
        1. Charge $100 on credit card:
           - Credit Card Liability: +$100
           - Payment Envelope: +$100 (reserve cash)
        2. Pay credit card $500:
           - Bank Account: -$500
           - Credit Card Liability: -$500
           - Payment Envelope: -$500 (release reserved cash)
    """
    envelope_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Identification
    envelope_number: str  # e.g., "1600", "1610"
    envelope_name: str    # e.g., "Credit Card A - Payment Reserve"
    envelope_type: EnvelopeType = EnvelopeType.PAYMENT

    # Linked liability account
    linked_account_id: str  # The liability account this tracks (e.g., "2100-CreditCard-A")
    linked_account_name: Optional[str] = None

    # Current state (Virtual balance - NOT real money)
    current_balance: float = 0.0  # Amount reserved for payment

    # Categorization
    category: Optional[str] = None  # e.g., "Credit Cards", "Loans"

    # Configuration
    is_active: bool = True

    # Display
    display_order: int = 0
    color_code: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    def record_charge(self, amount: float) -> float:
        """
        Increase envelope when liability increases (charge made).

        Args:
            amount: Charge amount (positive)

        Returns: New balance after charge
        """
        self.current_balance += amount
        self.updated_at = datetime.utcnow()
        return self.current_balance

    def record_payment(self, amount: float) -> float:
        """
        Decrease envelope when liability is paid.

        Args:
            amount: Payment amount (positive)

        Returns: New balance after payment
        """
        self.current_balance -= amount
        self.updated_at = datetime.utcnow()
        return self.current_balance

    def record_credit(self, amount: float) -> float:
        """
        Decrease envelope when credit/refund is applied to liability.

        Args:
            amount: Credit amount (positive)

        Returns: New balance after credit
        """
        self.current_balance -= amount
        self.updated_at = datetime.utcnow()
        return self.current_balance

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class BudgetAllocation(BaseModel):
    """
    Record of a budget allocation event.

    Tracks when money is allocated to budget envelopes (typically monthly).
    This creates an audit trail of budget allocations over time.
    """
    allocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Source and destination
    source_account_id: str  # Bank account providing the money
    envelope_id: str        # Budget envelope receiving allocation
    envelope_type: EnvelopeType

    # Allocation details
    allocation_date: date
    amount: float
    period_label: str  # e.g., "2025-01", "2025-Q1"

    # Description
    description: Optional[str] = None
    notes: Optional[str] = None

    # Status
    is_automatic: bool = False  # True if from recurring allocation

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class EnvelopeTransaction(BaseModel):
    """
    Record of a virtual envelope balance change.

    Tracks every change to envelope balances, creating an audit trail.
    Links to the actual journal entry that triggered the change.
    """
    envelope_transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Envelope reference
    envelope_id: str
    envelope_type: EnvelopeType

    # Transaction reference
    journal_entry_id: Optional[str] = None  # Link to actual accounting transaction
    distribution_id: Optional[str] = None   # Link to specific distribution
    allocation_id: Optional[str] = None     # Link to budget allocation

    # Transaction details
    transaction_date: date
    transaction_type: str  # "expense", "refund", "charge", "payment", "allocation"

    # Balance impact
    amount: float  # Positive or negative
    balance_before: float
    balance_after: float

    # Description
    description: str
    reference: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class BankAccountView(BaseModel):
    """
    Display view showing bank balance breakdown with envelope allocations.

    This is a calculated view, not stored data. It shows:
    - Real bank balance
    - Virtual allocations (budgets + payments)
    - Available to allocate

    Formula: Bank Balance = Budget Allocated + Payment Reserved + Available
    """
    account_id: str
    account_name: str

    # Real money
    bank_balance: float  # Actual cash in bank

    # Virtual allocations
    budget_allocated: float    # Sum of all budget envelope balances
    payment_reserved: float    # Sum of all payment envelope balances
    total_allocated: float     # budget_allocated + payment_reserved

    # Available
    available_to_allocate: float  # bank_balance - total_allocated

    # As of date
    as_of_date: date

    # Breakdown by envelope
    budget_envelopes: List[Dict[str, Any]] = Field(default_factory=list)
    # Each: {envelope_id, envelope_name, balance}

    payment_envelopes: List[Dict[str, Any]] = Field(default_factory=list)
    # Each: {envelope_id, envelope_name, balance, linked_account}

    def is_balanced(self) -> bool:
        """
        Verify that Bank = Budget + Payment + Available.

        Returns: True if equation holds (within $0.01)
        """
        calculated = self.budget_allocated + self.payment_reserved + self.available_to_allocate
        return abs(self.bank_balance - calculated) < 0.01

    def validate_equation(self) -> Dict[str, float]:
        """
        Validate fundamental equation and return breakdown.

        Returns: Dict with calculation details
        """
        calculated_total = self.budget_allocated + self.payment_reserved + self.available_to_allocate
        difference = self.bank_balance - calculated_total

        return {
            "bank_balance": self.bank_balance,
            "budget_allocated": self.budget_allocated,
            "payment_reserved": self.payment_reserved,
            "available_to_allocate": self.available_to_allocate,
            "calculated_total": calculated_total,
            "difference": difference,
            "is_balanced": abs(difference) < 0.01
        }

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class BudgetPeriodSummary(BaseModel):
    """
    Summary of budget performance for a period.

    Shows how well spending tracked to budget allocations.
    """
    period_label: str  # e.g., "2025-01"
    period_start: date
    period_end: date

    # Overall totals
    total_allocated: float
    total_spent: float
    total_remaining: float

    # By envelope
    envelope_details: List[Dict[str, Any]] = Field(default_factory=list)
    # Each: {envelope_id, name, allocated, spent, remaining, percent_used}

    # Counts
    envelopes_on_track: int = 0
    envelopes_overspent: int = 0

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
