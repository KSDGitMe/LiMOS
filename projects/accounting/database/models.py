"""
SQLAlchemy Database Models for LiMOS Accounting Module

This module defines the database schema for the accounting system using SQLAlchemy ORM.
All models map directly to the Pydantic models defined in models.py.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Boolean, ForeignKey, Text, JSON, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string for primary keys."""
    return str(uuid.uuid4())


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

class ChartOfAccountsDB(Base):
    __tablename__ = "chart_of_accounts"

    account_id = Column(String, primary_key=True, index=True)
    account_number = Column(String, unique=True, index=True)
    account_name = Column(String, nullable=False, index=True)
    account_type = Column(String, nullable=False, index=True)  # asset, liability, equity, revenue, expense
    account_subtype = Column(String, nullable=True)
    parent_account_id = Column(String, ForeignKey("chart_of_accounts.account_id"), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    current_balance = Column(Float, default=0.0)
    budget_envelope_id = Column(String, ForeignKey("budget_envelopes.envelope_id"), nullable=True)
    payment_envelope_id = Column(String, ForeignKey("payment_envelopes.envelope_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent_account = relationship("ChartOfAccountsDB", remote_side=[account_id], backref="child_accounts")
    distributions = relationship("DistributionDB", back_populates="account")


# ============================================================================
# BUDGET ENVELOPES
# ============================================================================

class BudgetEnvelopeDB(Base):
    __tablename__ = "budget_envelopes"

    envelope_id = Column(String, primary_key=True, default=generate_uuid)
    envelope_number = Column(String, unique=True, nullable=False, index=True)
    envelope_name = Column(String, nullable=False, index=True)
    monthly_allocation = Column(Float, nullable=False)
    rollover_policy = Column(String, default="accumulate")  # reset, accumulate, cap
    current_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    accounts = relationship("ChartOfAccountsDB", foreign_keys="ChartOfAccountsDB.budget_envelope_id", backref="budget_envelope")


# ============================================================================
# PAYMENT ENVELOPES
# ============================================================================

class PaymentEnvelopeDB(Base):
    __tablename__ = "payment_envelopes"

    envelope_id = Column(String, primary_key=True, default=generate_uuid)
    envelope_number = Column(String, unique=True, nullable=False, index=True)
    envelope_name = Column(String, nullable=False, index=True)
    linked_account_id = Column(String, ForeignKey("chart_of_accounts.account_id"), nullable=False)
    current_balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    linked_account = relationship("ChartOfAccountsDB", foreign_keys=[linked_account_id])
    accounts = relationship("ChartOfAccountsDB", foreign_keys="ChartOfAccountsDB.payment_envelope_id", backref="payment_envelope")


# ============================================================================
# JOURNAL ENTRIES
# ============================================================================

class JournalEntryDB(Base):
    __tablename__ = "journal_entries"

    journal_entry_id = Column(String, primary_key=True, default=generate_uuid)
    entry_number = Column(String, unique=True, nullable=True, index=True)
    entry_type = Column(String, nullable=False)  # standard, recurring, adjusting, closing
    entry_date = Column(String, nullable=False, index=True)  # ISO date string
    posting_date = Column(String, nullable=True, index=True)  # ISO date string
    description = Column(Text, nullable=False)
    memo = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    source_document = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True, index=True)
    recurring_entry_id = Column(String, ForeignKey("recurring_journal_entries.recurring_entry_id"), nullable=True)
    reversed_entry_id = Column(String, ForeignKey("journal_entries.journal_entry_id"), nullable=True)
    category = Column(String, nullable=True, index=True)
    tags = Column(JSON, default=list)  # Store as JSON array
    status = Column(String, default="draft", index=True)  # draft, posted, void
    created_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    posted_by = Column(String, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revision_number = Column(Integer, default=1)
    previous_version_id = Column(String, ForeignKey("journal_entries.journal_entry_id"), nullable=True)

    # Relationships
    distributions = relationship("DistributionDB", back_populates="journal_entry", cascade="all, delete-orphan")
    recurring_template = relationship("RecurringJournalEntryDB", foreign_keys=[recurring_entry_id])
    reversed_entry = relationship("JournalEntryDB", remote_side=[journal_entry_id], foreign_keys=[reversed_entry_id])


# ============================================================================
# DISTRIBUTIONS
# ============================================================================

class DistributionDB(Base):
    __tablename__ = "distributions"

    distribution_id = Column(String, primary_key=True, default=generate_uuid)
    journal_entry_id = Column(String, ForeignKey("journal_entries.journal_entry_id"), nullable=False)
    account_id = Column(String, ForeignKey("chart_of_accounts.account_id"), nullable=False)
    account_type = Column(String, nullable=False)
    flow_direction = Column(String, nullable=False)  # from, to
    amount = Column(Float, nullable=False)
    multiplier = Column(Integer, default=1)
    debit_credit = Column(String, nullable=False)  # Dr, Cr
    description = Column(Text, nullable=False)
    memo = Column(Text, nullable=True)
    reference_id = Column(String, nullable=True)
    cost_center = Column(String, nullable=True)
    department = Column(String, nullable=True)
    project_id = Column(String, nullable=True)
    budget_envelope_id = Column(String, ForeignKey("budget_envelopes.envelope_id"), nullable=True)
    payment_envelope_id = Column(String, ForeignKey("payment_envelopes.envelope_id"), nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    journal_entry = relationship("JournalEntryDB", back_populates="distributions")
    account = relationship("ChartOfAccountsDB", back_populates="distributions")
    budget_envelope = relationship("BudgetEnvelopeDB")
    payment_envelope = relationship("PaymentEnvelopeDB")


# ============================================================================
# RECURRING JOURNAL ENTRIES
# ============================================================================

class RecurringJournalEntryDB(Base):
    __tablename__ = "recurring_journal_entries"

    recurring_entry_id = Column(String, primary_key=True)
    template_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    entry_type = Column(String, default="recurring")
    frequency = Column(String, nullable=False)  # daily, weekly, monthly, quarterly, yearly
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=True)
    last_generated_date = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    auto_post = Column(Boolean, default=False)
    distributions = Column(JSON, nullable=False)  # Store distributions as JSON
    category = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    generated_entries = relationship("JournalEntryDB", foreign_keys="JournalEntryDB.recurring_entry_id", backref="recurring_source")


# ============================================================================
# INDEXES AND CONSTRAINTS
# ============================================================================

# Add check constraints
ChartOfAccountsDB.__table_args__ = (
    CheckConstraint("account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')", name="valid_account_type"),
)

JournalEntryDB.__table_args__ = (
    CheckConstraint("status IN ('draft', 'posted', 'void')", name="valid_status"),
    CheckConstraint("entry_type IN ('standard', 'recurring', 'adjusting', 'closing')", name="valid_entry_type"),
)

DistributionDB.__table_args__ = (
    CheckConstraint("flow_direction IN ('from', 'to')", name="valid_flow_direction"),
    CheckConstraint("debit_credit IN ('Dr', 'Cr')", name="valid_debit_credit"),
)

BudgetEnvelopeDB.__table_args__ = (
    CheckConstraint("rollover_policy IN ('reset', 'accumulate', 'cap')", name="valid_rollover_policy"),
)

RecurringJournalEntryDB.__table_args__ = (
    CheckConstraint("frequency IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')", name="valid_frequency"),
)
