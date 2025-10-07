"""
Reporting & Analytics Agent

Generates financial reports, performs analytics, identifies insights,
and tracks key performance indicators.

Key Features:
- Generate standard financial reports (Income Statement, Balance Sheet, Cash Flow)
- Spending and income analysis
- Trend analysis and forecasting
- Automated insights and anomaly detection
- KPI tracking
- Custom report builder
"""

import sqlite3
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict
import statistics

from core.agents.base import BaseAgent, AgentConfig
from core.agents.coordination.message_bus import MessageBus, Event
from projects.accounting.models.reporting import (
    Report,
    ReportType,
    ReportFormat,
    TimePeriod,
    TrendDirection,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    SpendingAnalysis,
    IncomeAnalysis,
    TrendAnalysis,
    ComparisonReport,
    Insight,
    InsightType,
    KPI,
    Dashboard,
    ScheduledReport,
    TaxSummary,
    CategoryBreakdown,
    TimeSeriesData
)
from projects.accounting.models.transactions import Transaction, TransactionType


class ReportingAgent(BaseAgent):
    """
    Reporting & Analytics Agent

    Responsibilities:
    - Generate financial reports
    - Analyze spending and income patterns
    - Identify trends and anomalies
    - Provide automated insights
    - Track KPIs
    - Support custom report creation
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.db_path = Path("data/accounting.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.message_bus: Optional[MessageBus] = None

    async def _initialize(self) -> None:
        """Initialize database schema and message bus."""
        await super()._initialize()
        self._setup_database()
        await self._setup_event_subscriptions()

    def _setup_database(self):
        """Create database tables for reporting."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                report_name TEXT NOT NULL,
                parameters TEXT,
                filters TEXT,
                start_date TEXT,
                end_date TEXT,
                as_of_date TEXT,
                data TEXT,
                summary TEXT,
                format TEXT DEFAULT 'json',
                file_path TEXT,
                status TEXT DEFAULT 'completed',
                error_message TEXT,
                generated_at TEXT NOT NULL,
                generated_by TEXT,
                execution_time_ms INTEGER
            )
        """)

        # Insights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                insight_id TEXT PRIMARY KEY,
                insight_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                metric_name TEXT,
                current_value REAL,
                expected_value REAL,
                difference REAL,
                related_category TEXT,
                related_account_id TEXT,
                time_period TEXT,
                actionable INTEGER DEFAULT 0,
                recommended_action TEXT,
                viewed INTEGER DEFAULT 0,
                acted_upon INTEGER DEFAULT 0,
                dismissed INTEGER DEFAULT 0,
                generated_at TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.8
            )
        """)

        # KPIs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kpis (
                kpi_id TEXT PRIMARY KEY,
                kpi_name TEXT NOT NULL,
                description TEXT NOT NULL,
                current_value REAL NOT NULL,
                target_value REAL,
                unit TEXT DEFAULT 'USD',
                on_track INTEGER DEFAULT 1,
                percentage_to_target REAL,
                trend_direction TEXT DEFAULT 'stable',
                change_from_previous REAL,
                change_percentage REAL,
                historical_values TEXT,
                display_format TEXT DEFAULT 'currency',
                color_coding TEXT DEFAULT 'green',
                category TEXT DEFAULT 'general',
                last_updated TEXT NOT NULL
            )
        """)

        # Dashboards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dashboards (
                dashboard_id TEXT PRIMARY KEY,
                dashboard_name TEXT NOT NULL,
                description TEXT,
                widgets TEXT,
                refresh_interval INTEGER DEFAULT 300,
                default_period TEXT DEFAULT 'monthly',
                is_default INTEGER DEFAULT 0,
                owner_id TEXT,
                shared_with TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Scheduled reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_reports (
                scheduled_report_id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                report_name TEXT NOT NULL,
                frequency TEXT NOT NULL,
                day_of_week TEXT,
                day_of_month INTEGER,
                time_of_day TEXT,
                parameters TEXT,
                format TEXT DEFAULT 'pdf',
                recipients TEXT,
                delivery_method TEXT DEFAULT 'email',
                is_active INTEGER DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                last_report_id TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_generated ON reports(generated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_type ON insights(insight_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_viewed ON insights(viewed)")

        conn.commit()
        conn.close()

    async def _setup_event_subscriptions(self):
        """Subscribe to relevant events."""
        from core.agents.coordination.message_bus import get_default_message_bus
        self.message_bus = get_default_message_bus()

        # Subscribe to transaction and budget events for insight generation
        self.message_bus.subscribe(
            agent_id=self.agent_id,
            event_types=[
                "transaction.created",
                "budget.alert.warning",
                "budget.alert.critical",
                "budget.alert.exceeded"
            ],
            callback=self._handle_event_for_insights
        )

    async def _handle_event_for_insights(self, event: Event):
        """Handle events to generate insights."""
        try:
            if event.event_type.startswith("budget.alert"):
                # Generate budget risk insight
                alert_data = event.payload
                insight = Insight(
                    insight_type=InsightType.BUDGET_RISK,
                    title=f"Budget Alert: {alert_data.get('category')}",
                    description=alert_data.get('message', ''),
                    severity="warning" if "warning" in event.event_type else "critical",
                    related_category=alert_data.get('category'),
                    actionable=True,
                    recommended_action=alert_data.get('recommended_action')
                )
                self._save_insight(insight)

        except Exception as e:
            self.logger.error(f"Error handling event for insights: {e}")

    async def _execute(self, task: Dict) -> Dict:
        """Execute reporting operations."""
        operation = task.get("operation")
        parameters = task.get("parameters", {})

        operations = {
            # Standard reports
            "generate_income_statement": self.generate_income_statement,
            "generate_balance_sheet": self.generate_balance_sheet,
            "generate_cash_flow_statement": self.generate_cash_flow_statement,

            # Analysis
            "analyze_spending": self.analyze_spending,
            "analyze_income": self.analyze_income,
            "analyze_trends": self.analyze_trends,
            "compare_periods": self.compare_periods,

            # Insights
            "generate_insights": self.generate_insights,
            "get_insights": self.get_insights,
            "dismiss_insight": self.dismiss_insight,

            # KPIs
            "calculate_kpis": self.calculate_kpis,
            "get_kpi": self.get_kpi,
            "update_kpi": self.update_kpi,

            # Reports management
            "get_report": self.get_report,
            "list_reports": self.list_reports,

            # Tax
            "generate_tax_summary": self.generate_tax_summary,

            # Custom
            "create_custom_report": self.create_custom_report
        }

        if operation not in operations:
            return {
                "status": "error",
                "error": f"Unknown operation: {operation}",
                "available_operations": list(operations.keys())
            }

        try:
            result = await operations[operation](**parameters)
            return {"status": "success", "result": result}
        except Exception as e:
            self.logger.error(f"Error executing {operation}: {e}")
            return {"status": "error", "error": str(e)}

    async def generate_income_statement(
        self,
        start_date: str,
        end_date: str,
        account_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate income statement (P&L).

        Args:
            start_date: Period start date
            end_date: Period end date
            account_ids: Optional list of account IDs to include

        Returns:
            Income statement
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        # Get all transactions for period
        transactions = await self._get_transactions(start, end, account_ids)

        # Separate income and expenses
        income_transactions = [t for t in transactions if t.transaction_type == TransactionType.INCOME]
        expense_transactions = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]

        # Calculate totals
        total_income = sum(t.amount for t in income_transactions)
        total_expenses = sum(t.amount for t in expense_transactions)
        net_income = total_income - total_expenses

        # Break down by category
        income_by_category = self._breakdown_by_category(income_transactions)
        expenses_by_category = self._breakdown_by_category(expense_transactions)

        # Calculate margin
        net_income_margin = (net_income / total_income * 100) if total_income > 0 else 0

        # Create statement
        statement = IncomeStatement(
            start_date=start,
            end_date=end,
            period_label=f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            total_income=total_income,
            income_by_category=income_by_category,
            total_expenses=total_expenses,
            expenses_by_category=expenses_by_category,
            net_income=net_income,
            net_income_margin=net_income_margin
        )

        # Save report
        report = Report(
            report_type=ReportType.INCOME_STATEMENT,
            report_name="Income Statement",
            start_date=start,
            end_date=end,
            data=statement.dict(),
            summary={
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_income": net_income
            }
        )
        self._save_report(report)

        return statement.dict()

    async def generate_balance_sheet(
        self,
        as_of_date: str,
        account_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate balance sheet.

        Args:
            as_of_date: Date for balance sheet
            account_ids: Optional list of account IDs

        Returns:
            Balance sheet
        """
        as_of = date.fromisoformat(as_of_date)

        # Get account balances (simplified - would query accounts table)
        # For now, calculate from transactions
        transactions = await self._get_transactions(
            date(2000, 1, 1),  # From beginning
            as_of,
            account_ids
        )

        # Calculate net balance (simplified)
        total_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
        total_expenses = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)
        net_balance = total_income - total_expenses

        # Simplified balance sheet
        statement = BalanceSheet(
            as_of_date=as_of,
            total_assets=max(net_balance, 0),
            cash_and_equivalents=max(net_balance, 0),
            investments=0.0,
            other_assets=0.0,
            total_liabilities=abs(min(net_balance, 0)),
            credit_card_debt=0.0,
            loans=0.0,
            other_liabilities=abs(min(net_balance, 0)),
            total_equity=net_balance,
            debt_to_asset_ratio=0.0
        )

        # Save report
        report = Report(
            report_type=ReportType.BALANCE_SHEET,
            report_name="Balance Sheet",
            as_of_date=as_of,
            data=statement.dict(),
            summary={
                "total_assets": statement.total_assets,
                "total_liabilities": statement.total_liabilities,
                "total_equity": statement.total_equity
            }
        )
        self._save_report(report)

        return statement.dict()

    async def generate_cash_flow_statement(
        self,
        start_date: str,
        end_date: str,
        account_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate cash flow statement.

        Args:
            start_date: Period start
            end_date: Period end
            account_ids: Optional account IDs

        Returns:
            Cash flow statement
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        # Get transactions
        transactions = await self._get_transactions(start, end, account_ids)

        # Calculate opening balance (transactions before start)
        opening_transactions = await self._get_transactions(
            date(2000, 1, 1),
            start - timedelta(days=1),
            account_ids
        )
        opening_balance = sum(
            t.amount if t.transaction_type == TransactionType.INCOME else -t.amount
            for t in opening_transactions
        )

        # Calculate cash flows
        income_received = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
        expenses_paid = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)

        cash_from_operations = income_received - expenses_paid
        closing_balance = opening_balance + cash_from_operations

        # Create statement
        statement = CashFlowStatement(
            start_date=start,
            end_date=end,
            period_label=f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            net_change=cash_from_operations,
            cash_from_operations=cash_from_operations,
            income_received=income_received,
            expenses_paid=expenses_paid,
            cash_from_investing=0.0,
            investment_purchases=0.0,
            investment_sales=0.0,
            cash_from_financing=0.0,
            loan_proceeds=0.0,
            loan_payments=0.0
        )

        # Save report
        report = Report(
            report_type=ReportType.CASH_FLOW,
            report_name="Cash Flow Statement",
            start_date=start,
            end_date=end,
            data=statement.dict(),
            summary={
                "opening_balance": opening_balance,
                "closing_balance": closing_balance,
                "net_change": cash_from_operations
            }
        )
        self._save_report(report)

        return statement.dict()

    async def analyze_spending(
        self,
        start_date: str,
        end_date: str,
        account_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze spending patterns.

        Args:
            start_date: Analysis start
            end_date: Analysis end
            account_ids: Optional account IDs

        Returns:
            Spending analysis
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        # Get expense transactions
        transactions = await self._get_transactions(start, end, account_ids)
        expenses = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]

        if not expenses:
            return {"error": "No expense transactions found"}

        # Calculate statistics
        total_spending = sum(t.amount for t in expenses)
        transaction_count = len(expenses)
        amounts = [t.amount for t in expenses]
        average_transaction = statistics.mean(amounts)
        median_transaction = statistics.median(amounts)

        # Break down by category
        spending_by_category = self._breakdown_by_category(expenses)
        top_categories = [c.category for c in sorted(
            spending_by_category,
            key=lambda x: x.amount,
            reverse=True
        )[:5]]

        # Break down by merchant
        merchant_totals = defaultdict(float)
        for t in expenses:
            merchant_totals[t.merchant] += t.amount

        spending_by_merchant = [
            {"merchant": merchant, "amount": amount, "transaction_count": sum(1 for t in expenses if t.merchant == merchant)}
            for merchant, amount in sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)
        ]
        top_merchants = [m["merchant"] for m in spending_by_merchant[:5]]

        # Calculate averages
        days = (end - start).days + 1
        daily_average = total_spending / days if days > 0 else 0
        weekly_average = daily_average * 7
        monthly_average = daily_average * 30

        # Day of week analysis
        spending_by_day = defaultdict(float)
        for t in expenses:
            day_name = t.date.strftime('%A')
            spending_by_day[day_name] += t.amount

        peak_day = max(spending_by_day.items(), key=lambda x: x[1])[0] if spending_by_day else None

        # Create analysis
        analysis = SpendingAnalysis(
            start_date=start,
            end_date=end,
            period_label=f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            total_spending=total_spending,
            transaction_count=transaction_count,
            average_transaction=average_transaction,
            median_transaction=median_transaction,
            spending_by_category=spending_by_category,
            top_categories=top_categories,
            spending_by_merchant=spending_by_merchant,
            top_merchants=top_merchants,
            daily_average=daily_average,
            weekly_average=weekly_average,
            monthly_average=monthly_average,
            spending_by_day_of_week=dict(spending_by_day),
            peak_spending_day=peak_day
        )

        return analysis.dict()

    async def analyze_income(
        self,
        start_date: str,
        end_date: str,
        account_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze income patterns.

        Args:
            start_date: Analysis start
            end_date: Analysis end
            account_ids: Optional account IDs

        Returns:
            Income analysis
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        # Get income transactions
        transactions = await self._get_transactions(start, end, account_ids)
        income_trans = [t for t in transactions if t.transaction_type == TransactionType.INCOME]

        if not income_trans:
            return {"error": "No income transactions found"}

        # Calculate statistics
        total_income = sum(t.amount for t in income_trans)
        transaction_count = len(income_trans)
        amounts = [t.amount for t in income_trans]
        average_transaction = statistics.mean(amounts)

        # Break down by category
        income_by_category = self._breakdown_by_category(income_trans)
        top_sources = [c.category for c in sorted(
            income_by_category,
            key=lambda x: x.amount,
            reverse=True
        )[:5]]

        # Calculate monthly average
        days = (end - start).days + 1
        monthly_average = (total_income / days) * 30 if days > 0 else 0

        # Create analysis
        analysis = IncomeAnalysis(
            start_date=start,
            end_date=end,
            period_label=f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            total_income=total_income,
            transaction_count=transaction_count,
            average_transaction=average_transaction,
            income_by_category=income_by_category,
            top_sources=top_sources,
            monthly_average=monthly_average
        )

        return analysis.dict()

    async def analyze_trends(
        self,
        metric_name: str,
        time_period: str,
        start_date: str,
        end_date: str,
        account_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze trends over time.

        Args:
            metric_name: Metric to analyze ("spending", "income", "net_income")
            time_period: Period granularity ("monthly", "weekly", "daily")
            start_date: Start date
            end_date: End date
            account_ids: Optional account IDs

        Returns:
            Trend analysis
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        period_enum = TimePeriod(time_period)

        # Get transactions
        transactions = await self._get_transactions(start, end, account_ids)

        # Group by time period
        time_series = self._create_time_series(transactions, metric_name, period_enum, start, end)

        # Calculate statistics
        values = [ts.value for ts in time_series]
        if not values:
            return {"error": "No data for trend analysis"}

        mean_value = statistics.mean(values)
        median_value = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        min_value = min(values)
        max_value = max(values)

        # Determine trend direction
        if len(values) >= 2:
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)

            change_pct = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0

            if change_pct > 10:
                trend_direction = TrendDirection.INCREASING
            elif change_pct < -10:
                trend_direction = TrendDirection.DECREASING
            else:
                trend_direction = TrendDirection.STABLE
        else:
            trend_direction = TrendDirection.STABLE
            change_pct = 0.0

        # Create analysis
        analysis = TrendAnalysis(
            metric_name=metric_name,
            time_period=period_enum,
            start_date=start,
            end_date=end,
            time_series=time_series,
            mean=mean_value,
            median=median_value,
            std_deviation=std_dev,
            min_value=min_value,
            max_value=max_value,
            trend_direction=trend_direction,
            trend_percentage=change_pct
        )

        return analysis.dict()

    async def compare_periods(
        self,
        current_start: str,
        current_end: str,
        previous_start: str,
        previous_end: str,
        account_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Compare two time periods.

        Args:
            current_start: Current period start
            current_end: Current period end
            previous_start: Previous period start
            previous_end: Previous period end
            account_ids: Optional account IDs

        Returns:
            Comparison report
        """
        curr_start = date.fromisoformat(current_start)
        curr_end = date.fromisoformat(current_end)
        prev_start = date.fromisoformat(previous_start)
        prev_end = date.fromisoformat(previous_end)

        # Get transactions for both periods
        current_trans = await self._get_transactions(curr_start, curr_end, account_ids)
        previous_trans = await self._get_transactions(prev_start, prev_end, account_ids)

        # Calculate metrics
        metrics = []

        # Total spending
        curr_spending = sum(t.amount for t in current_trans if t.transaction_type == TransactionType.EXPENSE)
        prev_spending = sum(t.amount for t in previous_trans if t.transaction_type == TransactionType.EXPENSE)
        spending_change = curr_spending - prev_spending
        spending_change_pct = (spending_change / prev_spending * 100) if prev_spending > 0 else 0

        metrics.append({
            "name": "Total Spending",
            "current_value": curr_spending,
            "previous_value": prev_spending,
            "change": spending_change,
            "change_percentage": spending_change_pct
        })

        # Total income
        curr_income = sum(t.amount for t in current_trans if t.transaction_type == TransactionType.INCOME)
        prev_income = sum(t.amount for t in previous_trans if t.transaction_type == TransactionType.INCOME)
        income_change = curr_income - prev_income
        income_change_pct = (income_change / prev_income * 100) if prev_income > 0 else 0

        metrics.append({
            "name": "Total Income",
            "current_value": curr_income,
            "previous_value": prev_income,
            "change": income_change,
            "change_percentage": income_change_pct
        })

        # Net income
        curr_net = curr_income - curr_spending
        prev_net = prev_income - prev_spending
        net_change = curr_net - prev_net
        net_change_pct = (net_change / prev_net * 100) if prev_net != 0 else 0

        metrics.append({
            "name": "Net Income",
            "current_value": curr_net,
            "previous_value": prev_net,
            "change": net_change,
            "change_percentage": net_change_pct
        })

        # Identify improvements/declines
        improvements = [m["name"] for m in metrics if m["change"] > 0 and "Income" in m["name"]] + \
                      [m["name"] for m in metrics if m["change"] < 0 and "Spending" in m["name"]]

        declines = [m["name"] for m in metrics if m["change"] < 0 and "Income" in m["name"]] + \
                  [m["name"] for m in metrics if m["change"] > 0 and "Spending" in m["name"]]

        # Create report
        report = ComparisonReport(
            current_period_start=curr_start,
            current_period_end=curr_end,
            previous_period_start=prev_start,
            previous_period_end=prev_end,
            metrics=metrics,
            improvements=improvements,
            declines=declines
        )

        return report.dict()

    async def generate_insights(
        self,
        account_ids: Optional[List[str]] = None,
        lookback_days: int = 30
    ) -> List[Dict]:
        """
        Generate automated insights.

        Args:
            account_ids: Optional account IDs
            lookback_days: Days to look back for analysis

        Returns:
            List of insights
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        transactions = await self._get_transactions(start_date, end_date, account_ids)
        insights = []

        # Detect spending spikes
        expenses = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]
        if expenses:
            amounts = [t.amount for t in expenses]
            avg = statistics.mean(amounts)
            std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0

            for t in expenses:
                if t.amount > avg + (2 * std_dev):  # 2 standard deviations above mean
                    insight = Insight(
                        insight_type=InsightType.SPENDING_SPIKE,
                        title="Unusual Large Expense Detected",
                        description=f"${t.amount:.2f} spent at {t.merchant} on {t.date}",
                        severity="warning",
                        current_value=t.amount,
                        expected_value=avg,
                        difference=t.amount - avg,
                        related_category=t.category
                    )
                    insights.append(insight)
                    self._save_insight(insight)

        return [i.dict() for i in insights]

    async def get_insights(
        self,
        viewed: Optional[bool] = None,
        dismissed: Optional[bool] = False,
        limit: int = 10
    ) -> List[Dict]:
        """Get insights with filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM insights WHERE dismissed = ?"
        params = [1 if dismissed else 0]

        if viewed is not None:
            query += " AND viewed = ?"
            params.append(1 if viewed else 0)

        query += " ORDER BY generated_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        insights = []
        for row in cursor.fetchall():
            insights.append({
                "insight_id": row[0],
                "insight_type": row[1],
                "title": row[2],
                "description": row[3],
                "severity": row[4],
                "actionable": bool(row[13]),
                "recommended_action": row[14]
            })

        conn.close()
        return insights

    async def dismiss_insight(self, insight_id: str) -> Dict:
        """Dismiss an insight."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE insights
            SET dismissed = 1
            WHERE insight_id = ?
        """, (insight_id,))

        conn.commit()
        conn.close()

        return {"insight_id": insight_id, "dismissed": True}

    async def calculate_kpis(
        self,
        account_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Calculate key performance indicators."""
        kpis = []

        # Monthly spending KPI
        today = date.today()
        month_start = date(today.year, today.month, 1)

        transactions = await self._get_transactions(month_start, today, account_ids)
        monthly_spending = sum(
            t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE
        )

        spending_kpi = KPI(
            kpi_name="Monthly Spending",
            description="Total spending for current month",
            current_value=monthly_spending,
            unit="USD",
            display_format="currency",
            category="spending"
        )
        kpis.append(spending_kpi)
        self._save_kpi(spending_kpi)

        # Monthly income KPI
        monthly_income = sum(
            t.amount for t in transactions if t.transaction_type == TransactionType.INCOME
        )

        income_kpi = KPI(
            kpi_name="Monthly Income",
            description="Total income for current month",
            current_value=monthly_income,
            unit="USD",
            display_format="currency",
            category="income"
        )
        kpis.append(income_kpi)
        self._save_kpi(income_kpi)

        # Savings rate KPI
        savings_rate = ((monthly_income - monthly_spending) / monthly_income * 100) if monthly_income > 0 else 0

        savings_kpi = KPI(
            kpi_name="Savings Rate",
            description="Percentage of income saved",
            current_value=savings_rate,
            target_value=20.0,
            unit="%",
            display_format="percentage",
            category="savings",
            on_track=savings_rate >= 20.0,
            color_coding="green" if savings_rate >= 20 else "yellow" if savings_rate >= 10 else "red"
        )
        kpis.append(savings_kpi)
        self._save_kpi(savings_kpi)

        return [k.dict() for k in kpis]

    async def get_kpi(self, kpi_name: str) -> Optional[Dict]:
        """Get KPI by name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM kpis
            WHERE kpi_name = ?
            ORDER BY last_updated DESC
            LIMIT 1
        """, (kpi_name,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "kpi_id": row[0],
            "kpi_name": row[1],
            "current_value": row[3],
            "target_value": row[4],
            "on_track": bool(row[6])
        }

    async def update_kpi(self, kpi_name: str, new_value: float) -> Dict:
        """Update KPI value."""
        # Implementation for updating KPI
        return {"status": "not_implemented"}

    async def get_report(self, report_id: str) -> Optional[Dict]:
        """Get report by ID."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reports WHERE report_id = ?", (report_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "report_id": row[0],
            "report_type": row[1],
            "report_name": row[2],
            "generated_at": row[13],
            "data": json.loads(row[8]) if row[8] else {}
        }

    async def list_reports(
        self,
        report_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """List reports with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT report_id, report_type, report_name, generated_at FROM reports WHERE 1=1"
        params = []

        if report_type:
            query += " AND report_type = ?"
            params.append(report_type)

        query += " ORDER BY generated_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        reports = []
        for row in cursor.fetchall():
            reports.append({
                "report_id": row[0],
                "report_type": row[1],
                "report_name": row[2],
                "generated_at": row[3]
            })

        conn.close()
        return reports

    async def generate_tax_summary(
        self,
        tax_year: int,
        account_ids: Optional[List[str]] = None
    ) -> Dict:
        """Generate tax summary for year."""
        start_date = date(tax_year, 1, 1)
        end_date = date(tax_year, 12, 31)

        transactions = await self._get_transactions(start_date, end_date, account_ids)

        # Separate income and deductions
        income_trans = [t for t in transactions if t.transaction_type == TransactionType.INCOME]
        expense_trans = [t for t in transactions if t.transaction_type == TransactionType.EXPENSE]

        total_income = sum(t.amount for t in income_trans)
        total_deductions = sum(t.amount for t in expense_trans)

        income_by_category = self._breakdown_by_category(income_trans)
        deductions_by_category = self._breakdown_by_category(expense_trans)

        summary = TaxSummary(
            tax_year=tax_year,
            start_date=start_date,
            end_date=end_date,
            total_income=total_income,
            w2_income=0.0,
            1099_income=0.0,
            other_income=total_income,
            income_by_category=income_by_category,
            total_deductions=total_deductions,
            business_expenses=0.0,
            charitable_contributions=0.0,
            medical_expenses=0.0,
            other_deductions=total_deductions,
            deductions_by_category=deductions_by_category,
            federal_tax_paid=0.0,
            state_tax_paid=0.0,
            estimated_tax_payments=0.0,
            estimated_taxable_income=total_income - total_deductions
        )

        return summary.dict()

    async def create_custom_report(self, report_config: Dict) -> Dict:
        """Create custom report."""
        # Placeholder for custom report builder
        return {"status": "not_implemented"}

    # Helper methods

    async def _get_transactions(
        self,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None
    ) -> List[Transaction]:
        """Get transactions for period."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT * FROM transactions
            WHERE date >= ? AND date <= ?
        """
        params = [start_date.isoformat(), end_date.isoformat()]

        if account_ids:
            placeholders = ','.join('?' * len(account_ids))
            query += f" AND account_id IN ({placeholders})"
            params.extend(account_ids)

        query += " ORDER BY date"

        cursor.execute(query, params)

        transactions = []
        for row in cursor.fetchall():
            transactions.append(Transaction(
                transaction_id=row[0],
                account_id=row[1],
                date=date.fromisoformat(row[2]),
                merchant=row[3],
                amount=row[4],
                transaction_type=TransactionType(row[5]),
                category=row[6],
                subcategory=row[7] if row[7] else None
            ))

        conn.close()
        return transactions

    def _breakdown_by_category(
        self,
        transactions: List[Transaction]
    ) -> List[CategoryBreakdown]:
        """Break down transactions by category."""
        category_totals = defaultdict(lambda: {"amount": 0.0, "count": 0})

        for t in transactions:
            key = (t.category, t.subcategory)
            category_totals[key]["amount"] += t.amount
            category_totals[key]["count"] += 1

        total_amount = sum(t.amount for t in transactions)

        breakdowns = []
        for (category, subcategory), data in category_totals.items():
            breakdown = CategoryBreakdown(
                category=category,
                subcategory=subcategory,
                amount=data["amount"],
                transaction_count=data["count"],
                percentage_of_total=(data["amount"] / total_amount * 100) if total_amount > 0 else 0,
                average_transaction=data["amount"] / data["count"] if data["count"] > 0 else 0
            )
            breakdowns.append(breakdown)

        return sorted(breakdowns, key=lambda x: x.amount, reverse=True)

    def _create_time_series(
        self,
        transactions: List[Transaction],
        metric_name: str,
        period: TimePeriod,
        start: date,
        end: date
    ) -> List[TimeSeriesData]:
        """Create time series data from transactions."""
        series = []

        # Group transactions by period
        if period == TimePeriod.MONTHLY:
            # Group by month
            current = date(start.year, start.month, 1)
            while current <= end:
                next_month = date(current.year + (current.month // 12), (current.month % 12) + 1, 1)
                period_end = min(next_month - timedelta(days=1), end)

                period_transactions = [
                    t for t in transactions
                    if current <= t.date <= period_end
                ]

                value = self._calculate_metric_value(period_transactions, metric_name)

                series.append(TimeSeriesData(
                    period=current.strftime('%Y-%m'),
                    period_start=current,
                    period_end=period_end,
                    value=value
                ))

                current = next_month

        return series

    def _calculate_metric_value(
        self,
        transactions: List[Transaction],
        metric_name: str
    ) -> float:
        """Calculate metric value for transactions."""
        if metric_name == "spending":
            return sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)
        elif metric_name == "income":
            return sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
        elif metric_name == "net_income":
            income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.INCOME)
            expenses = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE)
            return income - expenses
        return 0.0

    def _save_report(self, report: Report):
        """Save report to database."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reports (
                report_id, report_type, report_name, parameters, filters,
                start_date, end_date, as_of_date, data, summary,
                format, file_path, status, error_message,
                generated_at, generated_by, execution_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.report_id,
            report.report_type.value,
            report.report_name,
            json.dumps(report.parameters),
            json.dumps(report.filters),
            report.start_date.isoformat() if report.start_date else None,
            report.end_date.isoformat() if report.end_date else None,
            report.as_of_date.isoformat() if report.as_of_date else None,
            json.dumps(report.data),
            json.dumps(report.summary),
            report.format.value,
            report.file_path,
            report.status,
            report.error_message,
            report.generated_at.isoformat(),
            report.generated_by,
            report.execution_time_ms
        ))

        conn.commit()
        conn.close()

    def _save_insight(self, insight: Insight):
        """Save insight to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO insights (
                insight_id, insight_type, title, description, severity,
                metric_name, current_value, expected_value, difference,
                related_category, related_account_id, time_period,
                actionable, recommended_action, viewed, acted_upon,
                dismissed, generated_at, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            insight.insight_id,
            insight.insight_type.value,
            insight.title,
            insight.description,
            insight.severity,
            insight.metric_name,
            insight.current_value,
            insight.expected_value,
            insight.difference,
            insight.related_category,
            insight.related_account_id,
            insight.time_period,
            1 if insight.actionable else 0,
            insight.recommended_action,
            1 if insight.viewed else 0,
            1 if insight.acted_upon else 0,
            1 if insight.dismissed else 0,
            insight.generated_at.isoformat(),
            insight.confidence_score
        ))

        conn.commit()
        conn.close()

    def _save_kpi(self, kpi: KPI):
        """Save KPI to database."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO kpis (
                kpi_id, kpi_name, description, current_value, target_value,
                unit, on_track, percentage_to_target, trend_direction,
                change_from_previous, change_percentage, historical_values,
                display_format, color_coding, category, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            kpi.kpi_id,
            kpi.kpi_name,
            kpi.description,
            kpi.current_value,
            kpi.target_value,
            kpi.unit,
            1 if kpi.on_track else 0,
            kpi.percentage_to_target,
            kpi.trend_direction.value,
            kpi.change_from_previous,
            kpi.change_percentage,
            json.dumps([ts.dict() for ts in kpi.historical_values]),
            kpi.display_format,
            kpi.color_coding,
            kpi.category,
            kpi.last_updated.isoformat()
        ))

        conn.commit()
        conn.close()
