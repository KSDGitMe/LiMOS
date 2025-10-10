"""
Journal Entry & Distribution Models

Double-entry accounting using From/To flow instead of Debit/Credit.

ACCOUNTING EQUATION: Assets = Liabilities + Equity
Revenue increases Equity, Expenses decrease Equity

FLOW MECHANICS:
- FROM: Money flowing OUT of an account
- TO: Money flowing INTO an account

MULTIPLIER RULES by Account Type:
┌─────────────┬──────────────────┬──────────────────┬──────────┐
│ Account Type│ Normal Balance   │ FROM (outflow)   │ TO (inflow) │
├─────────────┼──────────────────┼──────────────────┼──────────┤
│ Asset       │ Debit (positive) │ -1 (decreases)   │ +1 (increases) │
│ Liability   │ Credit (negative)│ +1 (increases)   │ -1 (decreases) │
│ Equity      │ Credit (negative)│ +1 (increases)   │ -1 (decreases) │
│ Revenue     │ Credit (negative)│ +1 (increases)   │ -1 (decreases) │
│ Expense     │ Debit (positive) │ -1 (decreases)   │ +1 (increases) │
└─────────────┴──────────────────┴──────────────────┴──────────┘

BALANCING RULES:
In this FROM/TO system, entries are balanced when:
- Total FROM amounts = Total TO amounts
- The sum of (amount × multiplier) does NOT need to equal zero
- Both sides of a transaction can increase or decrease balances

EXAMPLES:
1. Pay vendor $100 (A/P decreases, Cash decreases):
   - Cash (Asset): FROM, multiplier -1, balance += 100 * -1 = -100 (decrease)
   - A/P (Liability): TO, multiplier -1, balance += 100 * -1 = -100 (decrease)
   - FROM total: $100, TO total: $100 ✓ Balanced

2. Receive payment $100 (A/R decreases, Cash increases):
   - A/R (Asset): FROM, multiplier -1, balance += 100 * -1 = -100 (decrease)
   - Cash (Asset): TO, multiplier +1, balance += 100 * 1 = +100 (increase)
   - FROM total: $100, TO total: $100 ✓ Balanced

3. Record sale $100 (Cash increases, Revenue increases):
   - Revenue (Revenue): FROM, multiplier +1, balance += 100 * 1 = +100 (increase)
   - Cash (Asset): TO, multiplier +1, balance += 100 * 1 = +100 (increase)
   - FROM total: $100, TO total: $100 ✓ Balanced

4. Record expense $100 (Expense increases, Cash decreases):
   - Cash (Asset): FROM, multiplier -1, balance += 100 * -1 = -100 (decrease)
   - Expense (Expense): TO, multiplier +1, balance += 100 * 1 = +100 (increase)
   - FROM total: $100, TO total: $100 ✓ Balanced
"""

import uuid
from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class AccountType(str, Enum):
    """
    Account types with their normal balance characteristics.

    Normal balance indicates whether the account typically has
    a positive (debit) or negative (credit) balance.
    """
    ASSET = "asset"  # Normal balance: Debit (positive)
    LIABILITY = "liability"  # Normal balance: Credit (negative)
    EQUITY = "equity"  # Normal balance: Credit (negative)
    REVENUE = "revenue"  # Normal balance: Credit (negative)
    EXPENSE = "expense"  # Normal balance: Debit (positive)


class FlowDirection(str, Enum):
    """
    Direction of money flow relative to an account.

    FROM: Money flowing OUT of the account
    TO: Money flowing INTO the account
    """
    FROM = "from"  # Outflow
    TO = "to"  # Inflow


class DistributionStatus(str, Enum):
    """Status of a distribution line item."""
    PENDING = "pending"
    POSTED = "posted"
    VOID = "void"


class DebitCredit(str, Enum):
    """Traditional accounting debit/credit indicator."""
    DEBIT = "Dr"
    CREDIT = "Cr"


class Distribution(BaseModel):
    """
    Single distribution line in a journal entry.

    Combines intuitive FROM/TO flow with traditional Debit/Credit accounting.
    - FROM/TO: User-friendly interface for data entry
    - debit_credit: Auto-calculated indicator (Dr/Cr) for traditional accounting
    - amount: Always positive
    """
    distribution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Account reference
    account_id: str
    account_type: AccountType

    # Flow direction and amount (User-friendly)
    flow_direction: FlowDirection  # FROM or TO
    amount: float = Field(gt=0, description="Always positive, direction determines effect")

    # Multiplier for balance calculation
    # This is calculated based on account_type + flow_direction
    multiplier: int = Field(description="Either 1 or -1")

    # Traditional accounting indicator (Auto-calculated from multiplier and account_type)
    debit_credit: DebitCredit = Field(description="Dr or Cr indicator")

    # Descriptive information
    description: Optional[str] = None
    memo: Optional[str] = None

    # Reference fields
    reference_id: Optional[str] = None  # External reference
    cost_center: Optional[str] = None
    department: Optional[str] = None
    project_id: Optional[str] = None

    # Virtual Envelope References (for budgeting)
    budget_envelope_id: Optional[str] = None   # Links expense to budget envelope
    payment_envelope_id: Optional[str] = None  # Links liability to payment envelope

    # Status
    status: DistributionStatus = DistributionStatus.PENDING

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def calculate_balance_impact(self) -> float:
        """
        Calculate the impact on the account balance.

        Returns: amount * multiplier
        Formula: new_balance = old_balance + (amount * multiplier)
        """
        return self.amount * self.multiplier

    def calculate_debit_credit_indicator(self) -> DebitCredit:
        """
        Calculate Dr/Cr indicator from multiplier and account type.

        Logic:
        - Assets & Expenses (Normal Debit accounts):
          - Multiplier +1 (increase) → Dr
          - Multiplier -1 (decrease) → Cr
        - Liabilities, Equity, Revenue (Normal Credit accounts):
          - Multiplier +1 (increase) → Cr
          - Multiplier -1 (decrease) → Dr

        Returns: DebitCredit.DEBIT or DebitCredit.CREDIT
        """
        if self.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            # Normal debit balance accounts
            return DebitCredit.DEBIT if self.multiplier == 1 else DebitCredit.CREDIT
        else:
            # Normal credit balance accounts (LIABILITY, EQUITY, REVENUE)
            return DebitCredit.CREDIT if self.multiplier == 1 else DebitCredit.DEBIT

    def get_debit_amount(self) -> float:
        """Get debit amount (amount if Dr, 0 if Cr)."""
        return self.amount if self.debit_credit == DebitCredit.DEBIT else 0.0

    def get_credit_amount(self) -> float:
        """Get credit amount (amount if Cr, 0 if Dr)."""
        return self.amount if self.debit_credit == DebitCredit.CREDIT else 0.0

    @staticmethod
    def calculate_multiplier(account_type: AccountType, flow_direction: FlowDirection) -> int:
        """
        Calculate the multiplier based on account type and flow direction.

        Rules:
        - Asset + TO = +1 (increase)
        - Asset + FROM = -1 (decrease)
        - Liability + TO = -1 (decrease)
        - Liability + FROM = +1 (increase)
        - Equity + TO = -1 (decrease)
        - Equity + FROM = +1 (increase)
        - Revenue + TO = -1 (decrease/return)
        - Revenue + FROM = +1 (increase/earn)
        - Expense + TO = +1 (increase)
        - Expense + FROM = -1 (decrease/refund)
        """
        if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            # Normal debit balance accounts
            return 1 if flow_direction == FlowDirection.TO else -1
        else:
            # Normal credit balance accounts (LIABILITY, EQUITY, REVENUE)
            return -1 if flow_direction == FlowDirection.TO else 1

    @validator('multiplier', always=True)
    def validate_multiplier(cls, v, values):
        """Validate that multiplier matches account_type and flow_direction."""
        if 'account_type' in values and 'flow_direction' in values:
            expected = cls.calculate_multiplier(
                values['account_type'],
                values['flow_direction']
            )
            if v != expected:
                raise ValueError(
                    f"Multiplier {v} doesn't match account_type {values['account_type']} "
                    f"and flow_direction {values['flow_direction']}. Expected {expected}"
                )
        return v

    @validator('debit_credit', always=True)
    def auto_calculate_debit_credit_indicator(cls, v, values):
        """Auto-calculate Dr/Cr indicator from multiplier and account_type."""
        if 'account_type' in values and 'multiplier' in values:
            account_type = values['account_type']
            multiplier = values['multiplier']

            if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                # Normal debit balance accounts
                return DebitCredit.DEBIT if multiplier == 1 else DebitCredit.CREDIT
            else:
                # Normal credit balance accounts
                return DebitCredit.CREDIT if multiplier == 1 else DebitCredit.DEBIT
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class JournalEntryType(str, Enum):
    """Types of journal entries."""
    STANDARD = "standard"
    ADJUSTING = "adjusting"
    CLOSING = "closing"
    REVERSING = "reversing"
    RECURRING = "recurring"


class JournalEntryStatus(str, Enum):
    """Status of a journal entry."""
    DRAFT = "draft"
    PENDING = "pending"
    POSTED = "posted"
    VOID = "void"
    REVERSED = "reversed"


class JournalEntry(BaseModel):
    """
    Journal entry containing multiple distributions.

    Enforces double-entry accounting: sum of all balance impacts must equal zero.
    Uses From/To flow semantics instead of Debit/Credit.
    """
    journal_entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Entry information
    entry_number: Optional[str] = None  # Sequential number like "JE-2025-001"
    entry_type: JournalEntryType = JournalEntryType.STANDARD
    entry_date: date
    posting_date: Optional[date] = None

    # Distributions (the heart of double-entry)
    distributions: List[Distribution] = Field(default_factory=list)

    # Descriptive information
    description: str
    memo: Optional[str] = None
    notes: Optional[str] = None

    # Reference fields
    source_document: Optional[str] = None
    transaction_id: Optional[str] = None  # Link to original transaction
    recurring_entry_id: Optional[str] = None
    reversed_entry_id: Optional[str] = None  # If this reverses another entry

    # Categorization
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Status
    status: JournalEntryStatus = JournalEntryStatus.DRAFT

    # Approval workflow
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    posted_by: Optional[str] = None
    posted_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Audit trail
    revision_number: int = 1
    previous_version_id: Optional[str] = None

    def is_balanced(self) -> bool:
        """
        Check if the journal entry is balanced.

        In the FROM/TO system, an entry is balanced when:
        - Total FROM amounts = Total TO amounts

        This ensures every dollar flowing OUT has a corresponding dollar flowing IN.
        """
        from_total = sum(d.amount for d in self.distributions if d.flow_direction == FlowDirection.FROM)
        to_total = sum(d.amount for d in self.distributions if d.flow_direction == FlowDirection.TO)

        # Allow for floating point precision issues
        return abs(from_total - to_total) < 0.01

    def get_balance_total(self) -> float:
        """
        Get the difference between FROM and TO totals.

        Should be 0 if balanced (FROM total - TO total = 0).
        """
        from_total = sum(d.amount for d in self.distributions if d.flow_direction == FlowDirection.FROM)
        to_total = sum(d.amount for d in self.distributions if d.flow_direction == FlowDirection.TO)
        return from_total - to_total

    def get_from_distributions(self) -> List[Distribution]:
        """Get all FROM (outflow) distributions."""
        return [d for d in self.distributions if d.flow_direction == FlowDirection.FROM]

    def get_to_distributions(self) -> List[Distribution]:
        """Get all TO (inflow) distributions."""
        return [d for d in self.distributions if d.flow_direction == FlowDirection.TO]

    def get_total_amount(self) -> float:
        """
        Get the total transaction amount.

        This is typically half of the sum of absolute values (since balanced entries
        have equal FROM and TO amounts).
        """
        return sum(d.amount for d in self.distributions) / 2

    def get_distributions_by_account(self, account_id: str) -> List[Distribution]:
        """Get all distributions for a specific account."""
        return [d for d in self.distributions if d.account_id == account_id]

    def get_total_debits(self) -> float:
        """Get total debit amount (traditional accounting view)."""
        return sum(d.get_debit_amount() for d in self.distributions)

    def get_total_credits(self) -> float:
        """Get total credit amount (traditional accounting view)."""
        return sum(d.get_credit_amount() for d in self.distributions)

    def is_balanced_traditional(self) -> bool:
        """
        Check if debits equal credits (traditional accounting validation).

        This should always be true if FROM = TO, as they're two views of the same data.
        """
        return abs(self.get_total_debits() - self.get_total_credits()) < 0.01

    def format_t_account(self) -> str:
        """
        Format the journal entry as a traditional T-account display.

        Returns a string showing debits on the left, credits on the right.
        """
        lines = []
        lines.append(f"Journal Entry: {self.entry_number or self.journal_entry_id}")
        lines.append(f"Date: {self.entry_date}")
        lines.append(f"Description: {self.description}")
        lines.append("-" * 80)
        lines.append(f"{'Account':<40} {'Debit':>15} {'Credit':>15}")
        lines.append("-" * 80)

        for dist in self.distributions:
            debit_str = f"${dist.amount:,.2f}" if dist.debit_credit == DebitCredit.DEBIT else ""
            credit_str = f"${dist.amount:,.2f}" if dist.debit_credit == DebitCredit.CREDIT else ""
            lines.append(f"{dist.account_id:<40} {debit_str:>15} {credit_str:>15}")

        lines.append("-" * 80)
        lines.append(f"{'TOTALS':<40} ${self.get_total_debits():>14,.2f} ${self.get_total_credits():>14,.2f}")
        lines.append("-" * 80)

        return "\n".join(lines)

    def add_distribution(
        self,
        account_id: str,
        account_type: AccountType,
        flow_direction: FlowDirection,
        amount: float,
        description: Optional[str] = None,
        **kwargs
    ) -> Distribution:
        """
        Add a distribution to the journal entry.

        Automatically calculates the correct multiplier based on account type
        and flow direction.
        """
        multiplier = Distribution.calculate_multiplier(account_type, flow_direction)

        distribution = Distribution(
            account_id=account_id,
            account_type=account_type,
            flow_direction=flow_direction,
            amount=amount,
            multiplier=multiplier,
            description=description,
            **kwargs
        )

        self.distributions.append(distribution)
        return distribution

    def create_ledger_entries(self, account_balances: Dict[str, float]) -> List['AccountLedger']:
        """
        Create general ledger entries for all distributions.

        Args:
            account_balances: Dict mapping account_id to current balance

        Returns:
            List of AccountLedger entries with running balances
        """
        ledger_entries = []

        for dist in self.distributions:
            # Get current balance for this account
            balance_before = account_balances.get(dist.account_id, 0.0)

            # Calculate balance impact
            balance_impact = dist.calculate_balance_impact()
            balance_after = balance_before + balance_impact

            # Create ledger entry
            ledger_entry = AccountLedger(
                account_id=dist.account_id,
                account_number="",  # Should be looked up from ChartOfAccounts
                account_name="",     # Should be looked up from ChartOfAccounts
                account_type=dist.account_type,
                journal_entry_id=self.journal_entry_id,
                distribution_id=dist.distribution_id,
                entry_number=self.entry_number,
                transaction_date=self.entry_date,
                posting_date=self.posting_date or self.entry_date,
                description=dist.description or self.description,
                reference=dist.reference_id,
                flow_direction=dist.flow_direction,
                amount=dist.amount,
                debit_credit=dist.debit_credit,
                debit_amount=dist.get_debit_amount(),
                credit_amount=dist.get_credit_amount(),
                multiplier=dist.multiplier,
                balance_impact=balance_impact,
                balance_before=balance_before,
                balance_after=balance_after,
                posted_by=self.posted_by,
                posted_at=self.posted_at or datetime.utcnow()
            )

            ledger_entries.append(ledger_entry)

            # Update account balance for next distribution
            account_balances[dist.account_id] = balance_after

        return ledger_entries

    @validator('distributions')
    def validate_distributions(cls, v):
        """Validate that there are at least 2 distributions."""
        if len(v) < 2:
            raise ValueError("Journal entry must have at least 2 distributions")
        return v

    @validator('status')
    def validate_balanced_before_posting(cls, v, values):
        """Ensure entry is balanced before allowing it to be posted."""
        if v == JournalEntryStatus.POSTED and 'distributions' in values:
            distributions = values['distributions']

            # Calculate FROM and TO totals
            from_total = sum(d.amount for d in distributions if d.flow_direction == FlowDirection.FROM)
            to_total = sum(d.amount for d in distributions if d.flow_direction == FlowDirection.TO)

            if abs(from_total - to_total) >= 0.01:
                raise ValueError(
                    f"Cannot post unbalanced journal entry. "
                    f"FROM total: ${from_total:.2f}, TO total: ${to_total:.2f}. "
                    f"Difference: ${abs(from_total - to_total):.2f}"
                )
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class ChartOfAccounts(BaseModel):
    """
    Chart of Accounts entry.

    Defines the structure of accounts available for journal entries.
    """
    account_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Account identification
    account_number: str  # e.g., "1000", "1100", "2000"
    account_name: str  # e.g., "Cash", "Accounts Receivable"

    # Classification
    account_type: AccountType
    account_subtype: Optional[str] = None  # e.g., "current_asset", "fixed_asset"

    # Hierarchy
    parent_account_id: Optional[str] = None
    level: int = 1  # 1 = top level, 2 = sub-account, etc.

    # Account properties
    is_active: bool = True
    is_system_account: bool = False  # Cannot be deleted
    allow_manual_entries: bool = True
    requires_distribution: bool = False  # Requires cost center, project, etc.

    # Virtual Envelope References (for budgeting)
    budget_envelope_id: Optional[str] = None   # For expense accounts: links to budget envelope
    payment_envelope_id: Optional[str] = None  # For liability accounts: links to payment envelope

    # Balance tracking
    current_balance: float = 0.0
    opening_balance: float = 0.0
    opening_balance_date: Optional[date] = None

    # Display
    display_order: int = 0
    description: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    def get_normal_balance_type(self) -> str:
        """Get the normal balance type (Debit or Credit)."""
        if self.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            return "Debit"
        else:
            return "Credit"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class AccountBalance(BaseModel):
    """
    Account balance tracking for a specific period.

    Tracks the flow of money through an account over a time period.
    Shows opening balance, activity (FROM/TO), and closing balance.
    """
    balance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Account reference
    account_id: str
    account_number: str
    account_name: str
    account_type: AccountType

    # Period definition
    period_start: date
    period_end: date
    period_label: str  # e.g., "2025-01", "2025-Q1", "2025"

    # Opening balance
    opening_balance: float
    opening_balance_date: date

    # Activity during period (FROM/TO perspective)
    total_from_amount: float = 0.0  # Money flowing OUT
    total_to_amount: float = 0.0    # Money flowing IN
    transaction_count: int = 0

    # Activity during period (Debit/Credit perspective)
    total_debits: float = 0.0
    total_credits: float = 0.0

    # Net activity
    net_change: float = 0.0  # Can be calculated as (to - from) or based on account type

    # Closing balance
    closing_balance: float

    # Reconciliation
    is_reconciled: bool = False
    reconciled_date: Optional[datetime] = None
    reconciled_by: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def calculate_closing_balance(self) -> float:
        """
        Calculate closing balance from opening + net change.

        Formula: closing = opening + (total_to × to_multiplier) + (total_from × from_multiplier)

        For simplicity, we calculate based on debit/credit:
        - Assets/Expenses: closing = opening + debits - credits
        - Liabilities/Equity/Revenue: closing = opening + credits - debits
        """
        if self.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            return self.opening_balance + self.total_debits - self.total_credits
        else:
            return self.opening_balance + self.total_credits - self.total_debits

    def verify_balance(self) -> bool:
        """Verify that closing_balance matches calculated value."""
        calculated = self.calculate_closing_balance()
        return abs(self.closing_balance - calculated) < 0.01

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class AccountLedger(BaseModel):
    """
    General Ledger entry for an account.

    Represents a single transaction's impact on an account balance.
    This is the detailed transaction-by-transaction history.
    """
    ledger_entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Account reference
    account_id: str
    account_number: str
    account_name: str
    account_type: AccountType

    # Transaction reference
    journal_entry_id: str
    distribution_id: str
    entry_number: Optional[str] = None
    transaction_date: date
    posting_date: date

    # Transaction details
    description: str
    reference: Optional[str] = None

    # Flow perspective
    flow_direction: FlowDirection
    amount: float

    # Traditional perspective
    debit_credit: DebitCredit
    debit_amount: float = 0.0
    credit_amount: float = 0.0

    # Balance calculation
    multiplier: int
    balance_impact: float  # amount × multiplier

    # Running balance
    balance_before: float
    balance_after: float

    # Metadata
    posted_by: Optional[str] = None
    posted_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class RecurrenceFrequency(str, Enum):
    """Frequency options for recurring journal entries."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUALLY = "semiannually"
    ANNUALLY = "annually"


class RecurringJournalEntry(BaseModel):
    """
    Template for recurring journal entries.

    Used to automatically generate journal entries on a schedule.

    Examples:
        Monthly mortgage: frequency=MONTHLY, day_of_month=1
        Biweekly payroll: frequency=BIWEEKLY, start_date=first pay date
        Quarterly tax: frequency=QUARTERLY, day_of_month=15, month_of_quarter=1
    """
    recurring_entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Template information
    template_name: str
    description: str

    # Entry configuration
    entry_type: JournalEntryType = JournalEntryType.RECURRING
    distribution_template: List[Dict[str, Any]] = Field(default_factory=list)
    # Each item: {account_id, account_type, flow_direction, amount, description,
    #             budget_envelope_id?, payment_envelope_id?}

    # Recurrence configuration
    frequency: RecurrenceFrequency
    interval: int = 1  # Every N periods (e.g., interval=2 for every 2 months)

    # Specific day/month rules
    day_of_month: Optional[int] = None  # 1-31, for monthly/quarterly/annually
    day_of_week: Optional[int] = None   # 0=Monday, 6=Sunday, for weekly
    month_of_quarter: Optional[int] = None  # 1-3, for quarterly
    month_of_year: Optional[int] = None     # 1-12, for annually

    # Date range
    start_date: date
    end_date: Optional[date] = None
    end_after_occurrences: Optional[int] = None  # Stop after N occurrences

    # Next occurrence (calculated)
    next_occurrence: Optional[date] = None

    # Automation
    auto_post: bool = False  # Automatically post when generated
    auto_create_days_before: int = 0  # Create N days before due date
    require_approval: bool = True

    # Status
    is_active: bool = True
    last_generated_date: Optional[date] = None
    total_generated: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    # Notes
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
