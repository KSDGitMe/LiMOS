"""
Budget Data Models

Models for budget management, tracking, and variance analysis.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class BudgetType(str, Enum):
    """Budget type categories."""
    MONTHLY = "monthly"
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    WEEKLY = "weekly"
    ENVELOPE = "envelope"  # Envelope budgeting
    ROLLING = "rolling"  # Rolling period


class BudgetStatus(str, Enum):
    """Budget status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    EXCEEDED = "exceeded"


class AlertLevel(str, Enum):
    """Budget alert threshold levels."""
    WARNING = "warning"  # 80%
    CRITICAL = "critical"  # 90%
    EXCEEDED = "exceeded"  # 100%


class CategoryBudget(BaseModel):
    """
    Budget allocation for a specific category.

    Each budget can have multiple category allocations.
    """
    category_budget_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    subcategory: Optional[str] = None
    allocated_amount: float
    spent_amount: float = 0.0
    remaining_amount: float = 0.0
    percent_used: float = 0.0

    # Rollover settings
    allow_rollover: bool = False
    rollover_from_previous: float = 0.0

    # Alerts
    alert_thresholds: List[float] = Field(default_factory=lambda: [0.8, 0.9, 1.0])
    alerts_triggered: List[str] = Field(default_factory=list)

    # Metadata
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    def update_spent(self, amount: float):
        """Update spent amount and recalculate metrics."""
        self.spent_amount += amount
        self.remaining_amount = self.allocated_amount - self.spent_amount
        self.percent_used = (self.spent_amount / self.allocated_amount) if self.allocated_amount > 0 else 0.0

        # Check alert thresholds
        for threshold in self.alert_thresholds:
            if self.percent_used >= threshold:
                alert_level = "exceeded" if threshold >= 1.0 else "critical" if threshold >= 0.9 else "warning"
                alert_key = f"{alert_level}_{int(threshold * 100)}"
                if alert_key not in self.alerts_triggered:
                    self.alerts_triggered.append(alert_key)


class Budget(BaseModel):
    """
    Complete budget with category allocations.

    Tracks spending across categories for a specific time period.
    """
    budget_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    budget_name: str
    budget_type: BudgetType
    account_ids: List[str] = Field(default_factory=list)  # Accounts this budget applies to

    # Time period
    start_date: date
    end_date: date
    current_period: str  # "2025-01", "2025-Q1", etc.

    # Total budget
    total_allocated: float
    total_spent: float = 0.0
    total_remaining: float = 0.0
    percent_used: float = 0.0

    # Category allocations
    categories: List[CategoryBudget] = Field(default_factory=list)

    # Status
    status: BudgetStatus = BudgetStatus.ACTIVE
    is_exceeded: bool = False

    # Settings
    auto_create_next_period: bool = True
    rollover_unused: bool = False

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    def get_category_budget(self, category: str, subcategory: Optional[str] = None) -> Optional[CategoryBudget]:
        """Get budget for a specific category."""
        for cat_budget in self.categories:
            if cat_budget.category == category and cat_budget.subcategory == subcategory:
                return cat_budget
        return None

    def update_spending(self, category: str, amount: float, subcategory: Optional[str] = None):
        """Update spending for a category."""
        cat_budget = self.get_category_budget(category, subcategory)
        if cat_budget:
            cat_budget.update_spent(amount)
            self._recalculate_totals()

    def _recalculate_totals(self):
        """Recalculate total metrics."""
        self.total_spent = sum(cat.spent_amount for cat in self.categories)
        self.total_remaining = self.total_allocated - self.total_spent
        self.percent_used = (self.total_spent / self.total_allocated) if self.total_allocated > 0 else 0.0
        self.is_exceeded = self.total_spent > self.total_allocated

        if self.is_exceeded:
            self.status = BudgetStatus.EXCEEDED

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


class BudgetAlert(BaseModel):
    """
    Budget alert notification.

    Generated when budget thresholds are exceeded.
    """
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    budget_id: str
    category_budget_id: Optional[str] = None
    alert_level: AlertLevel
    alert_type: str  # "threshold_reached", "exceeded", "projected_overrun"

    # Details
    category: str
    subcategory: Optional[str] = None
    allocated_amount: float
    spent_amount: float
    percent_used: float
    threshold: float

    # Message
    title: str
    message: str
    recommended_action: Optional[str] = None

    # Timing
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VarianceReport(BaseModel):
    """
    Variance analysis report comparing actual vs budgeted spending.

    Shows how actual spending differs from budget allocations.
    """
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    budget_id: str
    report_period: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Overall variance
    total_budgeted: float
    total_actual: float
    total_variance: float
    variance_percentage: float

    # Category variances
    category_variances: List[Dict[str, Any]] = Field(default_factory=list)

    # Analysis
    categories_over_budget: int = 0
    categories_under_budget: int = 0
    largest_overrun_category: Optional[str] = None
    largest_overrun_amount: float = 0.0
    largest_underrun_category: Optional[str] = None
    largest_underrun_amount: float = 0.0

    # Trends
    spending_trend: str = "stable"  # "increasing", "decreasing", "stable"
    forecast_end_of_period: float = 0.0

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BudgetTemplate(BaseModel):
    """
    Budget template for creating recurring budgets.

    Templates can be used to automatically create budgets for new periods.
    """
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_name: str
    budget_type: BudgetType

    # Category allocations (as percentages or fixed amounts)
    category_allocations: Dict[str, float] = Field(default_factory=dict)
    use_percentages: bool = True  # If True, values are percentages; if False, fixed amounts

    # Settings
    auto_create_for_period: bool = True
    rollover_unused: bool = False

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SpendingProjection(BaseModel):
    """
    Projected spending for budget period.

    Uses historical patterns and current trajectory to predict end-of-period spending.
    """
    projection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    budget_id: str
    category: str
    subcategory: Optional[str] = None

    # Current state
    days_elapsed: int
    days_remaining: int
    percent_period_complete: float

    # Actual spending
    allocated_amount: float
    spent_to_date: float
    percent_used: float

    # Projections
    projected_total_spending: float
    projected_variance: float
    projected_percent_used: float

    # Confidence
    confidence_level: float = 0.0
    projection_method: str = "linear"  # "linear", "average_daily", "trend_based"

    # Status
    will_exceed_budget: bool = False
    days_until_exceeded: Optional[int] = None

    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
