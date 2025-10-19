"""
Accounting Module Router

All accounting endpoints prefixed with /api/accounting/*
"""

from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# Import models from accounting module
from projects.accounting.models.journal_entries import (
    JournalEntry,
    ChartOfAccounts,
    RecurringJournalEntry,
    AccountType,
    JournalEntryStatus,
)
from projects.accounting.models.budget_envelopes import (
    BudgetEnvelope,
    PaymentEnvelope,
)

# Import database from accounting module (backend-agnostic)
from projects.accounting.database import (
    get_db,
    ChartOfAccountsRepository,
    JournalEntryRepository,
    BudgetEnvelopeRepository,
    PaymentEnvelopeRepository,
    RecurringJournalEntryRepository,
    ACCOUNTING_BACKEND
)

# Import services from accounting module
from projects.accounting.services.envelope_service import EnvelopeService
from projects.accounting.services.recurring_transaction_service import RecurringTransactionService

# Initialize router
router = APIRouter()

# Initialize services
envelope_service = EnvelopeService()
recurring_service = RecurringTransactionService()

# Backend-aware database dependency
def get_db_dependency():
    """
    Returns database session or None based on backend.
    For SQL: returns SQLAlchemy session
    For Notion: returns None (Notion repositories don't need sessions)
    """
    if ACCOUNTING_BACKEND == "notion":
        yield None
    else:
        db_gen = get_db()
        db = next(db_gen)
        try:
            yield db
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass


# ============================================================================
# JOURNAL ENTRIES
# ============================================================================

@router.post("/journal-entries", response_model=JournalEntry, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(entry: JournalEntry, db = Depends(get_db_dependency)):
    """Create a new journal entry."""
    # Validate balanced
    if not entry.is_balanced():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Journal entry is not balanced. FROM: {sum(d.amount for d in entry.get_from_distributions())}, "
                   f"TO: {sum(d.amount for d in entry.get_to_distributions())}"
        )

    created_entry = JournalEntryRepository.create(db, entry)

    if entry.status == JournalEntryStatus.POSTED:
        envelope_service.post_journal_entry(entry)

    return created_entry


@router.get("/journal-entries", response_model=List[JournalEntry])
async def list_journal_entries(
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    status: Optional[JournalEntryStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of entries to return"),
    db = Depends(get_db_dependency)
):
    """List journal entries with optional filters."""
    entries = JournalEntryRepository.get_all(
        db,
        start_date=start_date,
        end_date=end_date,
        status=status.value if status else None,
        limit=limit
    )
    return entries


@router.get("/journal-entries/{entry_id}", response_model=JournalEntry)
async def get_journal_entry(entry_id: str, db = Depends(get_db_dependency)):
    """Get a specific journal entry by ID."""
    entry = JournalEntryRepository.get_by_id(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )
    return entry


@router.put("/journal-entries/{entry_id}", response_model=JournalEntry)
async def update_journal_entry(entry_id: str, entry: JournalEntry, db = Depends(get_db_dependency)):
    """Update a journal entry (only if not posted)."""
    existing = JournalEntryRepository.get_by_id(db, entry_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )

    if existing.status == JournalEntryStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a posted journal entry"
        )

    if not entry.is_balanced():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Journal entry is not balanced"
        )

    entry.journal_entry_id = entry_id
    updated_entry = JournalEntryRepository.update(db, entry_id, entry)
    return updated_entry


@router.delete("/journal-entries/{entry_id}")
async def void_journal_entry(entry_id: str, db = Depends(get_db_dependency)):
    """Void a journal entry."""
    entry = JournalEntryRepository.get_by_id(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )

    entry.status = JournalEntryStatus.VOID
    JournalEntryRepository.update(db, entry_id, entry)
    return {"message": f"Journal entry {entry_id} voided successfully"}


@router.post("/journal-entries/{entry_id}/post", response_model=JournalEntry)
async def post_journal_entry(entry_id: str, db = Depends(get_db_dependency)):
    """Post a journal entry - changes status to POSTED and updates envelope balances."""
    entry = JournalEntryRepository.get_by_id(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )

    if entry.status == JournalEntryStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Journal entry is already posted"
        )

    entry.status = JournalEntryStatus.POSTED
    entry.posted_at = datetime.utcnow()
    updated_entry = JournalEntryRepository.update(db, entry_id, entry)
    envelope_service.post_journal_entry(updated_entry)

    return updated_entry


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

@router.get("/accounts", response_model=List[ChartOfAccounts])
async def list_accounts(
    account_type: Optional[AccountType] = Query(None, description="Filter by account type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db = Depends(get_db_dependency)
):
    """List all accounts in the chart of accounts."""
    accounts = ChartOfAccountsRepository.get_all(
        db,
        account_type=account_type.value if account_type else None,
        is_active=is_active
    )
    return accounts


@router.get("/accounts/{account_id}", response_model=ChartOfAccounts)
async def get_account(account_id: str, db = Depends(get_db_dependency)):
    """Get a specific account by ID."""
    account = ChartOfAccountsRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    return account


@router.post("/accounts", response_model=ChartOfAccounts, status_code=status.HTTP_201_CREATED)
async def create_account(account: ChartOfAccounts, db = Depends(get_db_dependency)):
    """Create a new account."""
    created_account = ChartOfAccountsRepository.create(db, account)
    return created_account


@router.put("/accounts/{account_id}", response_model=ChartOfAccounts)
async def update_account(account_id: str, account: ChartOfAccounts, db = Depends(get_db_dependency)):
    """Update an existing account."""
    existing = ChartOfAccountsRepository.get_by_id(db, account_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    updated_account = ChartOfAccountsRepository.update(db, account_id, account)
    return updated_account


# ============================================================================
# BUDGET ENVELOPES
# ============================================================================

@router.get("/envelopes/budget", response_model=List[BudgetEnvelope])
async def list_budget_envelopes(
    active_only: bool = Query(False, description="Return only active envelopes"),
    db = Depends(get_db_dependency)
):
    """List all budget envelopes."""
    envelopes = BudgetEnvelopeRepository.get_all(db, active_only=active_only)
    return envelopes


@router.get("/envelopes/budget/{envelope_id}", response_model=BudgetEnvelope)
async def get_budget_envelope(envelope_id: str, db = Depends(get_db_dependency)):
    """Get a specific budget envelope."""
    envelope = BudgetEnvelopeRepository.get_by_id(db, envelope_id)
    if not envelope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget envelope {envelope_id} not found"
        )
    return envelope


@router.post("/envelopes/budget", response_model=BudgetEnvelope, status_code=status.HTTP_201_CREATED)
async def create_budget_envelope(envelope: BudgetEnvelope, db = Depends(get_db_dependency)):
    """Create a new budget envelope."""
    created_envelope = BudgetEnvelopeRepository.create(db, envelope)
    return created_envelope


@router.put("/envelopes/budget/{envelope_id}", response_model=BudgetEnvelope)
async def update_budget_envelope(envelope_id: str, envelope: BudgetEnvelope, db = Depends(get_db_dependency)):
    """Update a budget envelope."""
    existing = BudgetEnvelopeRepository.get_by_id(db, envelope_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget envelope {envelope_id} not found"
        )

    updated_envelope = BudgetEnvelopeRepository.update(db, envelope_id, envelope)
    return updated_envelope


@router.delete("/envelopes/budget/{envelope_id}")
async def delete_budget_envelope(envelope_id: str, db = Depends(get_db_dependency)):
    """Delete a budget envelope."""
    existing = BudgetEnvelopeRepository.get_by_id(db, envelope_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget envelope {envelope_id} not found"
        )

    BudgetEnvelopeRepository.delete(db, envelope_id)
    return {"message": f"Budget envelope {envelope_id} deleted successfully"}


# ============================================================================
# PAYMENT ENVELOPES
# ============================================================================

@router.get("/envelopes/payment", response_model=List[PaymentEnvelope])
async def list_payment_envelopes(
    active_only: bool = Query(False, description="Return only active envelopes"),
    db = Depends(get_db_dependency)
):
    """List all payment envelopes."""
    envelopes = PaymentEnvelopeRepository.get_all(db, active_only=active_only)
    return envelopes


@router.get("/envelopes/payment/{envelope_id}", response_model=PaymentEnvelope)
async def get_payment_envelope(envelope_id: str, db = Depends(get_db_dependency)):
    """Get a specific payment envelope."""
    envelope = PaymentEnvelopeRepository.get_by_id(db, envelope_id)
    if not envelope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment envelope {envelope_id} not found"
        )
    return envelope


@router.post("/envelopes/payment", response_model=PaymentEnvelope, status_code=status.HTTP_201_CREATED)
async def create_payment_envelope(envelope: PaymentEnvelope, db = Depends(get_db_dependency)):
    """Create a new payment envelope."""
    created_envelope = PaymentEnvelopeRepository.create(db, envelope)
    return created_envelope


@router.put("/envelopes/payment/{envelope_id}", response_model=PaymentEnvelope)
async def update_payment_envelope(envelope_id: str, envelope: PaymentEnvelope, db = Depends(get_db_dependency)):
    """Update a payment envelope."""
    existing = PaymentEnvelopeRepository.get_by_id(db, envelope_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment envelope {envelope_id} not found"
        )

    updated_envelope = PaymentEnvelopeRepository.update(db, envelope_id, envelope)
    return updated_envelope


@router.delete("/envelopes/payment/{envelope_id}")
async def delete_payment_envelope(envelope_id: str, db = Depends(get_db_dependency)):
    """Delete a payment envelope."""
    existing = PaymentEnvelopeRepository.get_by_id(db, envelope_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment envelope {envelope_id} not found"
        )

    PaymentEnvelopeRepository.delete(db, envelope_id)
    return {"message": f"Payment envelope {envelope_id} deleted successfully"}


# ============================================================================
# RECURRING TEMPLATES
# ============================================================================

@router.get("/recurring-templates", response_model=List[RecurringJournalEntry])
async def list_recurring_templates(
    active_only: bool = Query(False, description="Return only active templates"),
    db = Depends(get_db_dependency)
):
    """List all recurring journal entry templates."""
    templates = RecurringJournalEntryRepository.get_all(db, active_only=active_only)
    return templates


@router.get("/recurring-templates/{template_id}", response_model=RecurringJournalEntry)
async def get_recurring_template(template_id: str, db = Depends(get_db_dependency)):
    """Get a specific recurring template."""
    template = RecurringJournalEntryRepository.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring template {template_id} not found"
        )
    return template


@router.post("/recurring-templates", response_model=RecurringJournalEntry, status_code=status.HTTP_201_CREATED)
async def create_recurring_template(template: RecurringJournalEntry, db = Depends(get_db_dependency)):
    """Create a new recurring template."""
    created_template = RecurringJournalEntryRepository.create(db, template)
    return created_template


@router.put("/recurring-templates/{template_id}", response_model=RecurringJournalEntry)
async def update_recurring_template(template_id: str, template: RecurringJournalEntry, db = Depends(get_db_dependency)):
    """Update a recurring template."""
    existing = RecurringJournalEntryRepository.get_by_id(db, template_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring template {template_id} not found"
        )

    updated_template = RecurringJournalEntryRepository.update(db, template_id, template)
    return updated_template


@router.patch("/recurring-templates/{template_id}/toggle-active", response_model=RecurringJournalEntry)
async def toggle_recurring_template(template_id: str, db = Depends(get_db_dependency)):
    """Toggle active status of a recurring template."""
    template = RecurringJournalEntryRepository.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring template {template_id} not found"
        )

    template.is_active = not template.is_active
    updated_template = RecurringJournalEntryRepository.update(db, template_id, template)
    return updated_template


@router.delete("/recurring-templates/{template_id}")
async def delete_recurring_template(template_id: str, db = Depends(get_db_dependency)):
    """Delete a recurring template."""
    existing = RecurringJournalEntryRepository.get_by_id(db, template_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring template {template_id} not found"
        )

    RecurringJournalEntryRepository.delete(db, template_id)
    return {"message": f"Recurring template {template_id} deleted successfully"}


@router.post("/recurring-templates/expand", response_model=List[JournalEntry])
async def expand_recurring_templates(
    start_date: str = Query(..., description="Start date (ISO format)"),
    end_date: str = Query(..., description="End date (ISO format)"),
    auto_post: bool = Query(False, description="Automatically post generated entries"),
    db = Depends(get_db_dependency)
):
    """Expand all active recurring templates into journal entries for the specified date range."""
    templates = RecurringJournalEntryRepository.get_all(db, active_only=True)
    generated_entries = []

    for template in templates:
        entries = recurring_service.expand_recurring_entry(
            template=template,
            start_date=start_date,
            end_date=end_date
        )

        for entry in entries:
            if auto_post and template.auto_post:
                entry.status = JournalEntryStatus.POSTED
                entry.posted_at = datetime.utcnow()

            created_entry = JournalEntryRepository.create(db, entry)
            generated_entries.append(created_entry)

    return generated_entries


# ============================================================================
# FORECASTING
# ============================================================================

@router.get("/forecast/account/{account_id}")
async def forecast_account(
    account_id: str,
    target_date: str = Query(..., description="Target date for forecast"),
    db = Depends(get_db_dependency)
):
    """Forecast account balance based on recurring transactions."""
    account = ChartOfAccountsRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    current_balance = account.current_balance
    as_of_date = datetime.now().strftime("%Y-%m-%d")

    return {
        "account_id": account_id,
        "account_name": account.account_name,
        "current_balance": current_balance,
        "as_of_date": as_of_date,
        "target_date": target_date,
        "projected_balance": current_balance,
        "balance_change": 0.0,
        "transactions_applied": 0
    }


@router.get("/forecast/envelope/{envelope_id}")
async def forecast_envelope(
    envelope_id: str,
    target_date: str = Query(..., description="Target date for forecast"),
    db = Depends(get_db_dependency)
):
    """Forecast envelope balance based on recurring transactions."""
    budget_envelope = BudgetEnvelopeRepository.get_by_id(db, envelope_id)
    if budget_envelope:
        return {
            "envelope_id": envelope_id,
            "envelope_name": budget_envelope.envelope_name,
            "current_balance": budget_envelope.current_balance,
            "as_of_date": datetime.now().strftime("%Y-%m-%d"),
            "target_date": target_date,
            "projected_balance": budget_envelope.current_balance,
            "balance_change": 0.0,
            "transactions_applied": 0
        }

    payment_envelope = PaymentEnvelopeRepository.get_by_id(db, envelope_id)
    if payment_envelope:
        return {
            "envelope_id": envelope_id,
            "envelope_name": payment_envelope.envelope_name,
            "current_balance": payment_envelope.current_balance,
            "as_of_date": datetime.now().strftime("%Y-%m-%d"),
            "target_date": target_date,
            "projected_balance": payment_envelope.current_balance,
            "balance_change": 0.0,
            "transactions_applied": 0
        }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Envelope {envelope_id} not found"
    )


# ============================================================================
# STATISTICS
# ============================================================================

@router.get("/stats/summary")
async def get_stats_summary(db = Depends(get_db_dependency)):
    """Get system statistics summary."""
    return {
        "accounts": len(ChartOfAccountsRepository.get_all(db)),
        "journal_entries": len(JournalEntryRepository.get_all(db)),
        "budget_envelopes": len(BudgetEnvelopeRepository.get_all(db)),
        "payment_envelopes": len(PaymentEnvelopeRepository.get_all(db)),
        "recurring_templates": len(RecurringJournalEntryRepository.get_all(db)),
    }
