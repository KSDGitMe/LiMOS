"""
Transaction Management Agent

Handles all transaction operations including CRUD, recurring transactions,
categorization, and pattern detection.
"""

import asyncio
import logging
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from calendar import monthrange
import json

from core.agents.base import BaseAgent, AgentConfig, AgentCapability
from core.agents.coordination import get_message_bus, MessageBus, EventPriority
from ..models.transactions import (
    Transaction,
    RecurringTransaction,
    RecurrenceRule,
    RecurrenceFrequency,
    TransactionType,
    TransactionStatus
)

logger = logging.getLogger(__name__)


class TransactionManagementAgent(BaseAgent):
    """
    Transaction Management Agent.

    Responsibilities:
    - Transaction CRUD operations
    - Recurring transaction management with array-based recurrence rules
    - Transaction search and categorization
    - Automatic pattern detection
    - Event publishing for transaction changes
    """

    def __init__(self, config: Optional[AgentConfig] = None, message_bus: Optional[MessageBus] = None):
        """Initialize Transaction Management Agent."""
        if config is None:
            config = AgentConfig(
                name="TransactionManagementAgent",
                description="Manages financial transactions and recurring transaction templates",
                capabilities=[
                    AgentCapability.DATABASE_OPERATIONS,
                    AgentCapability.DATA_EXTRACTION
                ]
            )
        super().__init__(config)
        self.message_bus = message_bus or get_message_bus()
        self.db_path = Path("storage/accounting/transactions.db")
        logger.info(f"TransactionManagementAgent '{self.name}' initialized")

    async def _initialize(self) -> None:
        """Initialize database and subscribe to events."""
        # Create database
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        # Subscribe to relevant events
        self.message_bus.subscribe(
            agent_id=self.config.agent_id,
            event_types=["receipt.processed"],
            callback=self._handle_receipt_processed
        )

        logger.info("TransactionManagementAgent initialized and subscribed to events")

    def _init_database(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    merchant TEXT NOT NULL,
                    amount REAL NOT NULL,
                    transaction_type TEXT NOT NULL,
                    category TEXT,
                    subcategory TEXT,
                    payment_method TEXT,
                    status TEXT DEFAULT 'pending',
                    notes TEXT,
                    tags TEXT,
                    recurring_transaction_id TEXT,
                    parent_transaction_id TEXT,
                    bank_transaction_id TEXT,
                    reconciled_date TEXT,
                    receipt_id TEXT,
                    attachment_urls TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT
                )
            """)

            # Recurring transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recurring_transactions (
                    recurring_transaction_id TEXT PRIMARY KEY,
                    template_name TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    merchant TEXT NOT NULL,
                    base_amount REAL NOT NULL,
                    amount_variance REAL,
                    transaction_type TEXT NOT NULL,
                    category TEXT,
                    subcategory TEXT,
                    payment_method TEXT,
                    recurrence_rule TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    end_after_occurrences INTEGER,
                    auto_create INTEGER DEFAULT 1,
                    create_days_before INTEGER DEFAULT 0,
                    require_confirmation INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    last_generated_date TEXT,
                    total_generated INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    notes TEXT,
                    tags TEXT
                )
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recurring_active ON recurring_transactions(is_active)")

            conn.commit()
            logger.info("Database initialized successfully")

    async def _execute(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute transaction operations."""
        operation = input_data.get("operation")
        if not operation:
            return {"success": False, "error": "No operation specified"}

        operations = {
            "create_transaction": self.create_transaction,
            "update_transaction": self.update_transaction,
            "delete_transaction": self.delete_transaction,
            "get_transaction": self.get_transaction,
            "search_transactions": self.search_transactions,
            "create_recurring": self.create_recurring_transaction,
            "update_recurring": self.update_recurring_transaction,
            "delete_recurring": self.delete_recurring_transaction,
            "get_recurring": self.get_recurring_transaction,
            "list_recurring": self.list_recurring_transactions,
            "calculate_next_occurrences": self.calculate_next_occurrences,
            "generate_scheduled": self.generate_scheduled_transactions,
            "detect_patterns": self.detect_recurring_patterns
        }

        method = operations.get(operation)
        if not method:
            return {"success": False, "error": f"Unknown operation: {operation}"}

        params = input_data.get("parameters", {})
        return method(**params)

    def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new transaction."""
        try:
            transaction = Transaction(**transaction_data)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    transaction.transaction_id,
                    transaction.account_id,
                    transaction.date.isoformat(),
                    transaction.merchant,
                    transaction.amount,
                    transaction.transaction_type.value,
                    transaction.category,
                    transaction.subcategory,
                    transaction.payment_method,
                    transaction.status.value,
                    transaction.notes,
                    json.dumps(transaction.tags),
                    transaction.recurring_transaction_id,
                    transaction.parent_transaction_id,
                    transaction.bank_transaction_id,
                    transaction.reconciled_date.isoformat() if transaction.reconciled_date else None,
                    transaction.receipt_id,
                    json.dumps(transaction.attachment_urls),
                    transaction.created_at.isoformat(),
                    transaction.updated_at.isoformat(),
                    transaction.created_by
                ))
                conn.commit()

            # Publish event
            asyncio.create_task(self.message_bus.publish(
                event_type="transaction.created",
                payload=transaction.dict(),
                source_agent=self.config.agent_id,
                priority=EventPriority.NORMAL
            ))

            logger.info(f"Transaction created: {transaction.transaction_id}")
            return {
                "success": True,
                "transaction_id": transaction.transaction_id,
                "transaction": transaction.dict()
            }

        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return {"success": False, "error": str(e)}

    def create_recurring_transaction(self, recurring_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new recurring transaction template."""
        try:
            recurring = RecurringTransaction(**recurring_data)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO recurring_transactions VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    recurring.recurring_transaction_id,
                    recurring.template_name,
                    recurring.account_id,
                    recurring.merchant,
                    recurring.base_amount,
                    recurring.amount_variance,
                    recurring.transaction_type.value,
                    recurring.category,
                    recurring.subcategory,
                    recurring.payment_method,
                    json.dumps(recurring.recurrence_rule.dict()),
                    recurring.start_date.isoformat(),
                    recurring.end_date.isoformat() if recurring.end_date else None,
                    recurring.end_after_occurrences,
                    1 if recurring.auto_create else 0,
                    recurring.create_days_before,
                    1 if recurring.require_confirmation else 0,
                    1 if recurring.is_active else 0,
                    recurring.last_generated_date.isoformat() if recurring.last_generated_date else None,
                    recurring.total_generated,
                    recurring.created_at.isoformat(),
                    recurring.updated_at.isoformat(),
                    recurring.notes,
                    json.dumps(recurring.tags)
                ))
                conn.commit()

            # Publish event
            asyncio.create_task(self.message_bus.publish(
                event_type="recurring_transaction.created",
                payload=recurring.dict(),
                source_agent=self.config.agent_id,
                priority=EventPriority.NORMAL
            ))

            logger.info(f"Recurring transaction created: {recurring.recurring_transaction_id}")
            return {
                "success": True,
                "recurring_transaction_id": recurring.recurring_transaction_id,
                "recurring_transaction": recurring.dict()
            }

        except Exception as e:
            logger.error(f"Error creating recurring transaction: {e}")
            return {"success": False, "error": str(e)}

    def calculate_next_occurrences(
        self,
        recurring_transaction_id: str,
        count: int = 10,
        from_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate the next N occurrence dates for a recurring transaction.

        This is the CORE algorithm for generating scheduled transaction dates.
        """
        try:
            # Get recurring transaction
            result = self.get_recurring_transaction(recurring_transaction_id)
            if not result["success"]:
                return result

            recurring = RecurringTransaction(**result["recurring_transaction"])
            rule = recurring.recurrence_rule

            start = date.fromisoformat(from_date) if from_date else date.today()
            if start < recurring.start_date:
                start = recurring.start_date

            occurrences = []
            current_date = start

            # Maximum iterations to prevent infinite loops
            max_iterations = 1000
            iterations = 0

            while len(occurrences) < count and iterations < max_iterations:
                iterations += 1

                # Check end conditions
                if recurring.end_date and current_date > recurring.end_date:
                    break
                if recurring.end_after_occurrences and recurring.total_generated + len(occurrences) >= recurring.end_after_occurrences:
                    break

                # Check if current_date matches the recurrence rule
                if self._date_matches_rule(current_date, rule, recurring.start_date):
                    occurrences.append(current_date.isoformat())

                # Advance to next potential date based on frequency
                current_date = self._advance_date(current_date, rule)

            logger.info(f"Calculated {len(occurrences)} occurrences for {recurring_transaction_id}")
            return {
                "success": True,
                "recurring_transaction_id": recurring_transaction_id,
                "occurrences": occurrences,
                "count": len(occurrences)
            }

        except Exception as e:
            logger.error(f"Error calculating occurrences: {e}")
            return {"success": False, "error": str(e)}

    def _date_matches_rule(self, check_date: date, rule: RecurrenceRule, start_date: date) -> bool:
        """Check if a date matches the recurrence rule."""
        # Check month of year (if specified)
        if rule.month_of_year and check_date.month not in rule.month_of_year:
            return False

        # Check day of month (if specified)
        if rule.day_of_month:
            # Handle end-of-month cases (e.g., day 31 in February)
            last_day = monthrange(check_date.year, check_date.month)[1]
            valid_days = [min(d, last_day) for d in rule.day_of_month]
            if check_date.day not in valid_days:
                return False

        # Check day of week (if specified)
        if rule.day_of_week:
            weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            current_weekday = weekday_names[check_date.weekday()]
            if current_weekday not in rule.day_of_week:
                return False

        # Check interval
        if rule.interval > 1:
            days_diff = (check_date - start_date).days
            if rule.frequency == RecurrenceFrequency.DAILY:
                if days_diff % rule.interval != 0:
                    return False
            elif rule.frequency == RecurrenceFrequency.WEEKLY:
                if (days_diff // 7) % rule.interval != 0:
                    return False
            elif rule.frequency == RecurrenceFrequency.MONTHLY:
                months_diff = (check_date.year - start_date.year) * 12 + (check_date.month - start_date.month)
                if months_diff % rule.interval != 0:
                    return False

        return True

    def _advance_date(self, current: date, rule: RecurrenceRule) -> date:
        """Advance date to next potential occurrence based on frequency."""
        if rule.frequency == RecurrenceFrequency.DAILY:
            return current + timedelta(days=1)
        elif rule.frequency == RecurrenceFrequency.WEEKLY:
            return current + timedelta(days=1)
        elif rule.frequency == RecurrenceFrequency.BIWEEKLY:
            return current + timedelta(days=1)
        elif rule.frequency == RecurrenceFrequency.MONTHLY:
            return current + timedelta(days=1)
        else:
            return current + timedelta(days=1)

    def generate_scheduled_transactions(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Generate scheduled transactions from active recurring templates.

        Creates actual transaction records for upcoming occurrences.
        """
        try:
            # Get all active recurring transactions
            result = self.list_recurring_transactions(is_active=True)
            if not result["success"]:
                return result

            generated = []
            end_date = (date.today() + timedelta(days=days_ahead)).isoformat()

            for recurring_data in result["recurring_transactions"]:
                recurring = RecurringTransaction(**recurring_data)

                if not recurring.auto_create:
                    continue

                # Calculate next occurrences
                from_date = recurring.last_generated_date or recurring.start_date
                occurrences_result = self.calculate_next_occurrences(
                    recurring.recurring_transaction_id,
                    count=days_ahead,  # Generous count
                    from_date=from_date.isoformat() if isinstance(from_date, date) else from_date
                )

                if not occurrences_result["success"]:
                    continue

                # Create transactions for occurrences within the window
                for occurrence_date_str in occurrences_result["occurrences"]:
                    occurrence_date = date.fromisoformat(occurrence_date_str)
                    if occurrence_date > date.fromisoformat(end_date):
                        break

                    # Create transaction
                    transaction_data = {
                        "account_id": recurring.account_id,
                        "date": occurrence_date.isoformat(),
                        "merchant": recurring.merchant,
                        "amount": recurring.base_amount,
                        "transaction_type": recurring.transaction_type.value,
                        "category": recurring.category,
                        "subcategory": recurring.subcategory,
                        "payment_method": recurring.payment_method,
                        "status": "pending",
                        "recurring_transaction_id": recurring.recurring_transaction_id,
                        "notes": f"Auto-generated from template: {recurring.template_name}"
                    }

                    create_result = self.create_transaction(transaction_data)
                    if create_result["success"]:
                        generated.append(create_result["transaction"])

                # Update last_generated_date
                if occurrences_result["occurrences"]:
                    last_occurrence = occurrences_result["occurrences"][-1]
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE recurring_transactions
                            SET last_generated_date = ?,
                                total_generated = total_generated + ?,
                                updated_at = ?
                            WHERE recurring_transaction_id = ?
                        """, (
                            last_occurrence,
                            len([o for o in occurrences_result["occurrences"] if date.fromisoformat(o) <= date.fromisoformat(end_date)]),
                            datetime.utcnow().isoformat(),
                            recurring.recurring_transaction_id
                        ))
                        conn.commit()

            logger.info(f"Generated {len(generated)} scheduled transactions")
            return {
                "success": True,
                "count": len(generated),
                "transactions": generated
            }

        except Exception as e:
            logger.error(f"Error generating scheduled transactions: {e}")
            return {"success": False, "error": str(e)}

    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Get a transaction by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
                row = cursor.fetchone()

                if not row:
                    return {"success": False, "error": "Transaction not found"}

                transaction = self._row_to_transaction(row)
                return {
                    "success": True,
                    "transaction": transaction.dict()
                }

        except Exception as e:
            logger.error(f"Error getting transaction: {e}")
            return {"success": False, "error": str(e)}

    def get_recurring_transaction(self, recurring_transaction_id: str) -> Dict[str, Any]:
        """Get a recurring transaction by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM recurring_transactions WHERE recurring_transaction_id = ?",
                    (recurring_transaction_id,)
                )
                row = cursor.fetchone()

                if not row:
                    return {"success": False, "error": "Recurring transaction not found"}

                recurring = self._row_to_recurring(row)
                return {
                    "success": True,
                    "recurring_transaction": recurring.dict()
                }

        except Exception as e:
            logger.error(f"Error getting recurring transaction: {e}")
            return {"success": False, "error": str(e)}

    def list_recurring_transactions(self, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """List all recurring transactions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if is_active is not None:
                    cursor.execute(
                        "SELECT * FROM recurring_transactions WHERE is_active = ?",
                        (1 if is_active else 0,)
                    )
                else:
                    cursor.execute("SELECT * FROM recurring_transactions")

                rows = cursor.fetchall()
                recurring_transactions = [self._row_to_recurring(row).dict() for row in rows]

                return {
                    "success": True,
                    "count": len(recurring_transactions),
                    "recurring_transactions": recurring_transactions
                }

        except Exception as e:
            logger.error(f"Error listing recurring transactions: {e}")
            return {"success": False, "error": str(e)}

    def search_transactions(
        self,
        account_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        merchant: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search transactions with filters."""
        try:
            query = "SELECT * FROM transactions WHERE 1=1"
            params = []

            if account_id:
                query += " AND account_id = ?"
                params.append(account_id)
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            if category:
                query += " AND category = ?"
                params.append(category)
            if merchant:
                query += " AND merchant LIKE ?"
                params.append(f"%{merchant}%")

            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                transactions = [self._row_to_transaction(row).dict() for row in rows]

                return {
                    "success": True,
                    "count": len(transactions),
                    "transactions": transactions
                }

        except Exception as e:
            logger.error(f"Error searching transactions: {e}")
            return {"success": False, "error": str(e)}

    def detect_recurring_patterns(self, account_id: str, lookback_days: int = 180) -> Dict[str, Any]:
        """Detect potential recurring transaction patterns."""
        # Placeholder for pattern detection logic
        # Would analyze historical transactions and suggest recurring templates
        logger.info(f"Pattern detection not yet implemented")
        return {
            "success": True,
            "patterns_detected": [],
            "message": "Pattern detection coming soon"
        }

    def update_transaction(self, transaction_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a transaction."""
        # Implementation similar to create but with UPDATE query
        return {"success": True, "message": "Update not yet implemented"}

    def delete_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Delete a transaction."""
        # Implementation with DELETE query
        return {"success": True, "message": "Delete not yet implemented"}

    def update_recurring_transaction(self, recurring_transaction_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a recurring transaction."""
        return {"success": True, "message": "Update not yet implemented"}

    def delete_recurring_transaction(self, recurring_transaction_id: str) -> Dict[str, Any]:
        """Delete a recurring transaction."""
        return {"success": True, "message": "Delete not yet implemented"}

    def _row_to_transaction(self, row: tuple) -> Transaction:
        """Convert database row to Transaction object."""
        return Transaction(
            transaction_id=row[0],
            account_id=row[1],
            date=date.fromisoformat(row[2]),
            merchant=row[3],
            amount=row[4],
            transaction_type=TransactionType(row[5]),
            category=row[6],
            subcategory=row[7],
            payment_method=row[8],
            status=TransactionStatus(row[9]),
            notes=row[10],
            tags=json.loads(row[11]) if row[11] else [],
            recurring_transaction_id=row[12],
            parent_transaction_id=row[13],
            bank_transaction_id=row[14],
            reconciled_date=datetime.fromisoformat(row[15]) if row[15] else None,
            receipt_id=row[16],
            attachment_urls=json.loads(row[17]) if row[17] else [],
            created_at=datetime.fromisoformat(row[18]),
            updated_at=datetime.fromisoformat(row[19]),
            created_by=row[20]
        )

    def _row_to_recurring(self, row: tuple) -> RecurringTransaction:
        """Convert database row to RecurringTransaction object."""
        return RecurringTransaction(
            recurring_transaction_id=row[0],
            template_name=row[1],
            account_id=row[2],
            merchant=row[3],
            base_amount=row[4],
            amount_variance=row[5],
            transaction_type=TransactionType(row[6]),
            category=row[7],
            subcategory=row[8],
            payment_method=row[9],
            recurrence_rule=RecurrenceRule(**json.loads(row[10])),
            start_date=date.fromisoformat(row[11]),
            end_date=date.fromisoformat(row[12]) if row[12] else None,
            end_after_occurrences=row[13],
            auto_create=bool(row[14]),
            create_days_before=row[15],
            require_confirmation=bool(row[16]),
            is_active=bool(row[17]),
            last_generated_date=date.fromisoformat(row[18]) if row[18] else None,
            total_generated=row[19],
            created_at=datetime.fromisoformat(row[20]),
            updated_at=datetime.fromisoformat(row[21]),
            notes=row[22],
            tags=json.loads(row[23]) if row[23] else []
        )

    async def _handle_receipt_processed(self, event):
        """Handle receipt processed events."""
        logger.info(f"Received receipt.processed event: {event.event_id}")
        # Could automatically create transaction from receipt data
        # Implementation depends on receipt data structure

    async def _cleanup(self) -> None:
        """Cleanup agent resources."""
        self.message_bus.unsubscribe(self.config.agent_id)
        logger.info("TransactionManagementAgent cleaned up")
