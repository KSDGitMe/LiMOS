"""
LiMOS Accounting API - FastAPI Application

REST API for the LiMOS accounting module providing endpoints for:
- Journal entries and transactions
- Budget and payment envelopes
- Recurring transaction templates
- Account balance forecasting
- Chart of accounts management
"""

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import date, datetime
import json
import os

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

# Import services
from ..services.envelope_service import EnvelopeService
from ..services.recurring_transaction_service import RecurringTransactionService

# Initialize FastAPI app
app = FastAPI(
    title="LiMOS Accounting API",
    description="REST API for double-entry accounting with virtual envelope budgeting",
    version="1.0.0",
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

# In-memory storage (replace with database in production)
journal_entries_db = {}
chart_of_accounts_db = {}
account_balances_db = {}
recurring_templates_db = {}

# Load test data on startup
@app.on_event("startup")
async def startup_event():
    """Load test data into memory on startup."""
    # Load chart of accounts
    coa_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/envelope_test_data.json"
    if os.path.exists(coa_file):
        with open(coa_file, 'r') as f:
            data = json.load(f)
            for account_data in data.get('chart_of_accounts', []):
                account = ChartOfAccounts(**account_data)
                chart_of_accounts_db[account.account_id] = account

            # Load budget envelopes
            for env_data in data.get('budget_envelopes', []):
                envelope = BudgetEnvelope(**env_data)
                envelope_service.create_budget_envelope(envelope)

            # Load payment envelopes
            for env_data in data.get('payment_envelopes', []):
                envelope = PaymentEnvelope(**env_data)
                envelope_service.create_payment_envelope(envelope)

    # Load recurring templates
    templates_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/recurring_templates.json"
    if os.path.exists(templates_file):
        with open(templates_file, 'r') as f:
            templates_data = json.load(f)
            for template_data in templates_data:
                template = RecurringJournalEntry(**template_data)
                recurring_templates_db[template.recurring_entry_id] = template

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "LiMOS Accounting API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "journal_entries": "/api/journal-entries",
            "envelopes": "/api/envelopes",
            "recurring": "/api/recurring-templates",
            "forecast": "/api/forecast"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "data_loaded": {
            "chart_of_accounts": len(chart_of_accounts_db),
            "journal_entries": len(journal_entries_db),
            "budget_envelopes": len(envelope_service.budget_envelopes),
            "payment_envelopes": len(envelope_service.payment_envelopes),
            "recurring_templates": len(recurring_templates_db)
        }
    }

# ============================================================================
# JOURNAL ENTRIES
# ============================================================================

@app.post("/api/journal-entries", response_model=JournalEntry, status_code=status.HTTP_201_CREATED, tags=["Journal Entries"])
async def create_journal_entry(entry: JournalEntry):
    """
    Create a new journal entry.

    Validates that the entry is balanced (FROM total = TO total) before saving.
    Optionally posts the entry and updates envelope balances.
    """
    # Validate balanced
    if not entry.is_balanced():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Journal entry is not balanced. FROM: {sum(d.amount for d in entry.get_from_distributions())}, "
                   f"TO: {sum(d.amount for d in entry.get_to_distributions())}"
        )

    # Save to database
    journal_entries_db[entry.journal_entry_id] = entry

    # If posted, update envelopes
    if entry.status == JournalEntryStatus.POSTED:
        envelope_txns = envelope_service.post_journal_entry(entry)

    return entry

@app.get("/api/journal-entries", response_model=List[JournalEntry], tags=["Journal Entries"])
async def list_journal_entries(
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    status: Optional[JournalEntryStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of entries to return")
):
    """List journal entries with optional filters."""
    entries = list(journal_entries_db.values())

    # Apply filters
    if start_date:
        entries = [e for e in entries if e.entry_date >= start_date]
    if end_date:
        entries = [e for e in entries if e.entry_date <= end_date]
    if status:
        entries = [e for e in entries if e.status == status]

    # Sort by date descending
    entries.sort(key=lambda e: e.entry_date, reverse=True)

    return entries[:limit]

@app.get("/api/journal-entries/{entry_id}", response_model=JournalEntry, tags=["Journal Entries"])
async def get_journal_entry(entry_id: str):
    """Get a specific journal entry by ID."""
    if entry_id not in journal_entries_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )
    return journal_entries_db[entry_id]

@app.put("/api/journal-entries/{entry_id}", response_model=JournalEntry, tags=["Journal Entries"])
async def update_journal_entry(entry_id: str, entry: JournalEntry):
    """Update a journal entry (only if not posted)."""
    if entry_id not in journal_entries_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )

    existing = journal_entries_db[entry_id]
    if existing.status == JournalEntryStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a posted journal entry"
        )

    journal_entries_db[entry_id] = entry
    return entry

@app.delete("/api/journal-entries/{entry_id}", tags=["Journal Entries"])
async def void_journal_entry(entry_id: str):
    """Void a journal entry."""
    if entry_id not in journal_entries_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )

    entry = journal_entries_db[entry_id]
    entry.status = JournalEntryStatus.VOID
    journal_entries_db[entry_id] = entry

    return {"message": f"Journal entry {entry_id} voided successfully"}

@app.post("/api/journal-entries/{entry_id}/post", response_model=JournalEntry, tags=["Journal Entries"])
async def post_journal_entry(entry_id: str):
    """
    Post a journal entry.

    Changes status to POSTED and updates envelope balances.
    """
    if entry_id not in journal_entries_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry {entry_id} not found"
        )

    entry = journal_entries_db[entry_id]

    if entry.status == JournalEntryStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Journal entry is already posted"
        )

    # Update status
    entry.status = JournalEntryStatus.POSTED
    entry.posted_at = datetime.utcnow()

    # Update envelopes
    envelope_txns = envelope_service.post_journal_entry(entry)

    journal_entries_db[entry_id] = entry

    return entry

# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

@app.get("/api/accounts", response_model=List[ChartOfAccounts], tags=["Chart of Accounts"])
async def list_accounts(
    account_type: Optional[AccountType] = Query(None, description="Filter by account type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """List all accounts in the chart of accounts."""
    accounts = list(chart_of_accounts_db.values())

    if account_type:
        accounts = [a for a in accounts if a.account_type == account_type]
    if is_active is not None:
        accounts = [a for a in accounts if a.is_active == is_active]

    # Sort by account number
    accounts.sort(key=lambda a: a.account_number)

    return accounts

@app.get("/api/accounts/{account_id}", response_model=ChartOfAccounts, tags=["Chart of Accounts"])
async def get_account(account_id: str):
    """Get a specific account by ID."""
    if account_id not in chart_of_accounts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )
    return chart_of_accounts_db[account_id]

@app.post("/api/accounts", response_model=ChartOfAccounts, status_code=status.HTTP_201_CREATED, tags=["Chart of Accounts"])
async def create_account(account: ChartOfAccounts):
    """Create a new account in the chart of accounts."""
    chart_of_accounts_db[account.account_id] = account
    return account

# ============================================================================
# BUDGET ENVELOPES
# ============================================================================

@app.get("/api/envelopes/budget", response_model=List[BudgetEnvelope], tags=["Envelopes"])
async def list_budget_envelopes(active_only: bool = Query(True, description="Only return active envelopes")):
    """List all budget envelopes."""
    return envelope_service.list_budget_envelopes(active_only=active_only)

@app.get("/api/envelopes/payment", response_model=List[PaymentEnvelope], tags=["Envelopes"])
async def list_payment_envelopes(active_only: bool = Query(True, description="Only return active envelopes")):
    """List all payment envelopes."""
    return envelope_service.list_payment_envelopes(active_only=active_only)

@app.post("/api/envelopes/budget", response_model=BudgetEnvelope, status_code=status.HTTP_201_CREATED, tags=["Envelopes"])
async def create_budget_envelope(envelope: BudgetEnvelope):
    """Create a new budget envelope."""
    return envelope_service.create_budget_envelope(envelope)

@app.post("/api/envelopes/payment", response_model=PaymentEnvelope, status_code=status.HTTP_201_CREATED, tags=["Envelopes"])
async def create_payment_envelope(envelope: PaymentEnvelope):
    """Create a new payment envelope."""
    return envelope_service.create_payment_envelope(envelope)

@app.put("/api/envelopes/budget/{envelope_id}", response_model=BudgetEnvelope, tags=["Envelopes"])
async def update_budget_envelope(envelope_id: str, envelope: BudgetEnvelope):
    """Update a budget envelope."""
    envelope.envelope_id = envelope_id
    return envelope_service.update_budget_envelope(envelope)

@app.delete("/api/envelopes/budget/{envelope_id}", tags=["Envelopes"])
async def delete_budget_envelope(envelope_id: str):
    """Delete a budget envelope."""
    envelope_service.delete_budget_envelope(envelope_id)
    return {"message": f"Budget envelope {envelope_id} deleted successfully"}

@app.put("/api/envelopes/payment/{envelope_id}", response_model=PaymentEnvelope, tags=["Envelopes"])
async def update_payment_envelope(envelope_id: str, envelope: PaymentEnvelope):
    """Update a payment envelope."""
    envelope.envelope_id = envelope_id
    return envelope_service.update_payment_envelope(envelope)

@app.delete("/api/envelopes/payment/{envelope_id}", tags=["Envelopes"])
async def delete_payment_envelope(envelope_id: str):
    """Delete a payment envelope."""
    envelope_service.delete_payment_envelope(envelope_id)
    return {"message": f"Payment envelope {envelope_id} deleted successfully"}

@app.post("/api/envelopes/allocate", tags=["Envelopes"])
async def apply_monthly_allocations(
    source_account_id: str,
    allocation_date: date,
    period_label: str
):
    """
    Apply monthly budget allocations to all active envelopes.

    This is typically run on the 1st of each month.
    """
    allocations = envelope_service.apply_monthly_allocations(
        source_account_id=source_account_id,
        allocation_date=allocation_date,
        period_label=period_label
    )

    return {
        "message": f"Applied {len(allocations)} monthly allocations",
        "allocations": allocations
    }

@app.get("/api/accounts/{account_id}/view", response_model=BankAccountView, tags=["Envelopes"])
async def get_bank_account_view(
    account_id: str,
    as_of_date: Optional[date] = Query(None, description="Date for the view (defaults to today)")
):
    """
    Get complete bank account view with envelope breakdown.

    Shows: Bank Balance = Budget Allocated + Payment Reserved + Available
    """
    if account_id not in chart_of_accounts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    account = chart_of_accounts_db[account_id]
    as_of = as_of_date or date.today()

    view = envelope_service.get_bank_account_view(
        account_id=account_id,
        account_name=account.account_name,
        bank_balance=account.current_balance,
        as_of_date=as_of
    )

    return view

# ============================================================================
# RECURRING TEMPLATES
# ============================================================================

@app.get("/api/recurring-templates", response_model=List[RecurringJournalEntry], tags=["Recurring Transactions"])
async def list_recurring_templates(active_only: bool = Query(True, description="Only return active templates")):
    """List all recurring transaction templates."""
    templates = list(recurring_templates_db.values())

    if active_only:
        templates = [t for t in templates if t.is_active]

    return templates

@app.get("/api/recurring-templates/{template_id}", response_model=RecurringJournalEntry, tags=["Recurring Transactions"])
async def get_recurring_template(template_id: str):
    """Get a specific recurring template."""
    if template_id not in recurring_templates_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring template {template_id} not found"
        )
    return recurring_templates_db[template_id]

@app.post("/api/recurring-templates", response_model=RecurringJournalEntry, status_code=status.HTTP_201_CREATED, tags=["Recurring Transactions"])
async def create_recurring_template(template: RecurringJournalEntry):
    """Create a new recurring transaction template."""
    recurring_templates_db[template.recurring_entry_id] = template
    return template

@app.put("/api/recurring-templates/{template_id}", response_model=RecurringJournalEntry, tags=["Recurring Transactions"])
async def update_recurring_template(template_id: str, template: RecurringJournalEntry):
    """Update a recurring transaction template."""
    if template_id not in recurring_templates_db:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    template.recurring_entry_id = template_id
    recurring_templates_db[template_id] = template
    return template

@app.delete("/api/recurring-templates/{template_id}", tags=["Recurring Transactions"])
async def delete_recurring_template(template_id: str):
    """Delete a recurring transaction template."""
    if template_id not in recurring_templates_db:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    del recurring_templates_db[template_id]
    return {"message": f"Template {template_id} deleted successfully"}

@app.patch("/api/recurring-templates/{template_id}/toggle-active", response_model=RecurringJournalEntry, tags=["Recurring Transactions"])
async def toggle_template_active(template_id: str):
    """Toggle a template's active status (pause/resume)."""
    if template_id not in recurring_templates_db:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    template = recurring_templates_db[template_id]
    template.is_active = not template.is_active
    return template

@app.post("/api/recurring-templates/expand", response_model=List[JournalEntry], tags=["Recurring Transactions"])
async def expand_recurring_templates(
    start_date: date,
    end_date: date,
    auto_post: bool = Query(False, description="Automatically post generated entries"),
    template_ids: Optional[List[str]] = Query(None, description="Specific template IDs to expand (optional)")
):
    """
    Expand recurring templates into journal entries for a date range.

    Useful for forecasting or bulk generating scheduled transactions.
    """
    # Get templates to expand
    if template_ids:
        templates = [recurring_templates_db[tid] for tid in template_ids if tid in recurring_templates_db]
    else:
        templates = list(recurring_templates_db.values())

    # Expand
    entries = recurring_service.expand_recurring_entries(
        recurring_templates=templates,
        start_date=start_date,
        end_date=end_date,
        auto_post=auto_post
    )

    # Optionally save to database
    if auto_post:
        for entry in entries:
            journal_entries_db[entry.journal_entry_id] = entry

    return entries

# ============================================================================
# FORECASTING
# ============================================================================

@app.get("/api/forecast/envelope/{envelope_id}", tags=["Forecasting"])
async def forecast_envelope_balance(
    envelope_id: str,
    target_date: date
):
    """
    Forecast a budget envelope balance on a future date.

    Applies monthly allocations based on the envelope's monthly_allocation setting.
    For more complex forecasting with scheduled expenses, use the account forecast endpoint.
    """
    # Simple forecast: just apply monthly allocations
    forecast = envelope_service.forecast_envelope_balance(
        envelope_id=envelope_id,
        target_date=target_date,
        scheduled_expenses=[]
    )

    return forecast

@app.get("/api/forecast/account/{account_id}", tags=["Forecasting"])
async def forecast_account_balance(
    account_id: str,
    target_date: date
):
    """
    Forecast an account balance on a future date.

    Uses recurring transactions to project future balance.
    """
    if account_id not in chart_of_accounts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    account = chart_of_accounts_db[account_id]

    # Expand recurring transactions up to target date
    templates = list(recurring_templates_db.values())
    future_entries = recurring_service.expand_recurring_entries(
        recurring_templates=templates,
        start_date=date.today(),
        end_date=target_date,
        auto_post=False
    )

    # Calculate balance impact
    starting_balance = account.current_balance
    balance_change = 0.0

    for entry in future_entries:
        for dist in entry.distributions:
            if dist.account_id == account_id:
                balance_change += dist.calculate_balance_impact()

    projected_balance = starting_balance + balance_change

    return {
        "account_id": account_id,
        "account_name": account.account_name,
        "current_balance": starting_balance,
        "as_of_date": date.today().isoformat(),
        "target_date": target_date.isoformat(),
        "projected_balance": projected_balance,
        "balance_change": balance_change,
        "transactions_applied": len([e for e in future_entries if any(d.account_id == account_id for d in e.distributions)])
    }

# ============================================================================
# STATISTICS & REPORTS
# ============================================================================

@app.get("/api/stats/summary", tags=["Statistics"])
async def get_summary_statistics():
    """Get summary statistics for the accounting system."""
    return {
        "chart_of_accounts": {
            "total": len(chart_of_accounts_db),
            "by_type": {
                "assets": len([a for a in chart_of_accounts_db.values() if a.account_type == AccountType.ASSET]),
                "liabilities": len([a for a in chart_of_accounts_db.values() if a.account_type == AccountType.LIABILITY]),
                "equity": len([a for a in chart_of_accounts_db.values() if a.account_type == AccountType.EQUITY]),
                "revenue": len([a for a in chart_of_accounts_db.values() if a.account_type == AccountType.REVENUE]),
                "expenses": len([a for a in chart_of_accounts_db.values() if a.account_type == AccountType.EXPENSE])
            }
        },
        "journal_entries": {
            "total": len(journal_entries_db),
            "posted": len([e for e in journal_entries_db.values() if e.status == JournalEntryStatus.POSTED]),
            "draft": len([e for e in journal_entries_db.values() if e.status == JournalEntryStatus.DRAFT])
        },
        "envelopes": {
            "budget": len(envelope_service.budget_envelopes),
            "payment": len(envelope_service.payment_envelopes),
            "total_budget_allocated": envelope_service.get_total_budget_allocated(),
            "total_payment_reserved": envelope_service.get_total_payment_reserved()
        },
        "recurring_templates": {
            "total": len(recurring_templates_db),
            "active": len([t for t in recurring_templates_db.values() if t.is_active])
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
