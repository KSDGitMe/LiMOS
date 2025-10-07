"""
Reporting & Analytics Data Models

Models for financial reports, analytics, insights, and trend analysis.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Report types."""
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    BUDGET_VARIANCE = "budget_variance"
    SPENDING_BY_CATEGORY = "spending_by_category"
    INCOME_BY_SOURCE = "income_by_source"
    TREND_ANALYSIS = "trend_analysis"
    ACCOUNT_SUMMARY = "account_summary"
    TAX_SUMMARY = "tax_summary"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report output formats."""
    JSON = "json"
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    HTML = "html"


class TimePeriod(str, Enum):
    """Time period options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class TrendDirection(str, Enum):
    """Trend direction."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class InsightType(str, Enum):
    """Types of insights."""
    SPENDING_SPIKE = "spending_spike"
    UNUSUAL_TRANSACTION = "unusual_transaction"
    RECURRING_PATTERN = "recurring_pattern"
    BUDGET_RISK = "budget_risk"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    INCOME_CHANGE = "income_change"
    CATEGORY_SHIFT = "category_shift"
    GOAL_PROGRESS = "goal_progress"


class ReportParameter(BaseModel):
    """Report parameter configuration."""
    parameter_name: str
    parameter_type: str  # "date", "account", "category", "number", "text"
    required: bool = False
    default_value: Optional[Any] = None
    description: Optional[str] = None


class CategoryBreakdown(BaseModel):
    """Category spending/income breakdown."""
    category: str
    subcategory: Optional[str] = None
    amount: float
    transaction_count: int
    percentage_of_total: float
    average_transaction: float
    change_from_previous: Optional[float] = None
    change_percentage: Optional[float] = None


class TimeSeriesData(BaseModel):
    """Time series data point."""
    period: str  # "2025-01", "2025-Q1", "2025-W01"
    period_start: date
    period_end: date
    value: float
    label: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncomeStatement(BaseModel):
    """
    Income statement (Profit & Loss).

    Revenue - Expenses = Net Income
    """
    statement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Period
    start_date: date
    end_date: date
    period_label: str

    # Revenue
    total_income: float
    income_by_category: List[CategoryBreakdown] = Field(default_factory=list)

    # Expenses
    total_expenses: float
    expenses_by_category: List[CategoryBreakdown] = Field(default_factory=list)

    # Net income
    net_income: float
    net_income_margin: float = 0.0  # (Net income / Total income) * 100

    # Comparisons
    previous_period_net_income: Optional[float] = None
    change_from_previous: Optional[float] = None
    change_percentage: Optional[float] = None

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: Optional[str] = None


class BalanceSheet(BaseModel):
    """
    Balance sheet.

    Assets = Liabilities + Equity
    """
    statement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # As of date
    as_of_date: date

    # Assets
    total_assets: float
    cash_and_equivalents: float
    investments: float
    other_assets: float
    assets_by_account: List[Dict[str, Any]] = Field(default_factory=list)

    # Liabilities
    total_liabilities: float
    credit_card_debt: float
    loans: float
    other_liabilities: float
    liabilities_by_account: List[Dict[str, Any]] = Field(default_factory=list)

    # Equity
    total_equity: float
    equity_change_from_previous: Optional[float] = None

    # Ratios
    debt_to_asset_ratio: float = 0.0
    current_ratio: float = 0.0

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: Optional[str] = None


class CashFlowStatement(BaseModel):
    """
    Cash flow statement.

    Shows cash inflows and outflows over period.
    """
    statement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Period
    start_date: date
    end_date: date
    period_label: str

    # Opening/closing balances
    opening_balance: float
    closing_balance: float
    net_change: float

    # Operating activities
    cash_from_operations: float
    income_received: float
    expenses_paid: float

    # Investing activities
    cash_from_investing: float
    investment_purchases: float
    investment_sales: float

    # Financing activities
    cash_from_financing: float
    loan_proceeds: float
    loan_payments: float

    # Details
    largest_inflows: List[Dict[str, Any]] = Field(default_factory=list)
    largest_outflows: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: Optional[str] = None


class SpendingAnalysis(BaseModel):
    """
    Detailed spending analysis.

    Breaks down spending patterns and trends.
    """
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Period
    start_date: date
    end_date: date
    period_label: str

    # Total spending
    total_spending: float
    transaction_count: int
    average_transaction: float
    median_transaction: float

    # By category
    spending_by_category: List[CategoryBreakdown] = Field(default_factory=list)
    top_categories: List[str] = Field(default_factory=list)

    # By merchant
    spending_by_merchant: List[Dict[str, Any]] = Field(default_factory=list)
    top_merchants: List[str] = Field(default_factory=list)

    # Trends
    daily_average: float
    weekly_average: float
    monthly_average: float
    trend_direction: TrendDirection = TrendDirection.STABLE

    # Comparisons
    previous_period_spending: Optional[float] = None
    change_from_previous: Optional[float] = None
    change_percentage: Optional[float] = None

    # Day of week analysis
    spending_by_day_of_week: Dict[str, float] = Field(default_factory=dict)
    peak_spending_day: Optional[str] = None

    # Insights
    unusual_patterns: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class IncomeAnalysis(BaseModel):
    """
    Income analysis and trends.

    Analyzes income sources and patterns.
    """
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Period
    start_date: date
    end_date: date
    period_label: str

    # Total income
    total_income: float
    transaction_count: int
    average_transaction: float

    # By category
    income_by_category: List[CategoryBreakdown] = Field(default_factory=list)
    top_sources: List[str] = Field(default_factory=list)

    # Trends
    monthly_average: float
    trend_direction: TrendDirection = TrendDirection.STABLE

    # Comparisons
    previous_period_income: Optional[float] = None
    change_from_previous: Optional[float] = None
    change_percentage: Optional[float] = None

    # Regularity
    regular_income_sources: List[str] = Field(default_factory=list)
    irregular_income_sources: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TrendAnalysis(BaseModel):
    """
    Time-based trend analysis.

    Analyzes trends over multiple periods.
    """
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Configuration
    metric_name: str  # "spending", "income", "net_income", "balance"
    time_period: TimePeriod
    start_date: date
    end_date: date

    # Time series data
    time_series: List[TimeSeriesData] = Field(default_factory=list)

    # Statistical analysis
    mean: float
    median: float
    std_deviation: float
    min_value: float
    max_value: float

    # Trend
    trend_direction: TrendDirection
    trend_percentage: float
    linear_regression_slope: Optional[float] = None

    # Patterns
    seasonal_patterns: List[str] = Field(default_factory=list)
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)

    # Forecasting
    next_period_forecast: Optional[float] = None
    forecast_confidence: Optional[float] = None

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ComparisonReport(BaseModel):
    """
    Period-over-period comparison report.

    Compares metrics across time periods.
    """
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Periods
    current_period_start: date
    current_period_end: date
    previous_period_start: date
    previous_period_end: date

    # Metrics
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    # Each metric: {name, current_value, previous_value, change, change_percentage}

    # Highlights
    improvements: List[str] = Field(default_factory=list)
    declines: List[str] = Field(default_factory=list)
    stable_metrics: List[str] = Field(default_factory=list)

    # Summary
    overall_trend: str = "mixed"
    key_takeaways: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class Insight(BaseModel):
    """
    Automated insight or observation.

    AI/algorithm generated financial insights.
    """
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    insight_type: InsightType

    # Content
    title: str
    description: str
    severity: str = "info"  # "info", "warning", "critical"

    # Data
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    expected_value: Optional[float] = None
    difference: Optional[float] = None

    # Context
    related_category: Optional[str] = None
    related_account_id: Optional[str] = None
    time_period: Optional[str] = None

    # Actionability
    actionable: bool = False
    recommended_action: Optional[str] = None

    # Status
    viewed: bool = False
    acted_upon: bool = False
    dismissed: bool = False

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = 0.8


class Report(BaseModel):
    """
    Generic financial report.

    Container for any report type with configuration and data.
    """
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: ReportType
    report_name: str

    # Configuration
    parameters: Dict[str, Any] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)

    # Period
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    as_of_date: Optional[date] = None

    # Data
    data: Dict[str, Any] = Field(default_factory=dict)
    summary: Dict[str, Any] = Field(default_factory=dict)

    # Output
    format: ReportFormat = ReportFormat.JSON
    file_path: Optional[str] = None

    # Status
    status: str = "completed"  # "pending", "processing", "completed", "failed"
    error_message: Optional[str] = None

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: Optional[str] = None
    execution_time_ms: Optional[int] = None


class Dashboard(BaseModel):
    """
    Financial dashboard configuration.

    Defines widgets and layout for dashboard views.
    """
    dashboard_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dashboard_name: str
    description: Optional[str] = None

    # Widgets
    widgets: List[Dict[str, Any]] = Field(default_factory=list)
    # Each widget: {widget_type, position, size, configuration}

    # Configuration
    refresh_interval: int = 300  # seconds
    default_period: TimePeriod = TimePeriod.MONTHLY

    # Access
    is_default: bool = False
    owner_id: Optional[str] = None
    shared_with: List[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class KPI(BaseModel):
    """
    Key Performance Indicator.

    Tracks important financial metrics over time.
    """
    kpi_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kpi_name: str
    description: str

    # Current value
    current_value: float
    target_value: Optional[float] = None
    unit: str = "USD"

    # Status
    on_track: bool = True
    percentage_to_target: Optional[float] = None

    # Trend
    trend_direction: TrendDirection = TrendDirection.STABLE
    change_from_previous: Optional[float] = None
    change_percentage: Optional[float] = None

    # History
    historical_values: List[TimeSeriesData] = Field(default_factory=list)

    # Display
    display_format: str = "currency"  # "currency", "percentage", "number"
    color_coding: str = "green"  # "green", "yellow", "red"

    # Metadata
    category: str = "general"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class ScheduledReport(BaseModel):
    """
    Scheduled report configuration.

    Defines reports to be generated automatically on a schedule.
    """
    scheduled_report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: ReportType
    report_name: str

    # Schedule
    frequency: str  # "daily", "weekly", "monthly", "quarterly"
    day_of_week: Optional[str] = None
    day_of_month: Optional[int] = None
    time_of_day: Optional[str] = None

    # Configuration
    parameters: Dict[str, Any] = Field(default_factory=dict)
    format: ReportFormat = ReportFormat.PDF

    # Distribution
    recipients: List[str] = Field(default_factory=list)
    delivery_method: str = "email"  # "email", "storage", "api"

    # Status
    is_active: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_report_id: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


class TaxSummary(BaseModel):
    """
    Tax summary report.

    Summarizes tax-related transactions for tax preparation.
    """
    summary_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Tax year
    tax_year: int
    start_date: date
    end_date: date

    # Income
    total_income: float
    w2_income: float
    1099_income: float
    other_income: float
    income_by_category: List[CategoryBreakdown] = Field(default_factory=list)

    # Deductions
    total_deductions: float
    business_expenses: float
    charitable_contributions: float
    medical_expenses: float
    other_deductions: float
    deductions_by_category: List[CategoryBreakdown] = Field(default_factory=list)

    # Tax payments
    federal_tax_paid: float
    state_tax_paid: float
    estimated_tax_payments: float

    # Summary
    estimated_taxable_income: float
    notes: List[str] = Field(default_factory=list)

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
