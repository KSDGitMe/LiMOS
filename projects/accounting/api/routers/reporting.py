"""
Reporting & Analytics API Router

Endpoints for financial reports, analytics, and insights.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


# Request Models
class DateRange(BaseModel):
    start_date: str
    end_date: str
    account_ids: Optional[List[str]] = None


class TrendAnalysisRequest(BaseModel):
    metric_name: str
    time_period: str
    start_date: str
    end_date: str
    account_ids: Optional[List[str]] = None


class PeriodComparison(BaseModel):
    current_start: str
    current_end: str
    previous_start: str
    previous_end: str
    account_ids: Optional[List[str]] = None


# Endpoints
@router.post("/income-statement")
async def generate_income_statement(request: DateRange):
    """Generate income statement (P&L)."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "generate_income_statement",
        "parameters": request.dict()
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/balance-sheet")
async def generate_balance_sheet(as_of_date: str, account_ids: Optional[List[str]] = None):
    """Generate balance sheet."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "generate_balance_sheet",
        "parameters": {
            "as_of_date": as_of_date,
            "account_ids": account_ids
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/cash-flow-statement")
async def generate_cash_flow_statement(request: DateRange):
    """Generate cash flow statement."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "generate_cash_flow_statement",
        "parameters": request.dict()
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/analyze/spending")
async def analyze_spending(request: DateRange):
    """Analyze spending patterns."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "analyze_spending",
        "parameters": request.dict()
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/analyze/income")
async def analyze_income(request: DateRange):
    """Analyze income patterns."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "analyze_income",
        "parameters": request.dict()
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/analyze/trends")
async def analyze_trends(request: TrendAnalysisRequest):
    """Analyze trends over time."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "analyze_trends",
        "parameters": request.dict()
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/compare-periods")
async def compare_periods(request: PeriodComparison):
    """Compare two time periods."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "compare_periods",
        "parameters": request.dict()
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/insights/generate")
async def generate_insights(
    account_ids: Optional[List[str]] = None,
    lookback_days: int = 30
):
    """Generate automated insights."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "generate_insights",
        "parameters": {
            "account_ids": account_ids,
            "lookback_days": lookback_days
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/insights")
async def get_insights(
    viewed: Optional[bool] = None,
    dismissed: bool = False,
    limit: int = 10
):
    """Get insights with filters."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "get_insights",
        "parameters": {
            "viewed": viewed,
            "dismissed": dismissed,
            "limit": limit
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/insights/{insight_id}/dismiss")
async def dismiss_insight(insight_id: str):
    """Dismiss an insight."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "dismiss_insight",
        "parameters": {"insight_id": insight_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.post("/kpis/calculate")
async def calculate_kpis(account_ids: Optional[List[str]] = None):
    """Calculate key performance indicators."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "calculate_kpis",
        "parameters": {"account_ids": account_ids}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/kpis/{kpi_name}")
async def get_kpi(kpi_name: str):
    """Get KPI by name."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "get_kpi",
        "parameters": {"kpi_name": kpi_name}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.post("/tax-summary")
async def generate_tax_summary(tax_year: int, account_ids: Optional[List[str]] = None):
    """Generate tax summary for year."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "generate_tax_summary",
        "parameters": {
            "tax_year": tax_year,
            "account_ids": account_ids
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/reports")
async def list_reports(report_type: Optional[str] = None, limit: int = 10):
    """List generated reports."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "list_reports",
        "parameters": {
            "report_type": report_type,
            "limit": limit
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get report by ID."""
    from ..app import get_agent

    agent = get_agent("reporting")
    result = await agent.execute({
        "operation": "get_report",
        "parameters": {"report_id": report_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]
