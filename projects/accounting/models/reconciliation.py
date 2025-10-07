"""
Reconciliation Data Models

Models for account reconciliation, statement matching, and payment processing.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ReconciliationStatus(str, Enum):
    """Reconciliation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISCREPANCY = "discrepancy"
    FAILED = "failed"


class MatchStatus(str, Enum):
    """Transaction match status."""
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    PARTIAL_MATCH = "partial_match"
    SUGGESTED = "suggested"
    MANUAL_MATCH = "manual_match"


class DiscrepancyType(str, Enum):
    """Types of reconciliation discrepancies."""
    MISSING_TRANSACTION = "missing_transaction"
    AMOUNT_MISMATCH = "amount_mismatch"
    DATE_MISMATCH = "date_mismatch"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    UNCLEARED_TRANSACTION = "uncleared_transaction"
    UNKNOWN = "unknown"


class PaymentStatus(str, Enum):
    """Payment processing status."""
    SCHEDULED = "scheduled"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment methods."""
    ACH = "ach"
    WIRE = "wire"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CASH = "cash"
    OTHER = "other"


class StatementTransaction(BaseModel):
    """
    Transaction from external statement (bank, credit card).

    Used for matching against internal transactions during reconciliation.
    """
    statement_transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    statement_id: str

    # Transaction details
    date: date
    description: str
    amount: float
    transaction_type: str  # "debit", "credit"

    # Matching
    match_status: MatchStatus = MatchStatus.UNMATCHED
    matched_transaction_id: Optional[str] = None
    match_confidence: float = 0.0

    # Statement details
    balance_after: Optional[float] = None
    reference_number: Optional[str] = None

    # Metadata
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class TransactionMatch(BaseModel):
    """
    Match between internal transaction and statement transaction.

    Records the matching details and confidence score.
    """
    match_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reconciliation_id: str

    # Matched items
    internal_transaction_id: str
    statement_transaction_id: str

    # Match details
    match_status: MatchStatus
    match_confidence: float
    match_method: str  # "exact", "fuzzy", "manual", "suggested"

    # Differences
    amount_difference: float = 0.0
    date_difference_days: int = 0
    description_similarity: float = 0.0

    # Resolution
    accepted: bool = False
    rejected: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class Discrepancy(BaseModel):
    """
    Reconciliation discrepancy.

    Identifies issues found during reconciliation that need resolution.
    """
    discrepancy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reconciliation_id: str

    # Discrepancy details
    discrepancy_type: DiscrepancyType
    severity: str = "medium"  # "low", "medium", "high"

    # Related items
    internal_transaction_id: Optional[str] = None
    statement_transaction_id: Optional[str] = None

    # Details
    description: str
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None
    difference: Optional[float] = None

    # Resolution
    status: str = "open"  # "open", "investigating", "resolved", "accepted"
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class ReconciliationStatement(BaseModel):
    """
    External statement for reconciliation.

    Bank statement, credit card statement, etc.
    """
    statement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str

    # Statement period
    statement_date: date
    start_date: date
    end_date: date

    # Balances
    opening_balance: float
    closing_balance: float

    # Statement details
    statement_type: str  # "bank", "credit_card", "investment"
    institution_name: Optional[str] = None
    account_number_last4: Optional[str] = None

    # Transactions
    transaction_count: int = 0
    total_debits: float = 0.0
    total_credits: float = 0.0

    # Processing
    imported_at: datetime = Field(default_factory=datetime.utcnow)
    imported_by: Optional[str] = None
    source_file: Optional[str] = None

    # Metadata
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None

    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class Reconciliation(BaseModel):
    """
    Account reconciliation session.

    Tracks the process of matching internal transactions against external statements.
    """
    reconciliation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str
    statement_id: str

    # Period
    start_date: date
    end_date: date

    # Status
    status: ReconciliationStatus = ReconciliationStatus.PENDING

    # Balances
    opening_balance_statement: float
    closing_balance_statement: float
    opening_balance_internal: float
    closing_balance_internal: float
    balance_difference: float = 0.0

    # Matching statistics
    total_statement_transactions: int = 0
    total_internal_transactions: int = 0
    matched_transactions: int = 0
    unmatched_statement_transactions: int = 0
    unmatched_internal_transactions: int = 0
    match_rate: float = 0.0

    # Discrepancies
    discrepancy_count: int = 0
    total_discrepancy_amount: float = 0.0

    # Processing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reconciled_by: Optional[str] = None

    # Results
    is_balanced: bool = False
    requires_adjustment: bool = False
    adjustment_amount: float = 0.0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    def calculate_match_rate(self):
        """Calculate matching success rate."""
        if self.total_statement_transactions == 0:
            self.match_rate = 0.0
        else:
            self.match_rate = (self.matched_transactions / self.total_statement_transactions) * 100

    def calculate_balance_difference(self):
        """Calculate difference between statement and internal balances."""
        self.balance_difference = self.closing_balance_internal - self.closing_balance_statement

    def check_balanced(self):
        """Check if reconciliation is balanced."""
        self.is_balanced = abs(self.balance_difference) < 0.01  # Within 1 cent


class Payment(BaseModel):
    """
    Scheduled or processed payment.

    Tracks payments from scheduling through completion.
    """
    payment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Payment details
    from_account_id: str
    to_account_id: Optional[str] = None
    payee_name: str
    amount: float
    currency: str = "USD"

    # Scheduling
    scheduled_date: date
    payment_method: PaymentMethod
    payment_status: PaymentStatus = PaymentStatus.SCHEDULED

    # Processing
    submitted_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Related transactions
    transaction_id: Optional[str] = None  # Created transaction after payment completes

    # Details
    memo: Optional[str] = None
    reference_number: Optional[str] = None
    confirmation_number: Optional[str] = None

    # Recurring
    is_recurring: bool = False
    recurring_payment_id: Optional[str] = None

    # Failure handling
    failure_reason: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    notes: Optional[str] = None


class RecurringPayment(BaseModel):
    """
    Recurring payment template.

    Defines a payment that repeats on a schedule.
    """
    recurring_payment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Payment details
    from_account_id: str
    payee_name: str
    amount: float
    payment_method: PaymentMethod

    # Schedule
    frequency: str  # "weekly", "monthly", "quarterly", "annual"
    day_of_month: Optional[int] = None  # For monthly/quarterly/annual
    day_of_week: Optional[str] = None  # For weekly

    # Period
    start_date: date
    end_date: Optional[date] = None
    next_payment_date: Optional[date] = None

    # Status
    is_active: bool = True

    # History
    payments_created: int = 0
    last_payment_id: Optional[str] = None
    last_payment_date: Optional[date] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    memo: Optional[str] = None
    notes: Optional[str] = None


class ReconciliationSummary(BaseModel):
    """
    Summary of reconciliation results.

    High-level overview for reporting and dashboards.
    """
    summary_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reconciliation_id: str
    account_id: str

    # Period
    period_start: date
    period_end: date

    # Results
    is_reconciled: bool
    match_rate: float
    discrepancy_count: int
    total_discrepancy_amount: float

    # Key metrics
    statement_balance: float
    internal_balance: float
    difference: float

    # Transaction counts
    matched: int
    unmatched_statement: int
    unmatched_internal: int

    # Resolution
    adjustments_needed: bool
    adjustment_amount: float

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class MatchingSuggestion(BaseModel):
    """
    Suggested match between transactions.

    AI/algorithm generated matching suggestions for review.
    """
    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reconciliation_id: str

    # Suggested match
    internal_transaction_id: str
    statement_transaction_id: str

    # Confidence
    confidence_score: float
    match_reason: str

    # Comparison
    amount_difference: float
    date_difference_days: int
    description_similarity: float

    # Features that matched
    matching_features: List[str] = Field(default_factory=list)

    # Action
    accepted: bool = False
    rejected: bool = False

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AdjustmentEntry(BaseModel):
    """
    Adjustment entry to resolve reconciliation discrepancies.

    Creates correcting transactions to balance accounts.
    """
    adjustment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reconciliation_id: str
    discrepancy_id: Optional[str] = None

    # Adjustment details
    account_id: str
    adjustment_type: str  # "correction", "fee", "interest", "error"
    amount: float
    description: str

    # Processing
    status: str = "pending"  # "pending", "approved", "applied", "rejected"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Related transaction
    transaction_id: Optional[str] = None  # Created after adjustment applied

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    notes: Optional[str] = None
