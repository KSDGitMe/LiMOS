"""
Transaction Data Models

Defines the structure for transactions and recurring transaction templates.
"""

import uuid
from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class TransactionType(str, Enum):
    """Transaction type categories."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    """Transaction status."""
    PENDING = "pending"
    CLEARED = "cleared"
    RECONCILED = "reconciled"
    VOID = "void"


class RecurrenceFrequency(str, Enum):
    """Recurrence frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUALLY = "semiannually"
    ANNUALLY = "annually"
    CUSTOM = "custom"


class RecurrenceRule(BaseModel):
    """
    Recurrence rule for recurring transactions.

    CRITICAL: day_of_month, day_of_week, month_of_year, and week_of_month
    are ARRAYS to support multiple values (e.g., pay on 1st and 15th).
    """
    frequency: RecurrenceFrequency
    interval: int = 1  # Every N periods

    # ARRAYS for flexibility
    day_of_month: List[int] = Field(
        default_factory=list,
        description="Days of month (1-31), max 31 items"
    )
    day_of_week: List[str] = Field(
        default_factory=list,
        description="Days of week (monday-sunday), max 7 items"
    )
    month_of_year: List[int] = Field(
        default_factory=list,
        description="Months (1-12), max 12 items"
    )
    week_of_month: List[int] = Field(
        default_factory=list,
        description="Week of month (1-5), max 5 items"
    )

    occurrence_limit_per_period: Optional[int] = None
    custom_schedule: Optional[List[str]] = None  # ISO date strings

    @validator('day_of_month')
    def validate_day_of_month(cls, v):
        if len(v) > 31:
            raise ValueError("day_of_month cannot have more than 31 items")
        if any(d < 1 or d > 31 for d in v):
            raise ValueError("day_of_month values must be between 1 and 31")
        return v

    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        valid_days = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
        if len(v) > 7:
            raise ValueError("day_of_week cannot have more than 7 items")
        if any(d.lower() not in valid_days for d in v):
            raise ValueError(f"day_of_week values must be one of {valid_days}")
        return [d.lower() for d in v]

    @validator('month_of_year')
    def validate_month_of_year(cls, v):
        if len(v) > 12:
            raise ValueError("month_of_year cannot have more than 12 items")
        if any(m < 1 or m > 12 for m in v):
            raise ValueError("month_of_year values must be between 1 and 12")
        return v

    @validator('week_of_month')
    def validate_week_of_month(cls, v):
        if len(v) > 5:
            raise ValueError("week_of_month cannot have more than 5 items")
        if any(w < 1 or w > 5 for w in v):
            raise ValueError("week_of_month values must be between 1 and 5")
        return v


class Transaction(BaseModel):
    """
    Single transaction record.

    Represents an actual financial transaction (completed or scheduled).
    """
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str
    date: date
    merchant: str
    amount: float
    transaction_type: TransactionType
    category: Optional[str] = None
    subcategory: Optional[str] = None
    payment_method: Optional[str] = None
    status: TransactionStatus = TransactionStatus.PENDING
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Linking
    recurring_transaction_id: Optional[str] = None
    parent_transaction_id: Optional[str] = None  # For splits

    # Reconciliation
    bank_transaction_id: Optional[str] = None
    reconciled_date: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    # Receipt/attachment
    receipt_id: Optional[str] = None
    attachment_urls: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class RecurringTransaction(BaseModel):
    """
    Recurring transaction template.

    Used to automatically generate scheduled transactions.
    """
    recurring_transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_name: str
    account_id: str
    merchant: str
    base_amount: float
    amount_variance: Optional[float] = None  # For variable amounts (± this much)
    transaction_type: TransactionType
    category: Optional[str] = None
    subcategory: Optional[str] = None
    payment_method: Optional[str] = None

    # Recurrence configuration
    recurrence_rule: RecurrenceRule

    # Date range
    start_date: date
    end_date: Optional[date] = None
    end_after_occurrences: Optional[int] = None

    # Automation settings
    auto_create: bool = True
    create_days_before: int = 0  # Create N days before due date
    require_confirmation: bool = False

    # Status
    is_active: bool = True
    last_generated_date: Optional[date] = None
    total_generated: int = 0

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class Account(BaseModel):
    """Financial account."""
    account_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_name: str
    account_type: str  # checking, savings, credit_card, etc.
    institution: Optional[str] = None
    current_balance: float = 0.0
    currency: str = "USD"

    # Interest configuration (for forecasting)
    interest_rate: Optional[float] = None  # APY for savings, APR for credit
    interest_type: Optional[str] = None  # simple, compound
    compounding_frequency: Optional[str] = None  # daily, monthly, quarterly

    # Status
    is_active: bool = True
    is_closed: bool = False

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
