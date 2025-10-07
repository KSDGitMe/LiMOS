"""
Budget Management API Router

Endpoints for budget management, tracking, and alerts.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel

router = APIRouter()


# Request Models
class CategoryBudgetCreate(BaseModel):
    category: str
    subcategory: Optional[str] = None
    allocated_amount: float
    alert_thresholds: Optional[List[float]] = [0.8, 0.9, 1.0]


class BudgetCreate(BaseModel):
    budget_name: str
    budget_type: str
    start_date: str
    end_date: str
    current_period: str
    categories: List[Dict]
    account_ids: Optional[List[str]] = []


# Endpoints
@router.post("/")
async def create_budget(budget: BudgetCreate):
    """Create a new budget."""
    from ..app import get_agent

    agent = get_agent("budget")
    result = await agent.execute({
        "operation": "create_budget",
        "parameters": {"budget_data": budget.dict()}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/{budget_id}")
async def get_budget(budget_id: str):
    """Get budget by ID."""
    from ..app import get_agent

    agent = get_agent("budget")
    result = await agent.execute({
        "operation": "get_budget",
        "parameters": {"budget_id": budget_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.get("/")
async def list_budgets(
    status: Optional[str] = None,
    budget_type: Optional[str] = None,
    current_period: Optional[str] = None
):
    """List budgets with filters."""
    from ..app import get_agent

    agent = get_agent("budget")
    result = await agent.execute({
        "operation": "list_budgets",
        "parameters": {
            "status": status,
            "budget_type": budget_type,
            "current_period": current_period
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/alerts")
async def get_alerts(
    budget_id: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    alert_level: Optional[str] = None
):
    """Get budget alerts."""
    from ..app import get_agent

    agent = get_agent("budget")
    result = await agent.execute({
        "operation": "get_alerts",
        "parameters": {
            "budget_id": budget_id,
            "acknowledged": acknowledged,
            "alert_level": alert_level
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge a budget alert."""
    from ..app import get_agent

    agent = get_agent("budget")
    result = await agent.execute({
        "operation": "acknowledge_alert",
        "parameters": {"alert_id": alert_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/{budget_id}/variance-report")
async def generate_variance_report(budget_id: str):
    """Generate variance analysis report."""
    from ..app import get_agent

    agent = get_agent("budget")
    result = await agent.execute({
        "operation": "generate_variance_report",
        "parameters": {"budget_id": budget_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/{budget_id}/project-spending")
async def project_spending(
    budget_id: str,
    category: str,
    subcategory: Optional[str] = None
):
    """Project end-of-period spending for category."""
    from ..app import get_agent

    agent = get_agent("budget")
    result = await agent.execute({
        "operation": "project_spending",
        "parameters": {
            "budget_id": budget_id,
            "category": category,
            "subcategory": subcategory
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]
