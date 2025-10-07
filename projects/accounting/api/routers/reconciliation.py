"""
Reconciliation & Payment API Router

Endpoints for statement reconciliation and payment processing.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel

router = APIRouter()


# Request Models
class StatementImport(BaseModel):
    account_id: str
    statement_date: str
    start_date: str
    end_date: str
    opening_balance: float
    closing_balance: float
    statement_type: str
    transactions: List[Dict]


class ReconciliationStart(BaseModel):
    account_id: str
    statement_id: str
    current_balance: float


class PaymentSchedule(BaseModel):
    from_account_id: str
    payee_name: str
    amount: float
    scheduled_date: str
    payment_method: str
    memo: Optional[str] = None


# Endpoints
@router.post("/statements")
async def import_statement(statement: StatementImport):
    """Import external statement."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "import_statement",
        "parameters": {"statement_data": statement.dict()}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/statements/{statement_id}")
async def get_statement(statement_id: str):
    """Get statement by ID."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "get_statement",
        "parameters": {"statement_id": statement_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.get("/statements")
async def list_statements(
    account_id: Optional[str] = None,
    start_date: Optional[str] = None
):
    """List statements with filters."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "list_statements",
        "parameters": {
            "account_id": account_id,
            "start_date": start_date
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/reconciliations")
async def start_reconciliation(recon: ReconciliationStart):
    """Start reconciliation process."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "start_reconciliation",
        "parameters": recon.dict()
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/reconciliations/{reconciliation_id}")
async def get_reconciliation(reconciliation_id: str):
    """Get reconciliation by ID."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "get_reconciliation",
        "parameters": {"reconciliation_id": reconciliation_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.post("/reconciliations/{reconciliation_id}/match")
async def match_transactions(reconciliation_id: str):
    """Auto-match transactions."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "match_transactions",
        "parameters": {"reconciliation_id": reconciliation_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/reconciliations/{reconciliation_id}/complete")
async def complete_reconciliation(reconciliation_id: str):
    """Complete reconciliation."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "complete_reconciliation",
        "parameters": {"reconciliation_id": reconciliation_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/reconciliations/{reconciliation_id}/discrepancies")
async def list_discrepancies(
    reconciliation_id: str,
    status: Optional[str] = None
):
    """List discrepancies for reconciliation."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "list_discrepancies",
        "parameters": {
            "reconciliation_id": reconciliation_id,
            "status": status
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/payments")
async def schedule_payment(payment: PaymentSchedule):
    """Schedule a payment."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "schedule_payment",
        "parameters": {"payment_data": payment.dict()}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/payments/{payment_id}")
async def get_payment(payment_id: str):
    """Get payment by ID."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "get_payment",
        "parameters": {"payment_id": payment_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.post("/payments/process")
async def process_payments(scheduled_date: Optional[str] = None):
    """Process scheduled payments."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "process_payments",
        "parameters": {"scheduled_date": scheduled_date}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/payments/{payment_id}/cancel")
async def cancel_payment(payment_id: str):
    """Cancel a scheduled payment."""
    from ..app import get_agent

    agent = get_agent("reconciliation")
    result = await agent.execute({
        "operation": "cancel_payment",
        "parameters": {"payment_id": payment_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]
