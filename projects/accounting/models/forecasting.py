"""
Cash Flow Forecasting Data Models

Models for balance projections, confidence intervals, and forecast configurations.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ForecastPeriod(str, Enum):
    """Forecast time period options."""
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


class InterestCompounding(str, Enum):
    """Interest compounding frequency."""
    DAILY = "daily"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ConfidenceLevel(float, Enum):
    """Confidence level options."""
    LOW = 0.68  # 1 standard deviation
    MEDIUM = 0.95  # 2 standard deviations
    HIGH = 0.997  # 3 standard deviations


class DailyBalance(BaseModel):
    """
    Single day's balance calculation in a forecast.

    This is the fundamental unit of the forecast - every day gets one record.
    """
    date: date
    opening_balance: float
    closing_balance: float
    daily_change: float

    # Transactions on this day
    income: float = 0.0
    expenses: float = 0.0
    transfers: float = 0.0
    interest_earned: float = 0.0

    # Transaction details
    transaction_count: int = 0
    transaction_ids: List[str] = Field(default_factory=list)

    # Confidence metrics
    point_estimate: float
    lower_bound: float
    upper_bound: float
    margin_of_error: float
    confidence_level: float = 0.95

    # Flags
    is_critical_date: bool = False  # Low balance warning
    is_large_expense: bool = False  # Unusually large expense
    is_payday: bool = False  # Income received

    # Metadata
    notes: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class CriticalDate(BaseModel):
    """
    Critical date identified in forecast.

    Examples: low balance, large expense, payment due date.
    """
    date: date
    type: str  # "low_balance", "large_expense", "payment_due", etc.
    severity: str  # "low", "medium", "high", "critical"
    projected_balance: float
    threshold: Optional[float] = None
    description: str
    recommended_action: Optional[str] = None

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class ForecastConfig(BaseModel):
    """
    Configuration for generating a cash flow forecast.

    This defines how the forecast should be calculated.
    """
    forecast_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str

    # Date range
    start_date: date
    end_date: date

    # Reference point (for historical reconstruction)
    reference_date: date = Field(default_factory=date.today)
    reference_balance: float  # Known balance at reference date

    # Interest calculation
    include_interest: bool = True
    interest_rate: Optional[float] = None  # APY or APR
    interest_type: Optional[str] = None  # "savings" or "credit"
    compounding: InterestCompounding = InterestCompounding.DAILY

    # Confidence intervals
    generate_confidence_intervals: bool = True
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM

    # Critical date detection
    low_balance_threshold: Optional[float] = None
    large_expense_threshold: Optional[float] = None

    # Data sources
    include_recurring_transactions: bool = True
    include_scheduled_transactions: bool = True
    include_historical_transactions: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    notes: Optional[str] = None

    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class ForecastResult(BaseModel):
    """
    Complete forecast result with daily balances and analysis.
    """
    forecast_id: str
    account_id: str
    config: ForecastConfig

    # Daily balance projections
    daily_balances: List[DailyBalance]

    # Summary statistics
    opening_balance: float
    closing_balance: float
    total_income: float
    total_expenses: float
    total_interest: float
    net_change: float

    # Date range
    start_date: date
    end_date: date
    days_projected: int

    # Critical dates
    critical_dates: List[CriticalDate]

    # Confidence metrics
    overall_confidence: float
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)

    # Analysis
    min_balance: float
    min_balance_date: date
    max_balance: float
    max_balance_date: date
    avg_daily_balance: float

    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    calculation_time_ms: float = 0.0

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class VarianceAnalysis(BaseModel):
    """
    Variance analysis for confidence interval calculation.

    Analyzes historical variance to predict future uncertainty.
    """
    category: str  # "income", "expenses", "discretionary", etc.
    mean: float
    std_deviation: float
    variance: float
    coefficient_of_variation: float
    sample_size: int
    period_analyzed_days: int

    # Time-based patterns
    weekday_variance: Dict[str, float] = Field(default_factory=dict)
    monthly_variance: Dict[int, float] = Field(default_factory=dict)

    # Confidence metrics
    reliability_score: float  # 0-1, higher = more predictable

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class ScenarioConfig(BaseModel):
    """
    Configuration for scenario modeling.

    Allows "what-if" analysis with different assumptions.
    """
    scenario_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_name: str
    base_forecast_id: str

    # Adjustments to base forecast
    one_time_income: List[Dict[str, Any]] = Field(default_factory=list)
    one_time_expenses: List[Dict[str, Any]] = Field(default_factory=list)
    recurring_adjustments: List[Dict[str, Any]] = Field(default_factory=list)

    # Modified parameters
    modified_interest_rate: Optional[float] = None
    modified_spending_factor: Optional[float] = None  # Multiply expenses by this

    description: Optional[str] = None

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class ForecastComparison(BaseModel):
    """
    Comparison between multiple forecasts or scenarios.
    """
    comparison_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    forecast_ids: List[str]
    comparison_type: str  # "scenario", "time_period", "account"

    # Comparative metrics
    balance_divergence: Dict[str, float] = Field(default_factory=dict)
    key_differences: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
