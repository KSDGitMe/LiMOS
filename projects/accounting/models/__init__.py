"""
Accounting Module Data Models

Pydantic models for accounting domain entities.
"""

from .transactions import (
    Transaction,
    TransactionType,
    RecurringTransaction,
    RecurrenceRule,
    RecurrenceFrequency,
    Account
)

from .forecasting import (
    ForecastConfig,
    ForecastResult,
    DailyBalance,
    CriticalDate,
    VarianceAnalysis,
    ScenarioConfig,
    ForecastComparison,
    ForecastPeriod,
    InterestCompounding,
    ConfidenceLevel
)

from .budgets import (
    Budget,
    BudgetType,
    BudgetStatus,
    CategoryBudget,
    BudgetAlert,
    AlertLevel,
    VarianceReport,
    BudgetTemplate,
    SpendingProjection
)

from .reconciliation import (
    Reconciliation,
    ReconciliationStatus,
    ReconciliationStatement,
    StatementTransaction,
    TransactionMatch,
    MatchStatus,
    Discrepancy,
    DiscrepancyType,
    Payment,
    PaymentStatus,
    PaymentMethod,
    RecurringPayment,
    ReconciliationSummary,
    MatchingSuggestion,
    AdjustmentEntry
)

from .reporting import (
    Report,
    ReportType,
    ReportFormat,
    TimePeriod,
    TrendDirection,
    InsightType,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    SpendingAnalysis,
    IncomeAnalysis,
    TrendAnalysis,
    ComparisonReport,
    Insight,
    KPI,
    Dashboard,
    ScheduledReport,
    TaxSummary,
    CategoryBreakdown,
    TimeSeriesData
)

from .networth import (
    Asset,
    AssetType,
    Liability,
    LiabilityType,
    ValuationMethod,
    NetWorthSnapshot,
    NetWorthTrend,
    AssetAllocation,
    PortfolioPerformance,
    AssetValuation,
    NetWorthGoal,
    DebtPayoffPlan,
    NetWorthReport,
    MarketData
)

from .journal_entries import (
    AccountType,
    FlowDirection,
    Distribution,
    DistributionStatus,
    DebitCredit,
    JournalEntry,
    JournalEntryType,
    JournalEntryStatus,
    ChartOfAccounts,
    AccountBalance,
    AccountLedger,
    RecurringJournalEntry
)

from .budget_envelopes import (
    BudgetEnvelope,
    PaymentEnvelope,
    EnvelopeType,
    RolloverPolicy,
    BudgetAllocation,
    EnvelopeTransaction,
    BankAccountView,
    BudgetPeriodSummary
)

__all__ = [
    # Transactions
    'Transaction',
    'TransactionType',
    'RecurringTransaction',
    'RecurrenceRule',
    'RecurrenceFrequency',
    'Account',

    # Forecasting
    'ForecastConfig',
    'ForecastResult',
    'DailyBalance',
    'CriticalDate',
    'VarianceAnalysis',
    'ScenarioConfig',
    'ForecastComparison',
    'ForecastPeriod',
    'InterestCompounding',
    'ConfidenceLevel',

    # Budgets
    'Budget',
    'BudgetType',
    'BudgetStatus',
    'CategoryBudget',
    'BudgetAlert',
    'AlertLevel',
    'VarianceReport',
    'BudgetTemplate',
    'SpendingProjection',

    # Reconciliation
    'Reconciliation',
    'ReconciliationStatus',
    'ReconciliationStatement',
    'StatementTransaction',
    'TransactionMatch',
    'MatchStatus',
    'Discrepancy',
    'DiscrepancyType',
    'Payment',
    'PaymentStatus',
    'PaymentMethod',
    'RecurringPayment',
    'ReconciliationSummary',
    'MatchingSuggestion',
    'AdjustmentEntry',

    # Reporting
    'Report',
    'ReportType',
    'ReportFormat',
    'TimePeriod',
    'TrendDirection',
    'InsightType',
    'IncomeStatement',
    'BalanceSheet',
    'CashFlowStatement',
    'SpendingAnalysis',
    'IncomeAnalysis',
    'TrendAnalysis',
    'ComparisonReport',
    'Insight',
    'KPI',
    'Dashboard',
    'ScheduledReport',
    'TaxSummary',
    'CategoryBreakdown',
    'TimeSeriesData',

    # Net Worth
    'Asset',
    'AssetType',
    'Liability',
    'LiabilityType',
    'ValuationMethod',
    'NetWorthSnapshot',
    'NetWorthTrend',
    'AssetAllocation',
    'PortfolioPerformance',
    'AssetValuation',
    'NetWorthGoal',
    'DebtPayoffPlan',
    'NetWorthReport',
    'MarketData',

    # Journal Entries (Double-Entry Accounting)
    'AccountType',
    'FlowDirection',
    'Distribution',
    'DistributionStatus',
    'DebitCredit',
    'JournalEntry',
    'JournalEntryType',
    'JournalEntryStatus',
    'ChartOfAccounts',
    'AccountBalance',
    'AccountLedger',
    'RecurringJournalEntry',

    # Budget Envelopes (Virtual Allocation Tracking)
    'BudgetEnvelope',
    'PaymentEnvelope',
    'EnvelopeType',
    'RolloverPolicy',
    'BudgetAllocation',
    'EnvelopeTransaction',
    'BankAccountView',
    'BudgetPeriodSummary'
]
