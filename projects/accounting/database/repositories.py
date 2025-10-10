"""
Database Repositories for LiMOS Accounting Module

This module provides repository classes for CRUD operations on all entities.
Repositories handle the conversion between Pydantic models and SQLAlchemy models.
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, date

from .models import (
    ChartOfAccountsDB, BudgetEnvelopeDB, PaymentEnvelopeDB,
    JournalEntryDB, DistributionDB, RecurringJournalEntryDB
)
from ..models.journal_entries import (
    ChartOfAccounts, JournalEntry, Distribution, RecurringJournalEntry
)
from ..models.budget_envelopes import BudgetEnvelope, PaymentEnvelope


# ============================================================================
# CHART OF ACCOUNTS REPOSITORY
# ============================================================================

class ChartOfAccountsRepository:
    """Repository for Chart of Accounts CRUD operations."""

    @staticmethod
    def create(db: Session, account: ChartOfAccounts) -> ChartOfAccounts:
        """Create a new account."""
        db_account = ChartOfAccountsDB(
            account_id=account.account_id,
            account_number=account.account_number,
            account_name=account.account_name,
            account_type=account.account_type,
            account_subtype=account.account_subtype,
            parent_account_id=account.parent_account_id,
            description=account.description,
            is_active=account.is_active,
            current_balance=account.current_balance,
            budget_envelope_id=account.budget_envelope_id,
            payment_envelope_id=account.payment_envelope_id,
        )
        db.add(db_account)
        db.commit()
        db.refresh(db_account)
        return ChartOfAccountsRepository._to_pydantic(db_account)

    @staticmethod
    def get_by_id(db: Session, account_id: str) -> Optional[ChartOfAccounts]:
        """Get account by ID."""
        db_account = db.query(ChartOfAccountsDB).filter(
            ChartOfAccountsDB.account_id == account_id
        ).first()
        return ChartOfAccountsRepository._to_pydantic(db_account) if db_account else None

    @staticmethod
    def get_all(db: Session, account_type: Optional[str] = None, is_active: Optional[bool] = None) -> List[ChartOfAccounts]:
        """Get all accounts with optional filters."""
        query = db.query(ChartOfAccountsDB)

        if account_type:
            query = query.filter(ChartOfAccountsDB.account_type == account_type)
        if is_active is not None:
            query = query.filter(ChartOfAccountsDB.is_active == is_active)

        db_accounts = query.all()
        return [ChartOfAccountsRepository._to_pydantic(acc) for acc in db_accounts]

    @staticmethod
    def update(db: Session, account_id: str, account: ChartOfAccounts) -> ChartOfAccounts:
        """Update an existing account."""
        db_account = db.query(ChartOfAccountsDB).filter(
            ChartOfAccountsDB.account_id == account_id
        ).first()

        if not db_account:
            raise ValueError(f"Account {account_id} not found")

        # Update fields
        db_account.account_name = account.account_name
        db_account.account_type = account.account_type
        db_account.account_subtype = account.account_subtype
        db_account.parent_account_id = account.parent_account_id
        db_account.description = account.description
        db_account.is_active = account.is_active
        db_account.current_balance = account.current_balance
        db_account.budget_envelope_id = account.budget_envelope_id
        db_account.payment_envelope_id = account.payment_envelope_id
        db_account.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_account)
        return ChartOfAccountsRepository._to_pydantic(db_account)

    @staticmethod
    def update_balance(db: Session, account_id: str, new_balance: float):
        """Update account balance."""
        db_account = db.query(ChartOfAccountsDB).filter(
            ChartOfAccountsDB.account_id == account_id
        ).first()

        if db_account:
            db_account.current_balance = new_balance
            db_account.updated_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def delete(db: Session, account_id: str):
        """Delete an account."""
        db_account = db.query(ChartOfAccountsDB).filter(
            ChartOfAccountsDB.account_id == account_id
        ).first()

        if db_account:
            db.delete(db_account)
            db.commit()

    @staticmethod
    def _to_pydantic(db_account: ChartOfAccountsDB) -> ChartOfAccounts:
        """Convert SQLAlchemy model to Pydantic model."""
        return ChartOfAccounts(
            account_id=db_account.account_id,
            account_number=db_account.account_number,
            account_name=db_account.account_name,
            account_type=db_account.account_type,
            account_subtype=db_account.account_subtype,
            parent_account_id=db_account.parent_account_id,
            description=db_account.description,
            is_active=db_account.is_active,
            current_balance=db_account.current_balance,
            budget_envelope_id=db_account.budget_envelope_id,
            payment_envelope_id=db_account.payment_envelope_id,
            created_at=db_account.created_at,
            updated_at=db_account.updated_at,
        )


# ============================================================================
# JOURNAL ENTRY REPOSITORY
# ============================================================================

class JournalEntryRepository:
    """Repository for Journal Entry CRUD operations."""

    @staticmethod
    def create(db: Session, entry: JournalEntry) -> JournalEntry:
        """Create a new journal entry with distributions."""
        db_entry = JournalEntryDB(
            journal_entry_id=entry.journal_entry_id,
            entry_number=entry.entry_number,
            entry_type=entry.entry_type,
            entry_date=entry.entry_date,
            posting_date=entry.posting_date,
            description=entry.description,
            memo=entry.memo,
            notes=entry.notes,
            source_document=entry.source_document,
            transaction_id=entry.transaction_id,
            recurring_entry_id=entry.recurring_entry_id,
            reversed_entry_id=entry.reversed_entry_id,
            category=entry.category,
            tags=entry.tags or [],
            status=entry.status,
            created_by=entry.created_by,
            approved_by=entry.approved_by,
            approved_at=entry.approved_at,
            posted_by=entry.posted_by,
            posted_at=entry.posted_at,
            revision_number=entry.revision_number,
            previous_version_id=entry.previous_version_id,
        )
        db.add(db_entry)

        # Add distributions
        for dist in entry.distributions:
            db_dist = DistributionDB(
                distribution_id=dist.distribution_id,
                journal_entry_id=entry.journal_entry_id,
                account_id=dist.account_id,
                account_type=dist.account_type,
                flow_direction=dist.flow_direction,
                amount=dist.amount,
                multiplier=dist.multiplier,
                debit_credit=dist.debit_credit,
                description=dist.description,
                memo=dist.memo,
                reference_id=dist.reference_id,
                cost_center=dist.cost_center,
                department=dist.department,
                project_id=dist.project_id,
                budget_envelope_id=dist.budget_envelope_id,
                payment_envelope_id=dist.payment_envelope_id,
                status=dist.status,
            )
            db.add(db_dist)

        db.commit()
        db.refresh(db_entry)
        return JournalEntryRepository._to_pydantic(db_entry)

    @staticmethod
    def get_by_id(db: Session, entry_id: str) -> Optional[JournalEntry]:
        """Get journal entry by ID."""
        db_entry = db.query(JournalEntryDB).filter(
            JournalEntryDB.journal_entry_id == entry_id
        ).first()
        return JournalEntryRepository._to_pydantic(db_entry) if db_entry else None

    @staticmethod
    def get_all(
        db: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[JournalEntry]:
        """Get all journal entries with optional filters."""
        query = db.query(JournalEntryDB)

        if start_date:
            query = query.filter(JournalEntryDB.entry_date >= start_date)
        if end_date:
            query = query.filter(JournalEntryDB.entry_date <= end_date)
        if status:
            query = query.filter(JournalEntryDB.status == status)

        query = query.order_by(JournalEntryDB.entry_date.desc())

        if limit:
            query = query.limit(limit)

        db_entries = query.all()
        return [JournalEntryRepository._to_pydantic(entry) for entry in db_entries]

    @staticmethod
    def update(db: Session, entry_id: str, entry: JournalEntry) -> JournalEntry:
        """Update a journal entry and its distributions."""
        db_entry = db.query(JournalEntryDB).filter(
            JournalEntryDB.journal_entry_id == entry_id
        ).first()

        if not db_entry:
            raise ValueError(f"Journal entry {entry_id} not found")

        # Update journal entry fields
        db_entry.entry_number = entry.entry_number
        db_entry.entry_type = entry.entry_type
        db_entry.entry_date = entry.entry_date
        db_entry.posting_date = entry.posting_date
        db_entry.description = entry.description
        db_entry.memo = entry.memo
        db_entry.notes = entry.notes
        db_entry.source_document = entry.source_document
        db_entry.transaction_id = entry.transaction_id
        db_entry.recurring_entry_id = entry.recurring_entry_id
        db_entry.reversed_entry_id = entry.reversed_entry_id
        db_entry.category = entry.category
        db_entry.tags = entry.tags or []
        db_entry.status = entry.status
        db_entry.created_by = entry.created_by
        db_entry.approved_by = entry.approved_by
        db_entry.approved_at = entry.approved_at
        db_entry.posted_by = entry.posted_by
        db_entry.posted_at = entry.posted_at
        db_entry.revision_number = entry.revision_number
        db_entry.previous_version_id = entry.previous_version_id
        db_entry.updated_at = datetime.utcnow()

        # Delete existing distributions
        db.query(DistributionDB).filter(
            DistributionDB.journal_entry_id == entry_id
        ).delete()

        # Add updated distributions
        for dist in entry.distributions:
            db_dist = DistributionDB(
                distribution_id=dist.distribution_id,
                journal_entry_id=entry_id,
                account_id=dist.account_id,
                account_type=dist.account_type,
                flow_direction=dist.flow_direction,
                amount=dist.amount,
                multiplier=dist.multiplier,
                debit_credit=dist.debit_credit,
                description=dist.description,
                memo=dist.memo,
                reference_id=dist.reference_id,
                cost_center=dist.cost_center,
                department=dist.department,
                project_id=dist.project_id,
                budget_envelope_id=dist.budget_envelope_id,
                payment_envelope_id=dist.payment_envelope_id,
                status=dist.status,
            )
            db.add(db_dist)

        db.commit()
        db.refresh(db_entry)
        return JournalEntryRepository._to_pydantic(db_entry)

    @staticmethod
    def delete(db: Session, entry_id: str):
        """Delete a journal entry and its distributions."""
        db_entry = db.query(JournalEntryDB).filter(
            JournalEntryDB.journal_entry_id == entry_id
        ).first()

        if db_entry:
            db.delete(db_entry)  # Cascade will delete distributions
            db.commit()

    @staticmethod
    def _to_pydantic(db_entry: JournalEntryDB) -> JournalEntry:
        """Convert SQLAlchemy model to Pydantic model."""
        distributions = [
            Distribution(
                distribution_id=d.distribution_id,
                account_id=d.account_id,
                account_type=d.account_type,
                flow_direction=d.flow_direction,
                amount=d.amount,
                multiplier=d.multiplier,
                debit_credit=d.debit_credit,
                description=d.description,
                memo=d.memo,
                reference_id=d.reference_id,
                cost_center=d.cost_center,
                department=d.department,
                project_id=d.project_id,
                budget_envelope_id=d.budget_envelope_id,
                payment_envelope_id=d.payment_envelope_id,
                status=d.status,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in db_entry.distributions
        ]

        return JournalEntry(
            journal_entry_id=db_entry.journal_entry_id,
            entry_number=db_entry.entry_number,
            entry_type=db_entry.entry_type,
            entry_date=db_entry.entry_date,
            posting_date=db_entry.posting_date,
            distributions=distributions,
            description=db_entry.description,
            memo=db_entry.memo,
            notes=db_entry.notes,
            source_document=db_entry.source_document,
            transaction_id=db_entry.transaction_id,
            recurring_entry_id=db_entry.recurring_entry_id,
            reversed_entry_id=db_entry.reversed_entry_id,
            category=db_entry.category,
            tags=db_entry.tags or [],
            status=db_entry.status,
            created_by=db_entry.created_by,
            approved_by=db_entry.approved_by,
            approved_at=db_entry.approved_at,
            posted_by=db_entry.posted_by,
            posted_at=db_entry.posted_at,
            created_at=db_entry.created_at,
            updated_at=db_entry.updated_at,
            revision_number=db_entry.revision_number,
            previous_version_id=db_entry.previous_version_id,
        )


# ============================================================================
# BUDGET ENVELOPE REPOSITORY
# ============================================================================

class BudgetEnvelopeRepository:
    """Repository for Budget Envelope CRUD operations."""

    @staticmethod
    def create(db: Session, envelope: BudgetEnvelope) -> BudgetEnvelope:
        """Create a new budget envelope."""
        db_envelope = BudgetEnvelopeDB(
            envelope_id=envelope.envelope_id,
            envelope_number=envelope.envelope_number,
            envelope_name=envelope.envelope_name,
            monthly_allocation=envelope.monthly_allocation,
            rollover_policy=envelope.rollover_policy,
            current_balance=envelope.current_balance,
            is_active=envelope.is_active,
            description=envelope.description,
        )
        db.add(db_envelope)
        db.commit()
        db.refresh(db_envelope)
        return BudgetEnvelopeRepository._to_pydantic(db_envelope)

    @staticmethod
    def get_by_id(db: Session, envelope_id: str) -> Optional[BudgetEnvelope]:
        """Get budget envelope by ID."""
        db_envelope = db.query(BudgetEnvelopeDB).filter(
            BudgetEnvelopeDB.envelope_id == envelope_id
        ).first()
        return BudgetEnvelopeRepository._to_pydantic(db_envelope) if db_envelope else None

    @staticmethod
    def get_all(db: Session, active_only: bool = False) -> List[BudgetEnvelope]:
        """Get all budget envelopes."""
        query = db.query(BudgetEnvelopeDB)

        if active_only:
            query = query.filter(BudgetEnvelopeDB.is_active == True)

        db_envelopes = query.all()
        return [BudgetEnvelopeRepository._to_pydantic(env) for env in db_envelopes]

    @staticmethod
    def update(db: Session, envelope_id: str, envelope: BudgetEnvelope) -> BudgetEnvelope:
        """Update a budget envelope."""
        db_envelope = db.query(BudgetEnvelopeDB).filter(
            BudgetEnvelopeDB.envelope_id == envelope_id
        ).first()

        if not db_envelope:
            raise ValueError(f"Budget envelope {envelope_id} not found")

        db_envelope.envelope_number = envelope.envelope_number
        db_envelope.envelope_name = envelope.envelope_name
        db_envelope.monthly_allocation = envelope.monthly_allocation
        db_envelope.rollover_policy = envelope.rollover_policy
        db_envelope.current_balance = envelope.current_balance
        db_envelope.is_active = envelope.is_active
        db_envelope.description = envelope.description
        db_envelope.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_envelope)
        return BudgetEnvelopeRepository._to_pydantic(db_envelope)

    @staticmethod
    def delete(db: Session, envelope_id: str):
        """Delete a budget envelope."""
        db_envelope = db.query(BudgetEnvelopeDB).filter(
            BudgetEnvelopeDB.envelope_id == envelope_id
        ).first()

        if db_envelope:
            db.delete(db_envelope)
            db.commit()

    @staticmethod
    def _to_pydantic(db_envelope: BudgetEnvelopeDB) -> BudgetEnvelope:
        """Convert SQLAlchemy model to Pydantic model."""
        return BudgetEnvelope(
            envelope_id=db_envelope.envelope_id,
            envelope_number=db_envelope.envelope_number,
            envelope_name=db_envelope.envelope_name,
            monthly_allocation=db_envelope.monthly_allocation,
            rollover_policy=db_envelope.rollover_policy,
            current_balance=db_envelope.current_balance,
            is_active=db_envelope.is_active,
            description=db_envelope.description,
            created_at=db_envelope.created_at,
            updated_at=db_envelope.updated_at,
        )


# ============================================================================
# PAYMENT ENVELOPE REPOSITORY
# ============================================================================

class PaymentEnvelopeRepository:
    """Repository for Payment Envelope CRUD operations."""

    @staticmethod
    def create(db: Session, envelope: PaymentEnvelope) -> PaymentEnvelope:
        """Create a new payment envelope."""
        db_envelope = PaymentEnvelopeDB(
            envelope_id=envelope.envelope_id,
            envelope_number=envelope.envelope_number,
            envelope_name=envelope.envelope_name,
            linked_account_id=envelope.linked_account_id,
            current_balance=envelope.current_balance,
            is_active=envelope.is_active,
            description=envelope.description,
        )
        db.add(db_envelope)
        db.commit()
        db.refresh(db_envelope)
        return PaymentEnvelopeRepository._to_pydantic(db_envelope)

    @staticmethod
    def get_by_id(db: Session, envelope_id: str) -> Optional[PaymentEnvelope]:
        """Get payment envelope by ID."""
        db_envelope = db.query(PaymentEnvelopeDB).filter(
            PaymentEnvelopeDB.envelope_id == envelope_id
        ).first()
        return PaymentEnvelopeRepository._to_pydantic(db_envelope) if db_envelope else None

    @staticmethod
    def get_all(db: Session, active_only: bool = False) -> List[PaymentEnvelope]:
        """Get all payment envelopes."""
        query = db.query(PaymentEnvelopeDB)

        if active_only:
            query = query.filter(PaymentEnvelopeDB.is_active == True)

        db_envelopes = query.all()
        return [PaymentEnvelopeRepository._to_pydantic(env) for env in db_envelopes]

    @staticmethod
    def update(db: Session, envelope_id: str, envelope: PaymentEnvelope) -> PaymentEnvelope:
        """Update a payment envelope."""
        db_envelope = db.query(PaymentEnvelopeDB).filter(
            PaymentEnvelopeDB.envelope_id == envelope_id
        ).first()

        if not db_envelope:
            raise ValueError(f"Payment envelope {envelope_id} not found")

        db_envelope.envelope_number = envelope.envelope_number
        db_envelope.envelope_name = envelope.envelope_name
        db_envelope.linked_account_id = envelope.linked_account_id
        db_envelope.current_balance = envelope.current_balance
        db_envelope.is_active = envelope.is_active
        db_envelope.description = envelope.description
        db_envelope.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_envelope)
        return PaymentEnvelopeRepository._to_pydantic(db_envelope)

    @staticmethod
    def delete(db: Session, envelope_id: str):
        """Delete a payment envelope."""
        db_envelope = db.query(PaymentEnvelopeDB).filter(
            PaymentEnvelopeDB.envelope_id == envelope_id
        ).first()

        if db_envelope:
            db.delete(db_envelope)
            db.commit()

    @staticmethod
    def _to_pydantic(db_envelope: PaymentEnvelopeDB) -> PaymentEnvelope:
        """Convert SQLAlchemy model to Pydantic model."""
        return PaymentEnvelope(
            envelope_id=db_envelope.envelope_id,
            envelope_number=db_envelope.envelope_number,
            envelope_name=db_envelope.envelope_name,
            linked_account_id=db_envelope.linked_account_id,
            current_balance=db_envelope.current_balance,
            is_active=db_envelope.is_active,
            description=db_envelope.description,
            created_at=db_envelope.created_at,
            updated_at=db_envelope.updated_at,
        )


# ============================================================================
# RECURRING JOURNAL ENTRY REPOSITORY
# ============================================================================

class RecurringJournalEntryRepository:
    """Repository for Recurring Journal Entry CRUD operations."""

    @staticmethod
    def create(db: Session, template: RecurringJournalEntry) -> RecurringJournalEntry:
        """Create a new recurring template."""
        # Convert distributions to JSON
        distributions_json = [dist.dict() for dist in template.distributions]

        db_template = RecurringJournalEntryDB(
            recurring_entry_id=template.recurring_entry_id,
            template_name=template.template_name,
            description=template.description,
            entry_type=template.entry_type,
            frequency=template.frequency,
            start_date=template.start_date,
            end_date=template.end_date,
            last_generated_date=template.last_generated_date,
            is_active=template.is_active,
            auto_post=template.auto_post,
            distributions=distributions_json,
            category=template.category,
            tags=template.tags or [],
            notes=template.notes,
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return RecurringJournalEntryRepository._to_pydantic(db_template)

    @staticmethod
    def get_by_id(db: Session, template_id: str) -> Optional[RecurringJournalEntry]:
        """Get recurring template by ID."""
        db_template = db.query(RecurringJournalEntryDB).filter(
            RecurringJournalEntryDB.recurring_entry_id == template_id
        ).first()
        return RecurringJournalEntryRepository._to_pydantic(db_template) if db_template else None

    @staticmethod
    def get_all(db: Session, active_only: bool = False) -> List[RecurringJournalEntry]:
        """Get all recurring templates."""
        query = db.query(RecurringJournalEntryDB)

        if active_only:
            query = query.filter(RecurringJournalEntryDB.is_active == True)

        db_templates = query.all()
        return [RecurringJournalEntryRepository._to_pydantic(t) for t in db_templates]

    @staticmethod
    def update(db: Session, template_id: str, template: RecurringJournalEntry) -> RecurringJournalEntry:
        """Update a recurring template."""
        db_template = db.query(RecurringJournalEntryDB).filter(
            RecurringJournalEntryDB.recurring_entry_id == template_id
        ).first()

        if not db_template:
            raise ValueError(f"Recurring template {template_id} not found")

        distributions_json = [dist.dict() for dist in template.distributions]

        db_template.template_name = template.template_name
        db_template.description = template.description
        db_template.entry_type = template.entry_type
        db_template.frequency = template.frequency
        db_template.start_date = template.start_date
        db_template.end_date = template.end_date
        db_template.last_generated_date = template.last_generated_date
        db_template.is_active = template.is_active
        db_template.auto_post = template.auto_post
        db_template.distributions = distributions_json
        db_template.category = template.category
        db_template.tags = template.tags or []
        db_template.notes = template.notes
        db_template.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_template)
        return RecurringJournalEntryRepository._to_pydantic(db_template)

    @staticmethod
    def delete(db: Session, template_id: str):
        """Delete a recurring template."""
        db_template = db.query(RecurringJournalEntryDB).filter(
            RecurringJournalEntryDB.recurring_entry_id == template_id
        ).first()

        if db_template:
            db.delete(db_template)
            db.commit()

    @staticmethod
    def _to_pydantic(db_template: RecurringJournalEntryDB) -> RecurringJournalEntry:
        """Convert SQLAlchemy model to Pydantic model."""
        # Convert JSON distributions back to Pydantic models
        distributions = [Distribution(**d) for d in db_template.distributions]

        return RecurringJournalEntry(
            recurring_entry_id=db_template.recurring_entry_id,
            template_name=db_template.template_name,
            description=db_template.description,
            entry_type=db_template.entry_type,
            frequency=db_template.frequency,
            start_date=db_template.start_date,
            end_date=db_template.end_date,
            last_generated_date=db_template.last_generated_date,
            is_active=db_template.is_active,
            auto_post=db_template.auto_post,
            distributions=distributions,
            category=db_template.category,
            tags=db_template.tags or [],
            notes=db_template.notes,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at,
        )
