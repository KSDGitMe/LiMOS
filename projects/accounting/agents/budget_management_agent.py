"""
Budget Management Agent

Tracks budgets, monitors spending in real-time, generates alerts when thresholds
are exceeded, and provides variance analysis and spending projections.

Key Features:
- Real-time spending tracking against category budgets
- Automatic alert generation at configurable thresholds (80%, 90%, 100%)
- Variance analysis comparing actual vs budgeted spending
- Spending projections to predict budget overruns
- Budget template support for recurring budgets
- Event-driven integration with Transaction Management Agent
"""

import sqlite3
import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.agents.base import BaseAgent, AgentConfig
from core.agents.coordination.message_bus import MessageBus, Event, EventPriority
from projects.accounting.models.budgets import (
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
from projects.accounting.models.transactions import Transaction, TransactionType


class BudgetManagementAgent(BaseAgent):
    """
    Budget Management Agent

    Responsibilities:
    - Create and manage budgets with category allocations
    - Track spending in real-time against budgets
    - Generate alerts when budget thresholds are exceeded
    - Provide variance analysis (actual vs budgeted)
    - Project end-of-period spending
    - Support budget templates for recurring budgets
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.db_path = Path("data/accounting.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.message_bus: Optional[MessageBus] = None

    async def _initialize(self) -> None:
        """Initialize database schema and message bus subscriptions."""
        await super()._initialize()
        self._setup_database()
        await self._setup_event_subscriptions()

    def _setup_database(self):
        """Create database tables for budgets."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                budget_id TEXT PRIMARY KEY,
                budget_name TEXT NOT NULL,
                budget_type TEXT NOT NULL,
                account_ids TEXT,  -- JSON array
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                current_period TEXT NOT NULL,
                total_allocated REAL NOT NULL,
                total_spent REAL DEFAULT 0.0,
                total_remaining REAL DEFAULT 0.0,
                percent_used REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                is_exceeded INTEGER DEFAULT 0,
                auto_create_next_period INTEGER DEFAULT 1,
                rollover_unused INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by TEXT,
                notes TEXT,
                tags TEXT  -- JSON array
            )
        """)

        # Category budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_budgets (
                category_budget_id TEXT PRIMARY KEY,
                budget_id TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                allocated_amount REAL NOT NULL,
                spent_amount REAL DEFAULT 0.0,
                remaining_amount REAL DEFAULT 0.0,
                percent_used REAL DEFAULT 0.0,
                allow_rollover INTEGER DEFAULT 0,
                rollover_from_previous REAL DEFAULT 0.0,
                alert_thresholds TEXT,  -- JSON array
                alerts_triggered TEXT,  -- JSON array
                notes TEXT,
                tags TEXT,  -- JSON array
                FOREIGN KEY (budget_id) REFERENCES budgets(budget_id)
            )
        """)

        # Budget alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget_alerts (
                alert_id TEXT PRIMARY KEY,
                budget_id TEXT NOT NULL,
                category_budget_id TEXT,
                alert_level TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                allocated_amount REAL NOT NULL,
                spent_amount REAL NOT NULL,
                percent_used REAL NOT NULL,
                threshold REAL NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                recommended_action TEXT,
                triggered_at TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_at TEXT,
                FOREIGN KEY (budget_id) REFERENCES budgets(budget_id)
            )
        """)

        # Budget templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget_templates (
                template_id TEXT PRIMARY KEY,
                template_name TEXT NOT NULL,
                budget_type TEXT NOT NULL,
                category_allocations TEXT NOT NULL,  -- JSON
                use_percentages INTEGER DEFAULT 1,
                auto_create_for_period INTEGER DEFAULT 1,
                rollover_unused INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                notes TEXT
            )
        """)

        # Variance reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS variance_reports (
                report_id TEXT PRIMARY KEY,
                budget_id TEXT NOT NULL,
                report_period TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                total_budgeted REAL NOT NULL,
                total_actual REAL NOT NULL,
                total_variance REAL NOT NULL,
                variance_percentage REAL NOT NULL,
                category_variances TEXT,  -- JSON
                categories_over_budget INTEGER DEFAULT 0,
                categories_under_budget INTEGER DEFAULT 0,
                largest_overrun_category TEXT,
                largest_overrun_amount REAL DEFAULT 0.0,
                largest_underrun_category TEXT,
                largest_underrun_amount REAL DEFAULT 0.0,
                spending_trend TEXT DEFAULT 'stable',
                forecast_end_of_period REAL DEFAULT 0.0,
                recommendations TEXT,  -- JSON
                FOREIGN KEY (budget_id) REFERENCES budgets(budget_id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets(current_period)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_status ON budgets(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category_budgets_budget ON category_budgets(budget_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_budget ON budget_alerts(budget_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON budget_alerts(acknowledged)")

        conn.commit()
        conn.close()

    async def _setup_event_subscriptions(self):
        """Subscribe to transaction events to update budgets in real-time."""
        # Get message bus from agent registry
        from core.agents.coordination.message_bus import get_default_message_bus
        self.message_bus = get_default_message_bus()

        # Subscribe to transaction events
        self.message_bus.subscribe(
            agent_id=self.agent_id,
            event_types=["transaction.created", "transaction.updated", "transaction.deleted"],
            callback=self._handle_transaction_event
        )

    async def _handle_transaction_event(self, event: Event):
        """
        Handle transaction events to update budget spending in real-time.

        When a transaction is created, find matching budgets and update spending.
        """
        try:
            transaction_data = event.payload.get("transaction", {})

            # Convert to Transaction object for processing
            transaction = Transaction(**transaction_data)

            # Only process expense transactions
            if transaction.transaction_type != TransactionType.EXPENSE:
                return

            # Find active budgets that apply to this transaction
            active_budgets = self._find_applicable_budgets(
                account_id=transaction.account_id,
                transaction_date=transaction.date,
                category=transaction.category
            )

            # Update spending for each applicable budget
            for budget in active_budgets:
                await self._update_budget_spending(
                    budget=budget,
                    category=transaction.category,
                    subcategory=transaction.subcategory,
                    amount=transaction.amount
                )

        except Exception as e:
            self.logger.error(f"Error handling transaction event: {e}")

    def _find_applicable_budgets(
        self,
        account_id: str,
        transaction_date: date,
        category: str
    ) -> List[Budget]:
        """Find active budgets that apply to a transaction."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM budgets
            WHERE status = 'active'
            AND start_date <= ?
            AND end_date >= ?
        """, (transaction_date.isoformat(), transaction_date.isoformat()))

        budgets = []
        for row in cursor.fetchall():
            # Check if budget applies to this account
            account_ids = json.loads(row[3]) if row[3] else []
            if account_ids and account_id not in account_ids:
                continue

            # Load budget with categories
            budget = self._load_budget_from_row(row)

            # Check if budget has this category
            if budget.get_category_budget(category):
                budgets.append(budget)

        conn.close()
        return budgets

    async def _update_budget_spending(
        self,
        budget: Budget,
        category: str,
        subcategory: Optional[str],
        amount: float
    ):
        """Update budget spending and generate alerts if thresholds exceeded."""
        import json

        # Update budget model
        budget.update_spending(category, amount, subcategory)
        budget.updated_at = datetime.utcnow()

        # Get category budget to check for new alerts
        cat_budget = budget.get_category_budget(category, subcategory)
        if not cat_budget:
            return

        # Check for new alerts
        new_alerts = self._check_for_alerts(budget, cat_budget)

        # Persist budget updates
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update budget totals
        cursor.execute("""
            UPDATE budgets
            SET total_spent = ?,
                total_remaining = ?,
                percent_used = ?,
                is_exceeded = ?,
                status = ?,
                updated_at = ?
            WHERE budget_id = ?
        """, (
            budget.total_spent,
            budget.total_remaining,
            budget.percent_used,
            1 if budget.is_exceeded else 0,
            budget.status.value,
            budget.updated_at.isoformat(),
            budget.budget_id
        ))

        # Update category budget
        cursor.execute("""
            UPDATE category_budgets
            SET spent_amount = ?,
                remaining_amount = ?,
                percent_used = ?,
                alerts_triggered = ?
            WHERE category_budget_id = ?
        """, (
            cat_budget.spent_amount,
            cat_budget.remaining_amount,
            cat_budget.percent_used,
            json.dumps(cat_budget.alerts_triggered),
            cat_budget.category_budget_id
        ))

        conn.commit()
        conn.close()

        # Persist and publish alerts
        for alert in new_alerts:
            self._save_alert(alert)
            await self._publish_alert(alert)

        # Publish budget updated event
        if self.message_bus:
            await self.message_bus.publish(
                event_type="budget.updated",
                payload={
                    "budget_id": budget.budget_id,
                    "category": category,
                    "subcategory": subcategory,
                    "amount": amount,
                    "total_spent": budget.total_spent,
                    "percent_used": budget.percent_used,
                    "is_exceeded": budget.is_exceeded
                },
                source_agent=self.agent_id
            )

    def _check_for_alerts(self, budget: Budget, cat_budget: CategoryBudget) -> List[BudgetAlert]:
        """Check if any new alert thresholds have been reached."""
        new_alerts = []

        for threshold in cat_budget.alert_thresholds:
            if cat_budget.percent_used >= threshold:
                alert_key = self._get_alert_key(threshold)

                # Only create alert if not already triggered
                if alert_key not in cat_budget.alerts_triggered:
                    alert = self._create_alert(budget, cat_budget, threshold)
                    new_alerts.append(alert)

        return new_alerts

    def _get_alert_key(self, threshold: float) -> str:
        """Get alert key from threshold."""
        if threshold >= 1.0:
            return "exceeded_100"
        elif threshold >= 0.9:
            return "critical_90"
        elif threshold >= 0.8:
            return "warning_80"
        else:
            return f"threshold_{int(threshold * 100)}"

    def _create_alert(
        self,
        budget: Budget,
        cat_budget: CategoryBudget,
        threshold: float
    ) -> BudgetAlert:
        """Create a budget alert."""
        # Determine alert level
        if threshold >= 1.0:
            alert_level = AlertLevel.EXCEEDED
            alert_type = "exceeded"
            title = f"Budget Exceeded: {cat_budget.category}"
            message = f"You've exceeded your budget for {cat_budget.category} by ${cat_budget.spent_amount - cat_budget.allocated_amount:.2f}"
            action = f"Review spending in {cat_budget.category} and consider adjusting budget or reducing expenses"
        elif threshold >= 0.9:
            alert_level = AlertLevel.CRITICAL
            alert_type = "threshold_reached"
            title = f"Budget Critical: {cat_budget.category}"
            message = f"You've used {cat_budget.percent_used*100:.0f}% of your {cat_budget.category} budget (${cat_budget.spent_amount:.2f} of ${cat_budget.allocated_amount:.2f})"
            action = f"Only ${cat_budget.remaining_amount:.2f} remaining in {cat_budget.category}"
        else:
            alert_level = AlertLevel.WARNING
            alert_type = "threshold_reached"
            title = f"Budget Warning: {cat_budget.category}"
            message = f"You've used {cat_budget.percent_used*100:.0f}% of your {cat_budget.category} budget"
            action = f"Monitor spending to stay within budget"

        return BudgetAlert(
            budget_id=budget.budget_id,
            category_budget_id=cat_budget.category_budget_id,
            alert_level=alert_level,
            alert_type=alert_type,
            category=cat_budget.category,
            subcategory=cat_budget.subcategory,
            allocated_amount=cat_budget.allocated_amount,
            spent_amount=cat_budget.spent_amount,
            percent_used=cat_budget.percent_used,
            threshold=threshold,
            title=title,
            message=message,
            recommended_action=action
        )

    def _save_alert(self, alert: BudgetAlert):
        """Save alert to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO budget_alerts (
                alert_id, budget_id, category_budget_id, alert_level, alert_type,
                category, subcategory, allocated_amount, spent_amount, percent_used,
                threshold, title, message, recommended_action, triggered_at,
                acknowledged, acknowledged_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.alert_id,
            alert.budget_id,
            alert.category_budget_id,
            alert.alert_level.value,
            alert.alert_type,
            alert.category,
            alert.subcategory,
            alert.allocated_amount,
            alert.spent_amount,
            alert.percent_used,
            alert.threshold,
            alert.title,
            alert.message,
            alert.recommended_action,
            alert.triggered_at.isoformat(),
            1 if alert.acknowledged else 0,
            alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        ))

        conn.commit()
        conn.close()

    async def _publish_alert(self, alert: BudgetAlert):
        """Publish alert event."""
        if self.message_bus:
            await self.message_bus.publish(
                event_type=f"budget.alert.{alert.alert_level.value}",
                payload={
                    "alert_id": alert.alert_id,
                    "budget_id": alert.budget_id,
                    "category": alert.category,
                    "title": alert.title,
                    "message": alert.message,
                    "recommended_action": alert.recommended_action,
                    "percent_used": alert.percent_used
                },
                source_agent=self.agent_id,
                priority=EventPriority.HIGH if alert.alert_level == AlertLevel.EXCEEDED else EventPriority.NORMAL
            )

    async def _execute(self, task: Dict) -> Dict:
        """Execute budget management operations."""
        operation = task.get("operation")
        parameters = task.get("parameters", {})

        operations = {
            "create_budget": self.create_budget,
            "get_budget": self.get_budget,
            "list_budgets": self.list_budgets,
            "update_budget": self.update_budget,
            "delete_budget": self.delete_budget,
            "get_alerts": self.get_alerts,
            "acknowledge_alert": self.acknowledge_alert,
            "generate_variance_report": self.generate_variance_report,
            "project_spending": self.project_spending,
            "create_template": self.create_template,
            "create_from_template": self.create_from_template
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

    async def create_budget(self, budget_data: Dict) -> Dict:
        """
        Create a new budget.

        Args:
            budget_data: Budget configuration including:
                - budget_name: Name of budget
                - budget_type: Type (monthly, annual, etc.)
                - start_date: Start date
                - end_date: End date
                - categories: List of category allocations

        Returns:
            Created budget with ID
        """
        import json

        # Create budget model
        budget = Budget(**budget_data)

        # Calculate total allocated from categories
        budget.total_allocated = sum(cat.allocated_amount for cat in budget.categories)
        budget.total_remaining = budget.total_allocated

        # Persist to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert budget
        cursor.execute("""
            INSERT INTO budgets (
                budget_id, budget_name, budget_type, account_ids,
                start_date, end_date, current_period,
                total_allocated, total_spent, total_remaining, percent_used,
                status, is_exceeded, auto_create_next_period, rollover_unused,
                created_at, updated_at, created_by, notes, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            budget.budget_id,
            budget.budget_name,
            budget.budget_type.value,
            json.dumps(budget.account_ids),
            budget.start_date.isoformat(),
            budget.end_date.isoformat(),
            budget.current_period,
            budget.total_allocated,
            budget.total_spent,
            budget.total_remaining,
            budget.percent_used,
            budget.status.value,
            1 if budget.is_exceeded else 0,
            1 if budget.auto_create_next_period else 0,
            1 if budget.rollover_unused else 0,
            budget.created_at.isoformat(),
            budget.updated_at.isoformat(),
            budget.created_by,
            budget.notes,
            json.dumps(budget.tags)
        ))

        # Insert category budgets
        for cat in budget.categories:
            cursor.execute("""
                INSERT INTO category_budgets (
                    category_budget_id, budget_id, category, subcategory,
                    allocated_amount, spent_amount, remaining_amount, percent_used,
                    allow_rollover, rollover_from_previous,
                    alert_thresholds, alerts_triggered, notes, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cat.category_budget_id,
                budget.budget_id,
                cat.category,
                cat.subcategory,
                cat.allocated_amount,
                cat.spent_amount,
                cat.remaining_amount,
                cat.percent_used,
                1 if cat.allow_rollover else 0,
                cat.rollover_from_previous,
                json.dumps(cat.alert_thresholds),
                json.dumps(cat.alerts_triggered),
                cat.notes,
                json.dumps(cat.tags)
            ))

        conn.commit()
        conn.close()

        # Publish event
        if self.message_bus:
            await self.message_bus.publish(
                event_type="budget.created",
                payload={"budget": budget.dict()},
                source_agent=self.agent_id
            )

        return budget.dict()

    async def get_budget(self, budget_id: str) -> Optional[Dict]:
        """Get budget by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM budgets WHERE budget_id = ?", (budget_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        budget = self._load_budget_from_row(row)
        conn.close()

        return budget.dict()

    def _load_budget_from_row(self, row) -> Budget:
        """Load Budget object from database row."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Load category budgets
        cursor.execute(
            "SELECT * FROM category_budgets WHERE budget_id = ?",
            (row[0],)
        )

        categories = []
        for cat_row in cursor.fetchall():
            categories.append(CategoryBudget(
                category_budget_id=cat_row[0],
                category=cat_row[2],
                subcategory=cat_row[3],
                allocated_amount=cat_row[4],
                spent_amount=cat_row[5],
                remaining_amount=cat_row[6],
                percent_used=cat_row[7],
                allow_rollover=bool(cat_row[8]),
                rollover_from_previous=cat_row[9],
                alert_thresholds=json.loads(cat_row[10]),
                alerts_triggered=json.loads(cat_row[11]),
                notes=cat_row[12],
                tags=json.loads(cat_row[13]) if cat_row[13] else []
            ))

        conn.close()

        return Budget(
            budget_id=row[0],
            budget_name=row[1],
            budget_type=BudgetType(row[2]),
            account_ids=json.loads(row[3]) if row[3] else [],
            start_date=date.fromisoformat(row[4]),
            end_date=date.fromisoformat(row[5]),
            current_period=row[6],
            total_allocated=row[7],
            total_spent=row[8],
            total_remaining=row[9],
            percent_used=row[10],
            status=BudgetStatus(row[11]),
            is_exceeded=bool(row[12]),
            auto_create_next_period=bool(row[13]),
            rollover_unused=bool(row[14]),
            created_at=datetime.fromisoformat(row[15]),
            updated_at=datetime.fromisoformat(row[16]),
            created_by=row[17],
            notes=row[18],
            tags=json.loads(row[19]) if row[19] else [],
            categories=categories
        )

    async def list_budgets(
        self,
        status: Optional[str] = None,
        budget_type: Optional[str] = None,
        current_period: Optional[str] = None
    ) -> List[Dict]:
        """List budgets with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM budgets WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if budget_type:
            query += " AND budget_type = ?"
            params.append(budget_type)

        if current_period:
            query += " AND current_period = ?"
            params.append(current_period)

        cursor.execute(query, params)

        budgets = []
        for row in cursor.fetchall():
            budget = self._load_budget_from_row(row)
            budgets.append(budget.dict())

        conn.close()
        return budgets

    async def update_budget(self, budget_id: str, updates: Dict) -> Dict:
        """Update budget (placeholder for future implementation)."""
        # TODO: Implement budget updates
        return {"status": "not_implemented"}

    async def delete_budget(self, budget_id: str) -> Dict:
        """Delete budget (placeholder for future implementation)."""
        # TODO: Implement budget deletion
        return {"status": "not_implemented"}

    async def get_alerts(
        self,
        budget_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        alert_level: Optional[str] = None
    ) -> List[Dict]:
        """Get budget alerts with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM budget_alerts WHERE 1=1"
        params = []

        if budget_id:
            query += " AND budget_id = ?"
            params.append(budget_id)

        if acknowledged is not None:
            query += " AND acknowledged = ?"
            params.append(1 if acknowledged else 0)

        if alert_level:
            query += " AND alert_level = ?"
            params.append(alert_level)

        query += " ORDER BY triggered_at DESC"

        cursor.execute(query, params)

        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                "alert_id": row[0],
                "budget_id": row[1],
                "category_budget_id": row[2],
                "alert_level": row[3],
                "alert_type": row[4],
                "category": row[5],
                "subcategory": row[6],
                "allocated_amount": row[7],
                "spent_amount": row[8],
                "percent_used": row[9],
                "threshold": row[10],
                "title": row[11],
                "message": row[12],
                "recommended_action": row[13],
                "triggered_at": row[14],
                "acknowledged": bool(row[15]),
                "acknowledged_at": row[16]
            })

        conn.close()
        return alerts

    async def acknowledge_alert(self, alert_id: str) -> Dict:
        """Acknowledge a budget alert."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE budget_alerts
            SET acknowledged = 1,
                acknowledged_at = ?
            WHERE alert_id = ?
        """, (datetime.utcnow().isoformat(), alert_id))

        conn.commit()
        conn.close()

        return {"alert_id": alert_id, "acknowledged": True}

    async def generate_variance_report(self, budget_id: str) -> Dict:
        """Generate variance analysis report comparing actual vs budgeted spending."""
        budget_dict = await self.get_budget(budget_id)
        if not budget_dict:
            return {"error": "Budget not found"}

        budget = Budget(**budget_dict)

        # Calculate category variances
        category_variances = []
        categories_over = 0
        categories_under = 0
        largest_overrun_cat = None
        largest_overrun_amt = 0.0
        largest_underrun_cat = None
        largest_underrun_amt = 0.0

        for cat in budget.categories:
            variance = cat.spent_amount - cat.allocated_amount
            variance_pct = (variance / cat.allocated_amount * 100) if cat.allocated_amount > 0 else 0

            category_variances.append({
                "category": cat.category,
                "subcategory": cat.subcategory,
                "budgeted": cat.allocated_amount,
                "actual": cat.spent_amount,
                "variance": variance,
                "variance_percentage": variance_pct,
                "status": "over" if variance > 0 else "under" if variance < 0 else "on_target"
            })

            if variance > 0:
                categories_over += 1
                if variance > largest_overrun_amt:
                    largest_overrun_amt = variance
                    largest_overrun_cat = cat.category
            elif variance < 0:
                categories_under += 1
                if abs(variance) > largest_underrun_amt:
                    largest_underrun_amt = abs(variance)
                    largest_underrun_cat = cat.category

        # Generate recommendations
        recommendations = []
        if categories_over > 0:
            recommendations.append(f"{categories_over} categories are over budget")
        if largest_overrun_cat:
            recommendations.append(f"Largest overrun: {largest_overrun_cat} by ${largest_overrun_amt:.2f}")
        if budget.is_exceeded:
            recommendations.append("Total budget exceeded - consider adjusting allocations")

        # Create report
        report = VarianceReport(
            budget_id=budget_id,
            report_period=budget.current_period,
            total_budgeted=budget.total_allocated,
            total_actual=budget.total_spent,
            total_variance=budget.total_spent - budget.total_allocated,
            variance_percentage=((budget.total_spent - budget.total_allocated) / budget.total_allocated * 100) if budget.total_allocated > 0 else 0,
            category_variances=category_variances,
            categories_over_budget=categories_over,
            categories_under_budget=categories_under,
            largest_overrun_category=largest_overrun_cat,
            largest_overrun_amount=largest_overrun_amt,
            largest_underrun_category=largest_underrun_cat,
            largest_underrun_amount=largest_underrun_amt,
            recommendations=recommendations
        )

        # Save report
        self._save_variance_report(report)

        return report.dict()

    def _save_variance_report(self, report: VarianceReport):
        """Save variance report to database."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO variance_reports (
                report_id, budget_id, report_period, generated_at,
                total_budgeted, total_actual, total_variance, variance_percentage,
                category_variances, categories_over_budget, categories_under_budget,
                largest_overrun_category, largest_overrun_amount,
                largest_underrun_category, largest_underrun_amount,
                spending_trend, forecast_end_of_period, recommendations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.report_id,
            report.budget_id,
            report.report_period,
            report.generated_at.isoformat(),
            report.total_budgeted,
            report.total_actual,
            report.total_variance,
            report.variance_percentage,
            json.dumps(report.category_variances),
            report.categories_over_budget,
            report.categories_under_budget,
            report.largest_overrun_category,
            report.largest_overrun_amount,
            report.largest_underrun_category,
            report.largest_underrun_amount,
            report.spending_trend,
            report.forecast_end_of_period,
            json.dumps(report.recommendations)
        ))

        conn.commit()
        conn.close()

    async def project_spending(
        self,
        budget_id: str,
        category: str,
        subcategory: Optional[str] = None
    ) -> Dict:
        """Project end-of-period spending for a budget category."""
        budget_dict = await self.get_budget(budget_id)
        if not budget_dict:
            return {"error": "Budget not found"}

        budget = Budget(**budget_dict)
        cat_budget = budget.get_category_budget(category, subcategory)

        if not cat_budget:
            return {"error": f"Category {category} not found in budget"}

        # Calculate days elapsed and remaining
        today = date.today()
        days_elapsed = (today - budget.start_date).days
        total_days = (budget.end_date - budget.start_date).days
        days_remaining = (budget.end_date - today).days

        if total_days <= 0:
            return {"error": "Invalid budget period"}

        percent_complete = days_elapsed / total_days

        # Project total spending using linear projection
        if days_elapsed > 0:
            daily_rate = cat_budget.spent_amount / days_elapsed
            projected_total = cat_budget.spent_amount + (daily_rate * days_remaining)
        else:
            projected_total = cat_budget.spent_amount

        projected_variance = projected_total - cat_budget.allocated_amount
        projected_percent_used = (projected_total / cat_budget.allocated_amount) if cat_budget.allocated_amount > 0 else 0

        will_exceed = projected_total > cat_budget.allocated_amount

        # Calculate days until exceeded
        days_until_exceeded = None
        if will_exceed and days_elapsed > 0:
            daily_rate = cat_budget.spent_amount / days_elapsed
            remaining_budget = cat_budget.allocated_amount - cat_budget.spent_amount
            if daily_rate > 0:
                days_until_exceeded = int(remaining_budget / daily_rate)

        projection = SpendingProjection(
            budget_id=budget_id,
            category=category,
            subcategory=subcategory,
            days_elapsed=days_elapsed,
            days_remaining=days_remaining,
            percent_period_complete=percent_complete,
            allocated_amount=cat_budget.allocated_amount,
            spent_to_date=cat_budget.spent_amount,
            percent_used=cat_budget.percent_used,
            projected_total_spending=projected_total,
            projected_variance=projected_variance,
            projected_percent_used=projected_percent_used,
            confidence_level=0.7,  # Linear projection has moderate confidence
            projection_method="linear",
            will_exceed_budget=will_exceed,
            days_until_exceeded=days_until_exceeded
        )

        return projection.dict()

    async def create_template(self, template_data: Dict) -> Dict:
        """Create budget template for recurring budgets."""
        import json

        template = BudgetTemplate(**template_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO budget_templates (
                template_id, template_name, budget_type,
                category_allocations, use_percentages,
                auto_create_for_period, rollover_unused,
                created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            template.template_id,
            template.template_name,
            template.budget_type.value,
            json.dumps(template.category_allocations),
            1 if template.use_percentages else 0,
            1 if template.auto_create_for_period else 0,
            1 if template.rollover_unused else 0,
            template.created_at.isoformat(),
            template.updated_at.isoformat(),
            template.notes
        ))

        conn.commit()
        conn.close()

        return template.dict()

    async def create_from_template(
        self,
        template_id: str,
        total_amount: float,
        start_date: str,
        end_date: str,
        period: str
    ) -> Dict:
        """Create budget from template."""
        import json

        # Load template
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM budget_templates WHERE template_id = ?",
            (template_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"error": "Template not found"}

        category_allocations = json.loads(row[3])
        use_percentages = bool(row[4])

        # Create category budgets from template
        categories = []
        for category, value in category_allocations.items():
            if use_percentages:
                allocated = total_amount * (value / 100.0)
            else:
                allocated = value

            categories.append({
                "category": category,
                "allocated_amount": allocated
            })

        # Create budget
        budget_data = {
            "budget_name": f"{row[1]} - {period}",
            "budget_type": row[2],
            "start_date": start_date,
            "end_date": end_date,
            "current_period": period,
            "categories": categories,
            "rollover_unused": bool(row[6])
        }

        return await self.create_budget(budget_data)
