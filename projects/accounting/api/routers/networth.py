"""
Net Worth & Asset Tracking API Router

Endpoints for net worth tracking, assets, liabilities, and goals.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()


# Request Models
class AssetCreate(BaseModel):
    asset_name: str
    asset_type: str
    current_value: float
    description: Optional[str] = None
    acquisition_date: Optional[str] = None
    is_liquid: bool = True


class LiabilityCreate(BaseModel):
    liability_name: str
    liability_type: str
    current_balance: float
    interest_rate: Optional[float] = None
    creditor: Optional[str] = None


class GoalCreate(BaseModel):
    goal_name: str
    target_amount: float
    target_date: Optional[str] = None
    current_amount: float


class PayoffPlanCreate(BaseModel):
    plan_name: str
    strategy: str
    included_liability_ids: List[str]
    monthly_payment: float
    extra_payment: Optional[float] = 0.0


# Asset Endpoints
@router.post("/assets")
async def create_asset(asset: AssetCreate):
    """Create a new asset."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "create_asset",
        "parameters": {"asset_data": asset.dict()}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    """Get asset by ID."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "get_asset",
        "parameters": {"asset_id": asset_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.get("/assets")
async def list_assets(asset_type: Optional[str] = None, is_active: bool = True):
    """List assets with filters."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "list_assets",
        "parameters": {
            "asset_type": asset_type,
            "is_active": is_active
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.put("/assets/{asset_id}")
async def update_asset(asset_id: str, updates: Dict):
    """Update asset value or details."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "update_asset",
        "parameters": {
            "asset_id": asset_id,
            "updates": updates
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str):
    """Soft delete asset."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "delete_asset",
        "parameters": {"asset_id": asset_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


# Liability Endpoints
@router.post("/liabilities")
async def create_liability(liability: LiabilityCreate):
    """Create a new liability."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "create_liability",
        "parameters": {"liability_data": liability.dict()}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/liabilities/{liability_id}")
async def get_liability(liability_id: str):
    """Get liability by ID."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "get_liability",
        "parameters": {"liability_id": liability_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.get("/liabilities")
async def list_liabilities(
    liability_type: Optional[str] = None,
    is_active: bool = True
):
    """List liabilities with filters."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "list_liabilities",
        "parameters": {
            "liability_type": liability_type,
            "is_active": is_active
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.put("/liabilities/{liability_id}")
async def update_liability(liability_id: str, updates: Dict):
    """Update liability balance."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "update_liability",
        "parameters": {
            "liability_id": liability_id,
            "updates": updates
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.delete("/liabilities/{liability_id}")
async def delete_liability(liability_id: str):
    """Soft delete liability."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "delete_liability",
        "parameters": {"liability_id": liability_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


# Net Worth Snapshot Endpoints
@router.post("/snapshots")
async def create_snapshot(snapshot_date: Optional[str] = None):
    """Create net worth snapshot."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "create_snapshot",
        "parameters": {"snapshot_date": snapshot_date}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/snapshots/{snapshot_id}")
async def get_snapshot(snapshot_id: str):
    """Get snapshot by ID."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "get_snapshot",
        "parameters": {"snapshot_id": snapshot_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.get("/snapshots")
async def list_snapshots(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10
):
    """List net worth snapshots."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "list_snapshots",
        "parameters": {
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


# Analysis Endpoints
@router.post("/analyze/trends")
async def analyze_trends(start_date: str, end_date: str):
    """Analyze net worth trends."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "analyze_trends",
        "parameters": {
            "start_date": start_date,
            "end_date": end_date
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/analyze/allocation")
async def analyze_allocation():
    """Analyze current asset allocation."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "analyze_allocation",
        "parameters": {}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/analyze/portfolio-performance")
async def calculate_portfolio_performance(start_date: str, end_date: str):
    """Calculate investment portfolio performance."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "calculate_portfolio_performance",
        "parameters": {
            "start_date": start_date,
            "end_date": end_date
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


# Goal Endpoints
@router.post("/goals")
async def create_goal(goal: GoalCreate):
    """Create net worth goal."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "create_goal",
        "parameters": {"goal_data": goal.dict()}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    """Get goal by ID."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "get_goal",
        "parameters": {"goal_id": goal_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.get("/goals")
async def list_goals(is_achieved: Optional[bool] = None):
    """List net worth goals."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "list_goals",
        "parameters": {"is_achieved": is_achieved}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.put("/goals/{goal_id}/progress")
async def update_goal_progress(goal_id: str, current_amount: float):
    """Update goal progress."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "update_goal_progress",
        "parameters": {
            "goal_id": goal_id,
            "current_amount": current_amount
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


# Debt Payoff Plan Endpoints
@router.post("/payoff-plans")
async def create_payoff_plan(plan: PayoffPlanCreate):
    """Create debt payoff plan."""
    from ..app import get_agent

    agent = get_agent("networth")

    # Calculate total debt from liabilities
    total_debt = 0.0
    total_minimum = 0.0

    result = await agent.execute({
        "operation": "create_payoff_plan",
        "parameters": {
            "plan_data": {
                **plan.dict(),
                "total_debt": total_debt,
                "total_minimum_payment": total_minimum,
                "original_total_debt": total_debt,
                "amount_remaining": total_debt
            }
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/payoff-plans/{plan_id}")
async def get_payoff_plan(plan_id: str):
    """Get payoff plan by ID."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "get_payoff_plan",
        "parameters": {"plan_id": plan_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.put("/payoff-plans/{plan_id}/progress")
async def update_payoff_plan(plan_id: str, amount_paid: float):
    """Update debt payoff plan progress."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "update_payoff_plan",
        "parameters": {
            "plan_id": plan_id,
            "amount_paid": amount_paid
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


# Report Endpoint
@router.post("/report")
async def generate_networth_report():
    """Generate comprehensive net worth report."""
    from ..app import get_agent

    agent = get_agent("networth")
    result = await agent.execute({
        "operation": "generate_networth_report",
        "parameters": {}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]
