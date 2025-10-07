"""
Transaction Management API Router

Endpoints for managing transactions and recurring transactions.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()


# Request/Response Models
class TransactionCreate(BaseModel):
    account_id: str
    date: str
    merchant: str
    amount: float
    transaction_type: str
    category: str
    subcategory: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class RecurringTransactionCreate(BaseModel):
    template_name: str
    account_id: str
    merchant: str
    base_amount: float
    transaction_type: str
    category: str
    subcategory: Optional[str] = None
    recurrence_rule: Dict
    start_date: str
    end_date: Optional[str] = None


# Endpoints
@router.post("/")
async def create_transaction(transaction: TransactionCreate):
    """Create a new transaction."""
    from ..app import get_agent

    agent = get_agent("transaction")
    result = await agent.execute({
        "operation": "create_transaction",
        "parameters": {"transaction_data": transaction.dict()}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Get transaction by ID."""
    from ..app import get_agent

    agent = get_agent("transaction")
    result = await agent.execute({
        "operation": "get_transaction",
        "parameters": {"transaction_id": transaction_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.get("/")
async def search_transactions(
    account_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    limit: int = 100
):
    """Search transactions with filters."""
    from ..app import get_agent

    agent = get_agent("transaction")
    result = await agent.execute({
        "operation": "search_transactions",
        "parameters": {
            "account_id": account_id,
            "start_date": start_date,
            "end_date": end_date,
            "category": category,
            "transaction_type": transaction_type,
            "limit": limit
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/recurring")
async def create_recurring_transaction(recurring: RecurringTransactionCreate):
    """Create a recurring transaction template."""
    from ..app import get_agent

    agent = get_agent("transaction")
    result = await agent.execute({
        "operation": "create_recurring",
        "parameters": {"recurring_data": recurring.dict()}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/recurring/{recurring_id}")
async def get_recurring_transaction(recurring_id: str):
    """Get recurring transaction template."""
    from ..app import get_agent

    agent = get_agent("transaction")
    result = await agent.execute({
        "operation": "get_recurring_transaction",
        "parameters": {"recurring_transaction_id": recurring_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.get("/recurring")
async def list_recurring_transactions():
    """List all recurring transaction templates."""
    from ..app import get_agent

    agent = get_agent("transaction")
    result = await agent.execute({
        "operation": "list_recurring_transactions",
        "parameters": {}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/recurring/{recurring_id}/occurrences")
async def calculate_next_occurrences(recurring_id: str, count: int = 10):
    """Calculate next N occurrences of recurring transaction."""
    from ..app import get_agent

    agent = get_agent("transaction")
    result = await agent.execute({
        "operation": "calculate_next_occurrences",
        "parameters": {
            "recurring_transaction_id": recurring_id,
            "count": count
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/recurring/generate")
async def generate_scheduled_transactions(days_ahead: int = 30):
    """Generate scheduled transactions from recurring templates."""
    from ..app import get_agent

    agent = get_agent("transaction")
    result = await agent.execute({
        "operation": "generate_scheduled_transactions",
        "parameters": {"days_ahead": days_ahead}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]
