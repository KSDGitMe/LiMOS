"""
LiMOS Accounting API - FastAPI Application with Database Persistence

REST API for the LiMOS accounting module with SQLite database backend.
"""

from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session

# Import models
from ..models.journal_entries import (
    JournalEntry,
    Distribution,
    ChartOfAccounts,
    AccountBalance,
    AccountLedger,
    RecurringJournalEntry,
    AccountType,
    FlowDirection,
    JournalEntryStatus,
    RecurrenceFrequency
)
from ..models.budget_envelopes import (
    BudgetEnvelope,
    PaymentEnvelope,
    BudgetAllocation,
    EnvelopeTransaction,
    BankAccountView,
    RolloverPolicy
)

# Import database
from ..database.database import init_database, get_db_session
from ..database.repositories import (
    ChartOfAccountsRepository,
    JournalEntryRepository,
    BudgetEnvelopeRepository,
    PaymentEnvelopeRepository,
    RecurringJournalEntryRepository
)

# Import services
from ..services.envelope_service import EnvelopeService
from ..services.recurring_transaction_service import RecurringTransactionService

# Initialize FastAPI app
app = FastAPI(
    title="LiMOS Accounting API",
    description="REST API for double-entry accounting with virtual envelope budgeting (Database-backed)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
envelope_service = EnvelopeService()
recurring_service = RecurringTransactionService()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_database()
    print("✅ Database initialized and ready!")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "LiMOS Accounting API (Database-backed)",
        "version": "2.0.0",
        "endpoints": {
            "docs": "/docs",
            "journal_entries": "/api/journal-entries",
            "accounts": "/api/accounts",
            "envelopes": "/api/envelopes",
            "recurring": "/api/recurring-templates",
            "forecast": "/api/forecast"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db_session)):
    """Detailed health check."""
    accounts_count = len(ChartOfAccountsRepository.get_all(db))
    entries_count = len(JournalEntryRepository.get_all(db))
    budget_env_count = len(BudgetEnvelopeRepository.get_all(db))
    payment_env_count = len(PaymentEnvelopeRepository.get_all(db))
    recurring_count = len(RecurringJournalEntryRepository.get_all(db))

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
        "data_loaded": {
            "chart_of_accounts": accounts_count,
            "journal_entries": entries_count,
            "budget_envelopes": budget_env_count,
            "payment_envelopes": payment_env_count,
            "recurring_templates": recurring_count
        }
    }


# ============================================================================
# JOURNAL ENTRIES
# ============================================================================

@app.post("/api/journal-entries", response_model=JournalEntry, status_code=status.HTTP_201_CREATED, tags=["Journal Entries"])
async def create_journal_entry(entry: JournalEntry, db: Session = Depends(get_db_session)):
    """
    Create a new journal entry.

    Validates that the entry is balanced (FROM total = TO total) before saving.
    """
    # Validate balanced
    if not entry.is_balanced():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Journal entry is not balanced. FROM: {sum(d.amount for d in entry.get_from_distributions())}, "
                   f"TO: {sum(d.amount for d in entry.get_to_distributions())}"
        )

    # Save to database
    created_entry = JournalEntryRepository.create(db, entry)

    # If posted, update envelopes
    if entry.status == JournalEntryStatus.POSTED:
        envelope_service.post_journal_entry(entry)

    return created_entry


@app.get("/api/journal-entries", response_model=List[JournalEntry], tags=["Journal Entries"])
async def list_journal_entries(
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    status: Optional[JournalEntryStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of entries to return"),
    db: Session = Depends(get_db_session)
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


@app.get("/api/journal-entries/{entry_id}", response_model=JournalEntry, tags=["Journal Entries"])
async def get_journal_entry(entry_id: str, db: Session = Depends(get_db_session)):
    """Get a specific journal entry by ID."""
    entry = JournalEntryRepository.get_by_id(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )
    return entry


@app.put("/api/journal-entries/{entry_id}", response_model=JournalEntry, tags=["Journal Entries"])
async def update_journal_entry(entry_id: str, entry: JournalEntry, db: Session = Depends(get_db_session)):
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

    # Validate balanced
    if not entry.is_balanced():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Journal entry is not balanced. FROM: {sum(d.amount for d in entry.get_from_distributions())}, "
                   f"TO: {sum(d.amount for d in entry.get_to_distributions())}"
        )

    # Ensure the entry_id matches
    entry.journal_entry_id = entry_id

    updated_entry = JournalEntryRepository.update(db, entry_id, entry)
    return updated_entry


@app.delete("/api/journal-entries/{entry_id}", tags=["Journal Entries"])
async def void_journal_entry(entry_id: str, db: Session = Depends(get_db_session)):
    """Void a journal entry."""
    entry = JournalEntryRepository.get_by_id(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )

    JournalEntryRepository.update(db, entry_id, {"status": "void"})
    return {"message": f"Journal entry {entry_id} voided successfully"}


@app.post("/api/journal-entries/{entry_id}/post", response_model=JournalEntry, tags=["Journal Entries"])
async def post_journal_entry(entry_id: str, db: Session = Depends(get_db_session)):
    """
    Post a journal entry.

    Changes status to POSTED and updates envelope balances.
    """
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

    # Update status
    updated_entry = JournalEntryRepository.update(db, entry_id, {
        "status": "posted",
        "posted_at": datetime.utcnow()
    })

    # Update envelopes
    envelope_service.post_journal_entry(entry)

    return updated_entry


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

@app.get("/api/accounts", response_model=List[ChartOfAccounts], tags=["Chart of Accounts"])
async def list_accounts(
    account_type: Optional[AccountType] = Query(None, description="Filter by account type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db_session)
):
    """List all accounts in the chart of accounts."""
    accounts = ChartOfAccountsRepository.get_all(
        db,
        account_type=account_type.value if account_type else None,
        is_active=is_active
    )
    return accounts


@app.get("/api/accounts/{account_id}", response_model=ChartOfAccounts, tags=["Chart of Accounts"])
async def get_account(account_id: str, db: Session = Depends(get_db_session)):
    """Get a specific account by ID."""
    account = ChartOfAccountsRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    return account


@app.post("/api/accounts", response_model=ChartOfAccounts, status_code=status.HTTP_201_CREATED, tags=["Chart of Accounts"])
async def create_account(account: ChartOfAccounts, db: Session = Depends(get_db_session)):
    """Create a new account."""
    created_account = ChartOfAccountsRepository.create(db, account)
    return created_account


@app.put("/api/accounts/{account_id}", response_model=ChartOfAccounts, tags=["Chart of Accounts"])
async def update_account(account_id: str, account: ChartOfAccounts, db: Session = Depends(get_db_session)):
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

@app.get("/api/envelopes/budget", response_model=List[BudgetEnvelope], tags=["Envelopes"])
async def list_budget_envelopes(
    active_only: bool = Query(False, description="Return only active envelopes"),
    db: Session = Depends(get_db_session)
):
    """List all budget envelopes."""
    envelopes = BudgetEnvelopeRepository.get_all(db, active_only=active_only)
    return envelopes


@app.get("/api/envelopes/budget/{envelope_id}", response_model=BudgetEnvelope, tags=["Envelopes"])
async def get_budget_envelope(envelope_id: str, db: Session = Depends(get_db_session)):
    """Get a specific budget envelope."""
    envelope = BudgetEnvelopeRepository.get_by_id(db, envelope_id)
    if not envelope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget envelope {envelope_id} not found"
        )
    return envelope


@app.post("/api/envelopes/budget", response_model=BudgetEnvelope, status_code=status.HTTP_201_CREATED, tags=["Envelopes"])
async def create_budget_envelope(envelope: BudgetEnvelope, db: Session = Depends(get_db_session)):
    """Create a new budget envelope."""
    created_envelope = BudgetEnvelopeRepository.create(db, envelope)
    return created_envelope


@app.put("/api/envelopes/budget/{envelope_id}", response_model=BudgetEnvelope, tags=["Envelopes"])
async def update_budget_envelope(envelope_id: str, envelope: BudgetEnvelope, db: Session = Depends(get_db_session)):
    """Update a budget envelope."""
    existing = BudgetEnvelopeRepository.get_by_id(db, envelope_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget envelope {envelope_id} not found"
        )

    updated_envelope = BudgetEnvelopeRepository.update(db, envelope_id, envelope)
    return updated_envelope


@app.delete("/api/envelopes/budget/{envelope_id}", tags=["Envelopes"])
async def delete_budget_envelope(envelope_id: str, db: Session = Depends(get_db_session)):
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

@app.get("/api/envelopes/payment", response_model=List[PaymentEnvelope], tags=["Envelopes"])
async def list_payment_envelopes(
    active_only: bool = Query(False, description="Return only active envelopes"),
    db: Session = Depends(get_db_session)
):
    """List all payment envelopes."""
    envelopes = PaymentEnvelopeRepository.get_all(db, active_only=active_only)
    return envelopes


@app.get("/api/envelopes/payment/{envelope_id}", response_model=PaymentEnvelope, tags=["Envelopes"])
async def get_payment_envelope(envelope_id: str, db: Session = Depends(get_db_session)):
    """Get a specific payment envelope."""
    envelope = PaymentEnvelopeRepository.get_by_id(db, envelope_id)
    if not envelope:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment envelope {envelope_id} not found"
        )
    return envelope


@app.post("/api/envelopes/payment", response_model=PaymentEnvelope, status_code=status.HTTP_201_CREATED, tags=["Envelopes"])
async def create_payment_envelope(envelope: PaymentEnvelope, db: Session = Depends(get_db_session)):
    """Create a new payment envelope."""
    created_envelope = PaymentEnvelopeRepository.create(db, envelope)
    return created_envelope


@app.put("/api/envelopes/payment/{envelope_id}", response_model=PaymentEnvelope, tags=["Envelopes"])
async def update_payment_envelope(envelope_id: str, envelope: PaymentEnvelope, db: Session = Depends(get_db_session)):
    """Update a payment envelope."""
    existing = PaymentEnvelopeRepository.get_by_id(db, envelope_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment envelope {envelope_id} not found"
        )

    updated_envelope = PaymentEnvelopeRepository.update(db, envelope_id, envelope)
    return updated_envelope


@app.delete("/api/envelopes/payment/{envelope_id}", tags=["Envelopes"])
async def delete_payment_envelope(envelope_id: str, db: Session = Depends(get_db_session)):
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

@app.get("/api/recurring-templates", response_model=List[RecurringJournalEntry], tags=["Recurring"])
async def list_recurring_templates(
    active_only: bool = Query(False, description="Return only active templates"),
    db: Session = Depends(get_db_session)
):
    """List all recurring journal entry templates."""
    templates = RecurringJournalEntryRepository.get_all(db, active_only=active_only)
    return templates


@app.get("/api/recurring-templates/{template_id}", response_model=RecurringJournalEntry, tags=["Recurring"])
async def get_recurring_template(template_id: str, db: Session = Depends(get_db_session)):
    """Get a specific recurring template."""
    template = RecurringJournalEntryRepository.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring template {template_id} not found"
        )
    return template


@app.post("/api/recurring-templates", response_model=RecurringJournalEntry, status_code=status.HTTP_201_CREATED, tags=["Recurring"])
async def create_recurring_template(template: RecurringJournalEntry, db: Session = Depends(get_db_session)):
    """Create a new recurring template."""
    created_template = RecurringJournalEntryRepository.create(db, template)
    return created_template


@app.put("/api/recurring-templates/{template_id}", response_model=RecurringJournalEntry, tags=["Recurring"])
async def update_recurring_template(template_id: str, template: RecurringJournalEntry, db: Session = Depends(get_db_session)):
    """Update a recurring template."""
    existing = RecurringJournalEntryRepository.get_by_id(db, template_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring template {template_id} not found"
        )

    updated_template = RecurringJournalEntryRepository.update(db, template_id, template)
    return updated_template


@app.patch("/api/recurring-templates/{template_id}/toggle-active", response_model=RecurringJournalEntry, tags=["Recurring"])
async def toggle_recurring_template(template_id: str, db: Session = Depends(get_db_session)):
    """Toggle active status of a recurring template."""
    template = RecurringJournalEntryRepository.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring template {template_id} not found"
        )

    # Toggle is_active
    template.is_active = not template.is_active
    updated_template = RecurringJournalEntryRepository.update(db, template_id, template)
    return updated_template


@app.delete("/api/recurring-templates/{template_id}", tags=["Recurring"])
async def delete_recurring_template(template_id: str, db: Session = Depends(get_db_session)):
    """Delete a recurring template."""
    existing = RecurringJournalEntryRepository.get_by_id(db, template_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring template {template_id} not found"
        )

    RecurringJournalEntryRepository.delete(db, template_id)
    return {"message": f"Recurring template {template_id} deleted successfully"}


@app.post("/api/recurring-templates/expand", response_model=List[JournalEntry], tags=["Recurring"])
async def expand_recurring_templates(
    start_date: str = Query(..., description="Start date (ISO format)"),
    end_date: str = Query(..., description="End date (ISO format)"),
    auto_post: bool = Query(False, description="Automatically post generated entries"),
    db: Session = Depends(get_db_session)
):
    """
    Expand all active recurring templates into journal entries for the specified date range.
    """
    templates = RecurringJournalEntryRepository.get_all(db, active_only=True)
    generated_entries = []

    for template in templates:
        entries = recurring_service.expand_recurring_entry(
            template=template,
            start_date=start_date,
            end_date=end_date
        )

        for entry in entries:
            # Set status based on auto_post
            if auto_post and template.auto_post:
                entry.status = JournalEntryStatus.POSTED
                entry.posted_at = datetime.utcnow()

            # Save to database
            created_entry = JournalEntryRepository.create(db, entry)
            generated_entries.append(created_entry)

    return generated_entries


# ============================================================================
# FORECASTING (Placeholder - to be implemented)
# ============================================================================

@app.get("/api/forecast/account/{account_id}", tags=["Forecasting"])
async def forecast_account(
    account_id: str,
    target_date: str = Query(..., description="Target date for forecast"),
    db: Session = Depends(get_db_session)
):
    """
    Forecast account balance based on recurring transactions.

    NOTE: This is a simplified implementation that returns current balance as projection.
    Full forecasting logic with recurring transactions needs to be implemented.
    """
    from datetime import datetime

    # Get account details
    account = ChartOfAccountsRepository.get_by_id(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    # For now, return current balance as projected balance
    # TODO: Implement actual forecasting logic with recurring transactions
    current_balance = account.current_balance
    as_of_date = datetime.now().strftime("%Y-%m-%d")

    return {
        "account_id": account_id,
        "account_name": account.account_name,
        "current_balance": current_balance,
        "as_of_date": as_of_date,
        "target_date": target_date,
        "projected_balance": current_balance,  # TODO: Calculate based on recurring transactions
        "balance_change": 0.0,  # TODO: Calculate based on recurring transactions
        "transactions_applied": 0
    }


@app.get("/api/forecast/envelope/{envelope_id}", tags=["Forecasting"])
async def forecast_envelope(
    envelope_id: str,
    target_date: str = Query(..., description="Target date for forecast"),
    db: Session = Depends(get_db_session)
):
    """
    Forecast envelope balance based on recurring transactions.

    NOTE: This is a simplified implementation that returns current balance as projection.
    Full forecasting logic with recurring transactions needs to be implemented.
    """
    from datetime import datetime

    # Try to get budget envelope first
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

    # Try payment envelope
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

@app.get("/api/stats/summary", tags=["Statistics"])
async def get_stats_summary(db: Session = Depends(get_db_session)):
    """Get system statistics summary."""
    return {
        "accounts": len(ChartOfAccountsRepository.get_all(db)),
        "journal_entries": len(JournalEntryRepository.get_all(db)),
        "budget_envelopes": len(BudgetEnvelopeRepository.get_all(db)),
        "payment_envelopes": len(PaymentEnvelopeRepository.get_all(db)),
        "recurring_templates": len(RecurringJournalEntryRepository.get_all(db)),
    }
