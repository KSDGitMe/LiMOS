"""
Cash Flow Forecasting Agent

Generates day-by-day balance projections using historical transactions,
recurring transactions, and scheduled payments. Includes interest calculations
and confidence interval generation.
"""

import asyncio
import logging
import sqlite3
import statistics
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import json

from core.agents.base import BaseAgent, AgentConfig, AgentCapability
from core.agents.coordination import get_message_bus, MessageBus, EventPriority
from ..models.transactions import Transaction, TransactionType, Account
from ..models.forecasting import (
    ForecastConfig,
    ForecastResult,
    DailyBalance,
    CriticalDate,
    VarianceAnalysis,
    InterestCompounding,
    ConfidenceLevel
)

logger = logging.getLogger(__name__)


class CashFlowForecastingAgent(BaseAgent):
    """
    Cash Flow Forecasting Agent.

    Responsibilities:
    - Day-by-day balance calculation
    - Historical balance reconstruction (work backwards from current)
    - Future projection using recurring transactions
    - Interest calculation for savings and credit accounts
    - Confidence interval generation
    - Critical date identification
    """

    def __init__(self, config: Optional[AgentConfig] = None, message_bus: Optional[MessageBus] = None):
        """Initialize Cash Flow Forecasting Agent."""
        if config is None:
            config = AgentConfig(
                name="CashFlowForecastingAgent",
                description="Projects account balances and cash flow with confidence intervals",
                capabilities=[
                    AgentCapability.DATA_EXTRACTION,
                    AgentCapability.DATABASE_OPERATIONS
                ]
            )
        super().__init__(config)
        self.message_bus = message_bus or get_message_bus()
        self.transaction_db_path = Path("storage/accounting/transactions.db")
        self.forecast_db_path = Path("storage/accounting/forecasts.db")
        logger.info(f"CashFlowForecastingAgent '{self.name}' initialized")

    async def _initialize(self) -> None:
        """Initialize database and subscribe to events."""
        # Create database
        self.forecast_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        # Subscribe to transaction events (forecasts need updating)
        self.message_bus.subscribe(
            agent_id=self.config.agent_id,
            event_types=[
                "transaction.created",
                "transaction.updated",
                "recurring_transaction.created",
                "recurring_transaction.modified",
                "account_balance.updated"
            ],
            callback=self._handle_transaction_event
        )

        logger.info("CashFlowForecastingAgent initialized and subscribed to events")

    def _init_database(self):
        """Initialize SQLite database for forecast storage."""
        with sqlite3.connect(self.forecast_db_path) as conn:
            cursor = conn.cursor()

            # Forecasts metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forecasts (
                    forecast_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    reference_date TEXT NOT NULL,
                    reference_balance REAL NOT NULL,
                    config TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    calculation_time_ms REAL
                )
            """)

            # Daily balances table (the core forecast data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_balances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    forecast_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    opening_balance REAL NOT NULL,
                    closing_balance REAL NOT NULL,
                    daily_change REAL NOT NULL,
                    income REAL DEFAULT 0,
                    expenses REAL DEFAULT 0,
                    transfers REAL DEFAULT 0,
                    interest_earned REAL DEFAULT 0,
                    transaction_count INTEGER DEFAULT 0,
                    transaction_ids TEXT,
                    point_estimate REAL NOT NULL,
                    lower_bound REAL NOT NULL,
                    upper_bound REAL NOT NULL,
                    margin_of_error REAL NOT NULL,
                    confidence_level REAL DEFAULT 0.95,
                    is_critical_date INTEGER DEFAULT 0,
                    is_large_expense INTEGER DEFAULT 0,
                    is_payday INTEGER DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (forecast_id) REFERENCES forecasts(forecast_id)
                )
            """)

            # Critical dates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS critical_dates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    forecast_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    projected_balance REAL NOT NULL,
                    threshold REAL,
                    description TEXT NOT NULL,
                    recommended_action TEXT,
                    FOREIGN KEY (forecast_id) REFERENCES forecasts(forecast_id)
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_balances_forecast ON daily_balances(forecast_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_balances_date ON daily_balances(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_critical_dates_forecast ON critical_dates(forecast_id)")

            conn.commit()
            logger.info("Forecast database initialized successfully")

    async def _execute(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute forecasting operations."""
        operation = input_data.get("operation")
        if not operation:
            return {"success": False, "error": "No operation specified"}

        operations = {
            "create_forecast": self.create_forecast,
            "get_forecast": self.get_forecast,
            "get_daily_balances": self.get_daily_balances,
            "get_critical_dates": self.get_critical_dates,
            "recalculate_forecast": self.recalculate_forecast,
            "analyze_variance": self.analyze_variance
        }

        method = operations.get(operation)
        if not method:
            return {"success": False, "error": f"Unknown operation: {operation}"}

        params = input_data.get("parameters", {})
        return method(**params)

    def create_forecast(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new cash flow forecast.

        This is the MAIN entry point for forecast generation.
        """
        try:
            start_time = datetime.utcnow()

            # Parse configuration
            config = ForecastConfig(**config_data)

            logger.info(
                f"Creating forecast for account {config.account_id} "
                f"from {config.start_date} to {config.end_date}"
            )

            # STEP 1: Reconstruct opening balance if start_date is in the past
            opening_balance = self._calculate_opening_balance(config)

            # STEP 2: Gather all transactions (historical + scheduled + recurring)
            all_transactions = self._gather_all_transactions(config)

            # STEP 3: Calculate day-by-day balances
            daily_balances = self._calculate_daily_balances(
                config,
                opening_balance,
                all_transactions
            )

            # STEP 4: Identify critical dates
            critical_dates = self._identify_critical_dates(config, daily_balances)

            # STEP 5: Calculate summary statistics
            summary = self._calculate_summary_stats(daily_balances)

            # Create forecast result
            calculation_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            result = ForecastResult(
                forecast_id=config.forecast_id,
                account_id=config.account_id,
                config=config,
                daily_balances=daily_balances,
                opening_balance=opening_balance,
                closing_balance=daily_balances[-1].closing_balance if daily_balances else opening_balance,
                total_income=summary["total_income"],
                total_expenses=summary["total_expenses"],
                total_interest=summary["total_interest"],
                net_change=summary["net_change"],
                start_date=config.start_date,
                end_date=config.end_date,
                days_projected=len(daily_balances),
                critical_dates=critical_dates,
                overall_confidence=summary["avg_confidence"],
                min_balance=summary["min_balance"],
                min_balance_date=summary["min_balance_date"],
                max_balance=summary["max_balance"],
                max_balance_date=summary["max_balance_date"],
                avg_daily_balance=summary["avg_balance"],
                calculation_time_ms=calculation_time
            )

            # Store forecast
            self._store_forecast(result)

            # Publish event
            asyncio.create_task(self.message_bus.publish(
                event_type="forecast.created",
                payload={"forecast_id": result.forecast_id, "account_id": result.account_id},
                source_agent=self.config.agent_id,
                priority=EventPriority.NORMAL
            ))

            logger.info(
                f"Forecast created: {result.forecast_id} "
                f"({len(daily_balances)} days, {calculation_time:.2f}ms)"
            )

            return {
                "success": True,
                "forecast_id": result.forecast_id,
                "forecast": result.dict()
            }

        except Exception as e:
            logger.error(f"Error creating forecast: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _calculate_opening_balance(self, config: ForecastConfig) -> float:
        """
        Calculate opening balance for the forecast.

        CRITICAL ALGORITHM:
        If start_date is in the past, work backwards from reference_balance
        by subtracting all transactions between start_date and reference_date.

        Opening Balance = Reference Balance - Sum(transactions from start to reference)
        """
        # If start date is at or after reference date, use reference balance
        if config.start_date >= config.reference_date:
            logger.info(
                f"Start date {config.start_date} >= reference date {config.reference_date}, "
                f"using reference balance: {config.reference_balance}"
            )
            return config.reference_balance

        # Need to reconstruct historical opening balance
        logger.info(
            f"Reconstructing opening balance: working backwards from "
            f"{config.reference_date} (balance: {config.reference_balance}) to {config.start_date}"
        )

        # Get all actual transactions between start_date and reference_date
        historical_transactions = self._get_historical_transactions(
            config.account_id,
            config.start_date,
            config.reference_date
        )

        # Calculate opening balance by subtracting transactions
        opening_balance = config.reference_balance

        for trans in historical_transactions:
            if trans.transaction_type == TransactionType.INCOME:
                opening_balance -= trans.amount
            elif trans.transaction_type == TransactionType.EXPENSE:
                opening_balance += trans.amount
            # Transfers handled separately depending on direction

        logger.info(
            f"Calculated opening balance: {opening_balance} "
            f"({len(historical_transactions)} transactions subtracted)"
        )

        return opening_balance

    def _gather_all_transactions(self, config: ForecastConfig) -> Dict[date, List[Transaction]]:
        """
        Gather all transactions for the forecast period.

        Returns dict mapping date -> list of transactions on that date.
        """
        transactions_by_date = defaultdict(list)

        # Historical actual transactions (if start_date is in past)
        if config.include_historical_transactions and config.start_date < date.today():
            historical = self._get_historical_transactions(
                config.account_id,
                config.start_date,
                min(date.today(), config.end_date)
            )
            for trans in historical:
                transactions_by_date[trans.date].append(trans)

        # Scheduled transactions (already created)
        if config.include_scheduled_transactions:
            scheduled = self._get_scheduled_transactions(
                config.account_id,
                max(date.today(), config.start_date),
                config.end_date
            )
            for trans in scheduled:
                transactions_by_date[trans.date].append(trans)

        # Recurring transaction projections (not yet created)
        if config.include_recurring_transactions:
            projected = self._project_recurring_transactions(
                config.account_id,
                max(date.today(), config.start_date),
                config.end_date
            )
            for trans in projected:
                transactions_by_date[trans.date].append(trans)

        logger.info(
            f"Gathered transactions: "
            f"{sum(len(v) for v in transactions_by_date.values())} total across "
            f"{len(transactions_by_date)} days"
        )

        return transactions_by_date

    def _calculate_daily_balances(
        self,
        config: ForecastConfig,
        opening_balance: float,
        transactions_by_date: Dict[date, List[Transaction]]
    ) -> List[DailyBalance]:
        """
        Calculate day-by-day balances - THE CORE FORECAST ALGORITHM.

        For each day from start_date to end_date:
        1. Opening balance = previous day's closing
        2. Add/subtract transactions
        3. Calculate interest if applicable
        4. Closing balance = opening + daily change
        5. Generate confidence interval
        """
        daily_balances = []
        current_date = config.start_date
        current_balance = opening_balance

        # Get variance analysis for confidence intervals
        variance = self._get_variance_analysis(config.account_id) if config.generate_confidence_intervals else None

        while current_date <= config.end_date:
            # Opening balance for this day
            opening = current_balance

            # Get transactions for this day
            day_transactions = transactions_by_date.get(current_date, [])

            # Calculate daily change
            income = sum(t.amount for t in day_transactions if t.transaction_type == TransactionType.INCOME)
            expenses = sum(t.amount for t in day_transactions if t.transaction_type == TransactionType.EXPENSE)
            transfers = sum(t.amount for t in day_transactions if t.transaction_type == TransactionType.TRANSFER)

            # Calculate interest if applicable
            interest = 0.0
            if config.include_interest and config.interest_rate:
                interest = self._calculate_daily_interest(
                    current_balance,
                    config.interest_rate,
                    config.interest_type,
                    config.compounding
                )

            # Total daily change
            daily_change = income - expenses + transfers + interest

            # Closing balance
            closing = opening + daily_change

            # Generate confidence interval
            days_from_reference = abs((current_date - config.reference_date).days)
            confidence_bounds = self._generate_confidence_interval(
                closing,
                days_from_reference,
                variance,
                config.confidence_level
            ) if config.generate_confidence_intervals else (closing, closing, 0.0)

            # Create daily balance record
            daily_balance = DailyBalance(
                date=current_date,
                opening_balance=opening,
                closing_balance=closing,
                daily_change=daily_change,
                income=income,
                expenses=expenses,
                transfers=transfers,
                interest_earned=interest,
                transaction_count=len(day_transactions),
                transaction_ids=[t.transaction_id for t in day_transactions],
                point_estimate=closing,
                lower_bound=confidence_bounds[0],
                upper_bound=confidence_bounds[1],
                margin_of_error=confidence_bounds[2],
                confidence_level=config.confidence_level.value,
                is_payday=income > 0,
                is_large_expense=expenses > (config.large_expense_threshold or float('inf'))
            )

            daily_balances.append(daily_balance)

            # Advance to next day
            current_balance = closing
            current_date += timedelta(days=1)

        return daily_balances

    def _calculate_daily_interest(
        self,
        balance: float,
        annual_rate: float,
        interest_type: Optional[str],
        compounding: InterestCompounding
    ) -> float:
        """
        Calculate interest for a single day.

        Savings: (balance × APY / 365)
        Credit: (balance × APR / 365) - only if balance is positive

        Supports daily, monthly, quarterly, annual compounding.
        """
        if balance <= 0:
            return 0.0

        # Daily interest rate
        daily_rate = annual_rate / 365.0

        # For credit cards, only charge interest on carried balances
        if interest_type == "credit" and balance < 0:
            return abs(balance) * daily_rate

        # For savings accounts
        if interest_type == "savings":
            return balance * daily_rate

        return 0.0

    def _generate_confidence_interval(
        self,
        point_estimate: float,
        days_from_reference: int,
        variance: Optional[VarianceAnalysis],
        confidence_level: ConfidenceLevel
    ) -> Tuple[float, float, float]:
        """
        Generate confidence interval for projected balance.

        Factors:
        - Time decay (further out = less confident)
        - Historical variance
        - Confidence level (68%, 95%, 99.7%)

        Returns: (lower_bound, upper_bound, margin_of_error)
        """
        if not variance:
            return (point_estimate, point_estimate, 0.0)

        # Base margin of error from historical std deviation
        base_margin = variance.std_deviation

        # Time decay: margin increases with distance from reference
        # Use square root of time for decay (standard in finance)
        time_factor = (days_from_reference / 30.0) ** 0.5  # Normalize to months

        # Confidence level multiplier
        # 68% = 1 std dev, 95% = 2 std dev, 99.7% = 3 std dev
        z_score = {
            ConfidenceLevel.LOW: 1.0,
            ConfidenceLevel.MEDIUM: 2.0,
            ConfidenceLevel.HIGH: 3.0
        }.get(confidence_level, 2.0)

        # Calculate margin of error
        margin = base_margin * time_factor * z_score

        lower_bound = point_estimate - margin
        upper_bound = point_estimate + margin

        return (lower_bound, upper_bound, margin)

    def _identify_critical_dates(
        self,
        config: ForecastConfig,
        daily_balances: List[DailyBalance]
    ) -> List[CriticalDate]:
        """
        Identify critical dates in the forecast.

        Examples: low balance warnings, large expenses, payment due dates.
        """
        critical_dates = []

        for day_balance in daily_balances:
            # Low balance warning
            if config.low_balance_threshold and day_balance.closing_balance < config.low_balance_threshold:
                severity = "critical" if day_balance.closing_balance < 0 else "high"
                critical_dates.append(CriticalDate(
                    date=day_balance.date,
                    type="low_balance",
                    severity=severity,
                    projected_balance=day_balance.closing_balance,
                    threshold=config.low_balance_threshold,
                    description=f"Balance projected to be ${day_balance.closing_balance:.2f}",
                    recommended_action="Consider moving funds or adjusting spending"
                ))

            # Large expense
            if day_balance.is_large_expense:
                critical_dates.append(CriticalDate(
                    date=day_balance.date,
                    type="large_expense",
                    severity="medium",
                    projected_balance=day_balance.closing_balance,
                    threshold=config.large_expense_threshold,
                    description=f"Large expense: ${day_balance.expenses:.2f}",
                    recommended_action="Ensure sufficient funds available"
                ))

        return critical_dates

    def _calculate_summary_stats(self, daily_balances: List[DailyBalance]) -> Dict[str, Any]:
        """Calculate summary statistics for the forecast."""
        if not daily_balances:
            return {
                "total_income": 0.0,
                "total_expenses": 0.0,
                "total_interest": 0.0,
                "net_change": 0.0,
                "min_balance": 0.0,
                "min_balance_date": date.today(),
                "max_balance": 0.0,
                "max_balance_date": date.today(),
                "avg_balance": 0.0,
                "avg_confidence": 0.95
            }

        total_income = sum(d.income for d in daily_balances)
        total_expenses = sum(d.expenses for d in daily_balances)
        total_interest = sum(d.interest_earned for d in daily_balances)
        net_change = daily_balances[-1].closing_balance - daily_balances[0].opening_balance

        min_day = min(daily_balances, key=lambda d: d.closing_balance)
        max_day = max(daily_balances, key=lambda d: d.closing_balance)
        avg_balance = statistics.mean(d.closing_balance for d in daily_balances)
        avg_confidence = statistics.mean(d.confidence_level for d in daily_balances)

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "total_interest": total_interest,
            "net_change": net_change,
            "min_balance": min_day.closing_balance,
            "min_balance_date": min_day.date,
            "max_balance": max_day.closing_balance,
            "max_balance_date": max_day.date,
            "avg_balance": avg_balance,
            "avg_confidence": avg_confidence
        }

    def _get_historical_transactions(
        self,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> List[Transaction]:
        """Get actual historical transactions from database."""
        # Query transaction database
        # This would use the TransactionManagementAgent's database
        # For now, return empty list (placeholder)
        return []

    def _get_scheduled_transactions(
        self,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> List[Transaction]:
        """Get already-created scheduled transactions."""
        # Query for transactions with status="pending" in date range
        return []

    def _project_recurring_transactions(
        self,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> List[Transaction]:
        """Project transactions from recurring templates."""
        # Would call TransactionManagementAgent to calculate occurrences
        # For now, return empty list (placeholder)
        return []

    def _get_variance_analysis(self, account_id: str) -> Optional[VarianceAnalysis]:
        """Analyze historical variance for confidence intervals."""
        # Analyze historical transaction patterns
        # For now, return default variance (placeholder)
        return VarianceAnalysis(
            category="overall",
            mean=0.0,
            std_deviation=100.0,  # Default $100 std deviation
            variance=10000.0,
            coefficient_of_variation=0.0,
            sample_size=0,
            period_analyzed_days=0,
            reliability_score=0.5
        )

    def _store_forecast(self, result: ForecastResult):
        """Store forecast result to database."""
        with sqlite3.connect(self.forecast_db_path) as conn:
            cursor = conn.cursor()

            # Store forecast metadata
            cursor.execute("""
                INSERT INTO forecasts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.forecast_id,
                result.account_id,
                result.start_date.isoformat(),
                result.end_date.isoformat(),
                result.config.reference_date.isoformat(),
                result.config.reference_balance,
                json.dumps(result.config.dict()),
                result.calculated_at.isoformat(),
                result.calculation_time_ms
            ))

            # Store daily balances
            for daily in result.daily_balances:
                cursor.execute("""
                    INSERT INTO daily_balances VALUES (
                        NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    result.forecast_id,
                    daily.date.isoformat(),
                    daily.opening_balance,
                    daily.closing_balance,
                    daily.daily_change,
                    daily.income,
                    daily.expenses,
                    daily.transfers,
                    daily.interest_earned,
                    daily.transaction_count,
                    json.dumps(daily.transaction_ids),
                    daily.point_estimate,
                    daily.lower_bound,
                    daily.upper_bound,
                    daily.margin_of_error,
                    daily.confidence_level,
                    1 if daily.is_critical_date else 0,
                    1 if daily.is_large_expense else 0,
                    1 if daily.is_payday else 0,
                    json.dumps(daily.notes)
                ))

            # Store critical dates
            for critical in result.critical_dates:
                cursor.execute("""
                    INSERT INTO critical_dates VALUES (
                        NULL, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    result.forecast_id,
                    critical.date.isoformat(),
                    critical.type,
                    critical.severity,
                    critical.projected_balance,
                    critical.threshold,
                    critical.description,
                    critical.recommended_action
                ))

            conn.commit()

    def get_forecast(self, forecast_id: str) -> Dict[str, Any]:
        """Retrieve a forecast by ID."""
        # Implementation placeholder
        return {"success": True, "message": "Get forecast not yet implemented"}

    def get_daily_balances(self, forecast_id: str) -> Dict[str, Any]:
        """Get daily balance data for a forecast."""
        # Implementation placeholder
        return {"success": True, "message": "Get daily balances not yet implemented"}

    def get_critical_dates(self, forecast_id: str) -> Dict[str, Any]:
        """Get critical dates for a forecast."""
        # Implementation placeholder
        return {"success": True, "message": "Get critical dates not yet implemented"}

    def recalculate_forecast(self, forecast_id: str) -> Dict[str, Any]:
        """Recalculate an existing forecast with latest data."""
        # Implementation placeholder
        return {"success": True, "message": "Recalculate not yet implemented"}

    def analyze_variance(self, account_id: str, lookback_days: int = 180) -> Dict[str, Any]:
        """Analyze historical variance for confidence intervals."""
        # Implementation placeholder
        return {"success": True, "message": "Variance analysis not yet implemented"}

    async def _handle_transaction_event(self, event):
        """Handle transaction-related events."""
        logger.info(f"Received transaction event: {event.event_type}")
        # Could trigger forecast recalculation
        # Implementation depends on caching strategy

    async def _cleanup(self) -> None:
        """Cleanup agent resources."""
        self.message_bus.unsubscribe(self.config.agent_id)
        logger.info("CashFlowForecastingAgent cleaned up")
