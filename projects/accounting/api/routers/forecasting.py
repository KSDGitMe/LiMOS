"""
Cash Flow Forecasting API Router

Endpoints for cash flow projections and forecasting.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

router = APIRouter()


# Request Models
class ForecastCreate(BaseModel):
    account_id: str
    start_date: str
    end_date: str
    reference_date: str
    reference_balance: float
    interest_rate: Optional[float] = 0.0
    interest_type: Optional[str] = "savings"
    confidence_level: Optional[str] = "medium"


# Endpoints
@router.post("/")
async def create_forecast(forecast: ForecastCreate):
    """Create cash flow forecast."""
    from ..app import get_agent

    agent = get_agent("forecasting")
    result = await agent.execute({
        "operation": "create_forecast",
        "parameters": {"config": forecast.dict()}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/{forecast_id}")
async def get_forecast(forecast_id: str):
    """Get forecast by ID."""
    from ..app import get_agent

    agent = get_agent("forecasting")
    result = await agent.execute({
        "operation": "get_forecast",
        "parameters": {"forecast_id": forecast_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]


@router.get("/")
async def list_forecasts(
    account_id: Optional[str] = None,
    start_date: Optional[str] = None,
    limit: int = 10
):
    """List forecasts with filters."""
    from ..app import get_agent

    agent = get_agent("forecasting")
    result = await agent.execute({
        "operation": "list_forecasts",
        "parameters": {
            "account_id": account_id,
            "start_date": start_date,
            "limit": limit
        }
    })

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])

    return result["result"]


@router.get("/{forecast_id}/critical-dates")
async def get_critical_dates(forecast_id: str):
    """Get critical dates from forecast."""
    from ..app import get_agent

    agent = get_agent("forecasting")
    result = await agent.execute({
        "operation": "get_critical_dates",
        "parameters": {"forecast_id": forecast_id}
    })

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result["result"]
