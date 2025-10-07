"""
Net Worth & Asset Tracking Data Models

Models for tracking net worth, assets, liabilities, and portfolio performance.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """Asset types."""
    CASH = "cash"
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    RETIREMENT = "retirement"
    REAL_ESTATE = "real_estate"
    VEHICLE = "vehicle"
    PERSONAL_PROPERTY = "personal_property"
    BUSINESS = "business"
    CRYPTOCURRENCY = "cryptocurrency"
    OTHER = "other"


class LiabilityType(str, Enum):
    """Liability types."""
    CREDIT_CARD = "credit_card"
    MORTGAGE = "mortgage"
    AUTO_LOAN = "auto_loan"
    STUDENT_LOAN = "student_loan"
    PERSONAL_LOAN = "personal_loan"
    BUSINESS_LOAN = "business_loan"
    OTHER = "other"


class ValuationMethod(str, Enum):
    """How asset value is determined."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    MARKET_PRICE = "market_price"
    ACCOUNT_BALANCE = "account_balance"
    APPRAISAL = "appraisal"
    ESTIMATED = "estimated"


class Asset(BaseModel):
    """
    Individual asset.

    Tracks a specific asset with current value and history.
    """
    asset_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_name: str
    asset_type: AssetType

    # Value
    current_value: float
    currency: str = "USD"
    valuation_method: ValuationMethod = ValuationMethod.MANUAL
    last_valuation_date: date = Field(default_factory=date.today)

    # Details
    description: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[float] = None

    # For investments
    ticker_symbol: Optional[str] = None
    shares: Optional[float] = None
    cost_basis: Optional[float] = None

    # For real estate/vehicles
    location: Optional[str] = None
    model: Optional[str] = None

    # Ownership
    owner: Optional[str] = None
    ownership_percentage: float = 100.0

    # Account linking
    linked_account_id: Optional[str] = None

    # Status
    is_active: bool = True
    is_liquid: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class Liability(BaseModel):
    """
    Individual liability.

    Tracks debts and obligations.
    """
    liability_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    liability_name: str
    liability_type: LiabilityType

    # Amount
    current_balance: float
    original_amount: Optional[float] = None
    currency: str = "USD"

    # Terms
    interest_rate: Optional[float] = None
    minimum_payment: Optional[float] = None
    payment_due_day: Optional[int] = None

    # Dates
    origination_date: Optional[date] = None
    maturity_date: Optional[date] = None
    last_payment_date: Optional[date] = None

    # Creditor
    creditor: Optional[str] = None
    account_number_last4: Optional[str] = None

    # Account linking
    linked_account_id: Optional[str] = None

    # Status
    is_active: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class NetWorthSnapshot(BaseModel):
    """
    Point-in-time snapshot of net worth.

    Captures total assets, liabilities, and net worth at a specific date.
    """
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_date: date

    # Assets
    total_assets: float
    liquid_assets: float
    non_liquid_assets: float
    assets_by_type: Dict[str, float] = Field(default_factory=dict)

    # Liabilities
    total_liabilities: float
    short_term_liabilities: float
    long_term_liabilities: float
    liabilities_by_type: Dict[str, float] = Field(default_factory=dict)

    # Net worth
    net_worth: float
    liquid_net_worth: float

    # Ratios
    debt_to_asset_ratio: float = 0.0
    liquidity_ratio: float = 0.0

    # Change tracking
    change_from_previous: Optional[float] = None
    change_percentage: Optional[float] = None
    days_since_previous: Optional[int] = None

    # Breakdown
    asset_details: List[Dict[str, Any]] = Field(default_factory=list)
    liability_details: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class NetWorthTrend(BaseModel):
    """
    Net worth trend analysis over time.

    Analyzes changes in net worth across multiple snapshots.
    """
    trend_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Period
    start_date: date
    end_date: date
    period_label: str

    # Snapshots
    snapshots: List[NetWorthSnapshot] = Field(default_factory=list)
    snapshot_count: int = 0

    # Trend analysis
    starting_net_worth: float
    ending_net_worth: float
    total_change: float
    total_change_percentage: float

    # Statistics
    average_net_worth: float
    median_net_worth: float
    min_net_worth: float
    max_net_worth: float

    # Growth
    average_monthly_growth: float
    annualized_growth_rate: float

    # Composition changes
    asset_composition_change: Dict[str, float] = Field(default_factory=dict)
    liability_composition_change: Dict[str, float] = Field(default_factory=dict)

    # Milestones
    milestones_reached: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class AssetAllocation(BaseModel):
    """
    Asset allocation analysis.

    Shows how assets are distributed across types and categories.
    """
    allocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    as_of_date: date

    # Total value
    total_value: float

    # By type
    allocation_by_type: Dict[str, float] = Field(default_factory=dict)
    allocation_percentage_by_type: Dict[str, float] = Field(default_factory=dict)

    # By liquidity
    liquid_assets: float
    liquid_percentage: float
    non_liquid_assets: float
    non_liquid_percentage: float

    # By risk
    low_risk_value: Optional[float] = None
    medium_risk_value: Optional[float] = None
    high_risk_value: Optional[float] = None

    # Recommendations
    is_diversified: bool = True
    concentration_risks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PortfolioPerformance(BaseModel):
    """
    Investment portfolio performance.

    Tracks returns and performance metrics for investment assets.
    """
    performance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Period
    start_date: date
    end_date: date
    period_label: str

    # Values
    starting_value: float
    ending_value: float
    contributions: float = 0.0
    withdrawals: float = 0.0

    # Returns
    total_return: float
    total_return_percentage: float
    time_weighted_return: Optional[float] = None
    money_weighted_return: Optional[float] = None

    # Gains/losses
    realized_gains: float = 0.0
    unrealized_gains: float = 0.0
    total_gains: float = 0.0

    # Income
    dividends: float = 0.0
    interest: float = 0.0
    total_income: float = 0.0

    # Performance metrics
    annualized_return: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    # Holdings
    top_performers: List[Dict[str, Any]] = Field(default_factory=list)
    worst_performers: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class AssetValuation(BaseModel):
    """
    Historical asset valuation record.

    Tracks value changes over time for an asset.
    """
    valuation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_id: str

    # Valuation
    valuation_date: date
    value: float
    currency: str = "USD"
    valuation_method: ValuationMethod

    # Change tracking
    previous_value: Optional[float] = None
    change: Optional[float] = None
    change_percentage: Optional[float] = None

    # Source
    source: Optional[str] = None  # "manual", "api", "import"
    verified: bool = False
    verified_by: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class NetWorthGoal(BaseModel):
    """
    Net worth milestone or goal.

    Tracks progress toward net worth targets.
    """
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal_name: str
    description: Optional[str] = None

    # Target
    target_amount: float
    target_date: Optional[date] = None

    # Progress
    current_amount: float
    amount_remaining: float
    percentage_complete: float

    # Status
    is_achieved: bool = False
    achieved_date: Optional[date] = None

    # Tracking
    milestone_amounts: List[float] = Field(default_factory=list)
    milestones_reached: int = 0

    # Projection
    projected_completion_date: Optional[date] = None
    on_track: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DebtPayoffPlan(BaseModel):
    """
    Debt payoff strategy and timeline.

    Plans and tracks debt reduction.
    """
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_name: str
    strategy: str  # "avalanche", "snowball", "custom"

    # Debts
    included_liability_ids: List[str] = Field(default_factory=list)
    total_debt: float
    total_minimum_payment: float

    # Payment plan
    monthly_payment: float
    extra_payment: float = 0.0

    # Timeline
    estimated_payoff_date: Optional[date] = None
    estimated_months: Optional[int] = None

    # Costs
    total_interest_without_plan: float = 0.0
    total_interest_with_plan: float = 0.0
    interest_savings: float = 0.0

    # Progress
    original_total_debt: float
    amount_paid: float = 0.0
    amount_remaining: float
    percentage_complete: float = 0.0

    # Status
    is_active: bool = True
    started_date: Optional[date] = None
    completed_date: Optional[date] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class NetWorthReport(BaseModel):
    """
    Comprehensive net worth report.

    Complete analysis of financial position.
    """
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_date: date

    # Current snapshot
    current_snapshot: NetWorthSnapshot

    # Trend
    trend_analysis: Optional[NetWorthTrend] = None

    # Allocation
    asset_allocation: Optional[AssetAllocation] = None

    # Performance
    portfolio_performance: Optional[PortfolioPerformance] = None

    # Goals
    goals_progress: List[NetWorthGoal] = Field(default_factory=list)

    # Debt
    debt_summary: Dict[str, Any] = Field(default_factory=dict)
    debt_payoff_plans: List[DebtPayoffPlan] = Field(default_factory=list)

    # Insights
    key_metrics: Dict[str, float] = Field(default_factory=dict)
    highlights: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: Optional[str] = None


class MarketData(BaseModel):
    """
    Market data for investment tracking.

    Stores market prices for automated valuation.
    """
    market_data_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Symbol
    symbol: str
    asset_type: str  # "stock", "etf", "mutual_fund", "crypto"

    # Price
    price: float
    currency: str = "USD"
    price_date: date

    # Daily change
    change: Optional[float] = None
    change_percentage: Optional[float] = None

    # Volume
    volume: Optional[int] = None

    # 52-week range
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None

    # Source
    source: str = "manual"  # "manual", "api", "import"

    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
