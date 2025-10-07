"""
Reconciliation & Payment Agent

Handles account reconciliation, statement matching, payment processing,
and discrepancy resolution.

Key Features:
- Import and parse external statements (bank, credit card)
- Match statement transactions with internal transactions
- Detect and resolve discrepancies
- Schedule and process payments
- Manage recurring payments
- Generate reconciliation reports
"""

import sqlite3
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import re
from difflib import SequenceMatcher

from core.agents.base import BaseAgent, AgentConfig
from core.agents.coordination.message_bus import MessageBus, Event, EventPriority
from projects.accounting.models.reconciliation import (
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
from projects.accounting.models.transactions import Transaction, TransactionType


class ReconciliationAgent(BaseAgent):
    """
    Reconciliation & Payment Agent

    Responsibilities:
    - Import external statements
    - Match transactions with statements
    - Detect discrepancies
    - Process payments
    - Manage recurring payments
    - Generate reconciliation reports
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
        """Create database tables for reconciliation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Statements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reconciliation_statements (
                statement_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                statement_date TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                opening_balance REAL NOT NULL,
                closing_balance REAL NOT NULL,
                statement_type TEXT NOT NULL,
                institution_name TEXT,
                account_number_last4 TEXT,
                transaction_count INTEGER DEFAULT 0,
                total_debits REAL DEFAULT 0.0,
                total_credits REAL DEFAULT 0.0,
                imported_at TEXT NOT NULL,
                imported_by TEXT,
                source_file TEXT,
                raw_data TEXT,
                notes TEXT
            )
        """)

        # Statement transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statement_transactions (
                statement_transaction_id TEXT PRIMARY KEY,
                statement_id TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                match_status TEXT DEFAULT 'unmatched',
                matched_transaction_id TEXT,
                match_confidence REAL DEFAULT 0.0,
                balance_after REAL,
                reference_number TEXT,
                raw_data TEXT,
                notes TEXT,
                FOREIGN KEY (statement_id) REFERENCES reconciliation_statements(statement_id)
            )
        """)

        # Reconciliations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reconciliations (
                reconciliation_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                statement_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                opening_balance_statement REAL NOT NULL,
                closing_balance_statement REAL NOT NULL,
                opening_balance_internal REAL NOT NULL,
                closing_balance_internal REAL NOT NULL,
                balance_difference REAL DEFAULT 0.0,
                total_statement_transactions INTEGER DEFAULT 0,
                total_internal_transactions INTEGER DEFAULT 0,
                matched_transactions INTEGER DEFAULT 0,
                unmatched_statement_transactions INTEGER DEFAULT 0,
                unmatched_internal_transactions INTEGER DEFAULT 0,
                match_rate REAL DEFAULT 0.0,
                discrepancy_count INTEGER DEFAULT 0,
                total_discrepancy_amount REAL DEFAULT 0.0,
                started_at TEXT,
                completed_at TEXT,
                reconciled_by TEXT,
                is_balanced INTEGER DEFAULT 0,
                requires_adjustment INTEGER DEFAULT 0,
                adjustment_amount REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (statement_id) REFERENCES reconciliation_statements(statement_id)
            )
        """)

        # Transaction matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction_matches (
                match_id TEXT PRIMARY KEY,
                reconciliation_id TEXT NOT NULL,
                internal_transaction_id TEXT NOT NULL,
                statement_transaction_id TEXT NOT NULL,
                match_status TEXT NOT NULL,
                match_confidence REAL NOT NULL,
                match_method TEXT NOT NULL,
                amount_difference REAL DEFAULT 0.0,
                date_difference_days INTEGER DEFAULT 0,
                description_similarity REAL DEFAULT 0.0,
                accepted INTEGER DEFAULT 0,
                rejected INTEGER DEFAULT 0,
                reviewed_by TEXT,
                reviewed_at TEXT,
                created_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (reconciliation_id) REFERENCES reconciliations(reconciliation_id)
            )
        """)

        # Discrepancies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discrepancies (
                discrepancy_id TEXT PRIMARY KEY,
                reconciliation_id TEXT NOT NULL,
                discrepancy_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                internal_transaction_id TEXT,
                statement_transaction_id TEXT,
                description TEXT NOT NULL,
                expected_value REAL,
                actual_value REAL,
                difference REAL,
                status TEXT DEFAULT 'open',
                resolution TEXT,
                resolved_by TEXT,
                resolved_at TEXT,
                detected_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (reconciliation_id) REFERENCES reconciliations(reconciliation_id)
            )
        """)

        # Payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                from_account_id TEXT NOT NULL,
                to_account_id TEXT,
                payee_name TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                scheduled_date TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                payment_status TEXT DEFAULT 'scheduled',
                submitted_at TEXT,
                processed_at TEXT,
                completed_at TEXT,
                transaction_id TEXT,
                memo TEXT,
                reference_number TEXT,
                confirmation_number TEXT,
                is_recurring INTEGER DEFAULT 0,
                recurring_payment_id TEXT,
                failure_reason TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by TEXT,
                notes TEXT
            )
        """)

        # Recurring payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recurring_payments (
                recurring_payment_id TEXT PRIMARY KEY,
                from_account_id TEXT NOT NULL,
                payee_name TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                frequency TEXT NOT NULL,
                day_of_month INTEGER,
                day_of_week TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT,
                next_payment_date TEXT,
                is_active INTEGER DEFAULT 1,
                payments_created INTEGER DEFAULT 0,
                last_payment_id TEXT,
                last_payment_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                memo TEXT,
                notes TEXT
            )
        """)

        # Adjustment entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adjustment_entries (
                adjustment_id TEXT PRIMARY KEY,
                reconciliation_id TEXT NOT NULL,
                discrepancy_id TEXT,
                account_id TEXT NOT NULL,
                adjustment_type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                approved_by TEXT,
                approved_at TEXT,
                transaction_id TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT,
                notes TEXT,
                FOREIGN KEY (reconciliation_id) REFERENCES reconciliations(reconciliation_id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statements_account ON reconciliation_statements(account_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statement_trans_statement ON statement_transactions(statement_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statement_trans_match ON statement_transactions(match_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reconciliations_account ON reconciliations(account_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reconciliations_status ON reconciliations(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(payment_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_scheduled ON payments(scheduled_date)")

        conn.commit()
        conn.close()

    async def _setup_event_subscriptions(self):
        """Subscribe to relevant events."""
        from core.agents.coordination.message_bus import get_default_message_bus
        self.message_bus = get_default_message_bus()

        # Subscribe to transaction events
        self.message_bus.subscribe(
            agent_id=self.agent_id,
            event_types=["transaction.created"],
            callback=self._handle_transaction_event
        )

    async def _handle_transaction_event(self, event: Event):
        """Handle transaction events for payment tracking."""
        try:
            transaction_data = event.payload.get("transaction", {})
            transaction = Transaction(**transaction_data)

            # Check if this transaction is related to a payment
            # This could be enhanced to link payments with transactions
            self.logger.info(f"Transaction event received: {transaction.transaction_id}")

        except Exception as e:
            self.logger.error(f"Error handling transaction event: {e}")

    async def _execute(self, task: Dict) -> Dict:
        """Execute reconciliation operations."""
        operation = task.get("operation")
        parameters = task.get("parameters", {})

        operations = {
            # Statement operations
            "import_statement": self.import_statement,
            "get_statement": self.get_statement,
            "list_statements": self.list_statements,

            # Reconciliation operations
            "start_reconciliation": self.start_reconciliation,
            "get_reconciliation": self.get_reconciliation,
            "match_transactions": self.match_transactions,
            "accept_match": self.accept_match,
            "reject_match": self.reject_match,
            "complete_reconciliation": self.complete_reconciliation,

            # Discrepancy operations
            "list_discrepancies": self.list_discrepancies,
            "resolve_discrepancy": self.resolve_discrepancy,
            "create_adjustment": self.create_adjustment,

            # Payment operations
            "schedule_payment": self.schedule_payment,
            "process_payments": self.process_payments,
            "get_payment": self.get_payment,
            "cancel_payment": self.cancel_payment,

            # Recurring payment operations
            "create_recurring_payment": self.create_recurring_payment,
            "generate_scheduled_payments": self.generate_scheduled_payments,

            # Reporting
            "generate_reconciliation_summary": self.generate_reconciliation_summary
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

    async def import_statement(self, statement_data: Dict) -> Dict:
        """
        Import external statement.

        Args:
            statement_data: Statement configuration including:
                - account_id: Account ID
                - statement_date: Statement date
                - start_date: Period start
                - end_date: Period end
                - opening_balance: Opening balance
                - closing_balance: Closing balance
                - transactions: List of statement transactions

        Returns:
            Imported statement with ID
        """
        import json

        # Create statement model
        transactions_list = statement_data.pop("transactions", [])
        statement = ReconciliationStatement(**statement_data)

        # Calculate totals
        statement.transaction_count = len(transactions_list)
        statement.total_debits = sum(
            t["amount"] for t in transactions_list if t["transaction_type"] == "debit"
        )
        statement.total_credits = sum(
            t["amount"] for t in transactions_list if t["transaction_type"] == "credit"
        )

        # Save statement
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reconciliation_statements (
                statement_id, account_id, statement_date, start_date, end_date,
                opening_balance, closing_balance, statement_type, institution_name,
                account_number_last4, transaction_count, total_debits, total_credits,
                imported_at, imported_by, source_file, raw_data, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            statement.statement_id,
            statement.account_id,
            statement.statement_date.isoformat(),
            statement.start_date.isoformat(),
            statement.end_date.isoformat(),
            statement.opening_balance,
            statement.closing_balance,
            statement.statement_type,
            statement.institution_name,
            statement.account_number_last4,
            statement.transaction_count,
            statement.total_debits,
            statement.total_credits,
            statement.imported_at.isoformat(),
            statement.imported_by,
            statement.source_file,
            json.dumps(statement.raw_data),
            statement.notes
        ))

        # Save statement transactions
        for trans_data in transactions_list:
            trans = StatementTransaction(
                statement_id=statement.statement_id,
                **trans_data
            )

            cursor.execute("""
                INSERT INTO statement_transactions (
                    statement_transaction_id, statement_id, date, description,
                    amount, transaction_type, match_status, matched_transaction_id,
                    match_confidence, balance_after, reference_number, raw_data, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trans.statement_transaction_id,
                trans.statement_id,
                trans.date.isoformat(),
                trans.description,
                trans.amount,
                trans.transaction_type,
                trans.match_status.value,
                trans.matched_transaction_id,
                trans.match_confidence,
                trans.balance_after,
                trans.reference_number,
                json.dumps(trans.raw_data),
                trans.notes
            ))

        conn.commit()
        conn.close()

        # Publish event
        if self.message_bus:
            await self.message_bus.publish(
                event_type="statement.imported",
                payload={
                    "statement_id": statement.statement_id,
                    "account_id": statement.account_id,
                    "transaction_count": statement.transaction_count
                },
                source_agent=self.agent_id
            )

        return statement.dict()

    async def get_statement(self, statement_id: str) -> Optional[Dict]:
        """Get statement by ID."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM reconciliation_statements WHERE statement_id = ?",
            (statement_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # Load transactions
        cursor.execute(
            "SELECT * FROM statement_transactions WHERE statement_id = ?",
            (statement_id,)
        )

        transactions = []
        for trans_row in cursor.fetchall():
            transactions.append({
                "statement_transaction_id": trans_row[0],
                "date": trans_row[2],
                "description": trans_row[3],
                "amount": trans_row[4],
                "transaction_type": trans_row[5],
                "match_status": trans_row[6],
                "matched_transaction_id": trans_row[7],
                "match_confidence": trans_row[8]
            })

        conn.close()

        return {
            "statement_id": row[0],
            "account_id": row[1],
            "statement_date": row[2],
            "start_date": row[3],
            "end_date": row[4],
            "opening_balance": row[5],
            "closing_balance": row[6],
            "transaction_count": row[10],
            "transactions": transactions
        }

    async def list_statements(
        self,
        account_id: Optional[str] = None,
        start_date: Optional[str] = None
    ) -> List[Dict]:
        """List statements with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM reconciliation_statements WHERE 1=1"
        params = []

        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)

        if start_date:
            query += " AND start_date >= ?"
            params.append(start_date)

        query += " ORDER BY statement_date DESC"

        cursor.execute(query, params)

        statements = []
        for row in cursor.fetchall():
            statements.append({
                "statement_id": row[0],
                "account_id": row[1],
                "statement_date": row[2],
                "start_date": row[3],
                "end_date": row[4],
                "opening_balance": row[5],
                "closing_balance": row[6],
                "transaction_count": row[10]
            })

        conn.close()
        return statements

    async def start_reconciliation(
        self,
        account_id: str,
        statement_id: str,
        current_balance: float
    ) -> Dict:
        """
        Start reconciliation process.

        Args:
            account_id: Account to reconcile
            statement_id: Statement to reconcile against
            current_balance: Current internal balance

        Returns:
            Reconciliation session
        """
        # Load statement
        statement_dict = await self.get_statement(statement_id)
        if not statement_dict:
            return {"error": "Statement not found"}

        statement = ReconciliationStatement(**statement_dict)

        # Get internal transactions for period
        internal_transactions = await self._get_internal_transactions(
            account_id,
            statement.start_date,
            statement.end_date
        )

        # Calculate opening balance for internal
        opening_internal = self._calculate_opening_balance(
            current_balance,
            internal_transactions,
            statement.start_date,
            statement.end_date
        )

        # Create reconciliation
        recon = Reconciliation(
            account_id=account_id,
            statement_id=statement_id,
            start_date=statement.start_date,
            end_date=statement.end_date,
            opening_balance_statement=statement.opening_balance,
            closing_balance_statement=statement.closing_balance,
            opening_balance_internal=opening_internal,
            closing_balance_internal=current_balance,
            total_statement_transactions=statement.transaction_count,
            total_internal_transactions=len(internal_transactions),
            status=ReconciliationStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )

        recon.calculate_balance_difference()
        recon.check_balanced()

        # Save reconciliation
        self._save_reconciliation(recon)

        # Publish event
        if self.message_bus:
            await self.message_bus.publish(
                event_type="reconciliation.started",
                payload={
                    "reconciliation_id": recon.reconciliation_id,
                    "account_id": account_id,
                    "statement_id": statement_id
                },
                source_agent=self.agent_id
            )

        return recon.dict()

    def _calculate_opening_balance(
        self,
        current_balance: float,
        transactions: List[Transaction],
        start_date: date,
        end_date: date
    ) -> float:
        """Calculate opening balance from current balance and transactions."""
        opening = current_balance

        for trans in transactions:
            if trans.transaction_type == TransactionType.INCOME:
                opening -= trans.amount
            elif trans.transaction_type == TransactionType.EXPENSE:
                opening += trans.amount

        return opening

    async def _get_internal_transactions(
        self,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> List[Transaction]:
        """Get internal transactions for period."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM transactions
            WHERE account_id = ?
            AND date >= ?
            AND date <= ?
            ORDER BY date
        """, (account_id, start_date.isoformat(), end_date.isoformat()))

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
                subcategory=row[7]
            ))

        conn.close()
        return transactions

    async def match_transactions(self, reconciliation_id: str) -> Dict:
        """
        Auto-match statement transactions with internal transactions.

        Uses fuzzy matching on date, amount, and description.

        Returns:
            Match results with suggestions
        """
        # Get reconciliation
        recon_dict = await self.get_reconciliation(reconciliation_id)
        if not recon_dict:
            return {"error": "Reconciliation not found"}

        # Get statement transactions
        statement_transactions = await self._get_statement_transactions(
            recon_dict["statement_id"]
        )

        # Get internal transactions
        internal_transactions = await self._get_internal_transactions(
            recon_dict["account_id"],
            date.fromisoformat(recon_dict["start_date"]),
            date.fromisoformat(recon_dict["end_date"])
        )

        # Match transactions
        matches = []
        suggestions = []

        for stmt_trans in statement_transactions:
            if stmt_trans.match_status == MatchStatus.MATCHED:
                continue

            best_match = None
            best_score = 0.0

            for internal_trans in internal_transactions:
                # Skip already matched
                if self._is_transaction_matched(internal_trans.transaction_id):
                    continue

                score = self._calculate_match_score(stmt_trans, internal_trans)

                if score > best_score:
                    best_score = score
                    best_match = internal_trans

            # If confident match, create match
            if best_match and best_score >= 0.8:
                match = self._create_match(
                    reconciliation_id,
                    internal_trans=best_match,
                    stmt_trans=stmt_trans,
                    confidence=best_score,
                    method="auto"
                )
                matches.append(match)
                self._save_match(match)

            # If possible match, create suggestion
            elif best_match and best_score >= 0.5:
                suggestion = MatchingSuggestion(
                    reconciliation_id=reconciliation_id,
                    internal_transaction_id=best_match.transaction_id,
                    statement_transaction_id=stmt_trans.statement_transaction_id,
                    confidence_score=best_score,
                    match_reason="Fuzzy match on date and amount"
                )
                suggestions.append(suggestion.dict())

        # Update reconciliation stats
        await self._update_reconciliation_stats(reconciliation_id)

        return {
            "matches_created": len(matches),
            "suggestions": suggestions,
            "match_results": [m.dict() for m in matches]
        }

    def _calculate_match_score(
        self,
        stmt_trans: StatementTransaction,
        internal_trans: Transaction
    ) -> float:
        """Calculate matching score between transactions."""
        score = 0.0

        # Amount match (40%)
        if abs(stmt_trans.amount - internal_trans.amount) < 0.01:
            score += 0.4
        elif abs(stmt_trans.amount - internal_trans.amount) < 1.0:
            score += 0.2

        # Date match (30%)
        date_diff = abs((stmt_trans.date - internal_trans.date).days)
        if date_diff == 0:
            score += 0.3
        elif date_diff <= 2:
            score += 0.2
        elif date_diff <= 5:
            score += 0.1

        # Description similarity (30%)
        desc_sim = SequenceMatcher(
            None,
            stmt_trans.description.lower(),
            internal_trans.merchant.lower()
        ).ratio()
        score += desc_sim * 0.3

        return score

    def _create_match(
        self,
        reconciliation_id: str,
        internal_trans: Transaction,
        stmt_trans: StatementTransaction,
        confidence: float,
        method: str
    ) -> TransactionMatch:
        """Create transaction match."""
        date_diff = abs((stmt_trans.date - internal_trans.date).days)
        amount_diff = abs(stmt_trans.amount - internal_trans.amount)

        return TransactionMatch(
            reconciliation_id=reconciliation_id,
            internal_transaction_id=internal_trans.transaction_id,
            statement_transaction_id=stmt_trans.statement_transaction_id,
            match_status=MatchStatus.MATCHED,
            match_confidence=confidence,
            match_method=method,
            amount_difference=amount_diff,
            date_difference_days=date_diff
        )

    def _save_match(self, match: TransactionMatch):
        """Save transaction match to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO transaction_matches (
                match_id, reconciliation_id, internal_transaction_id,
                statement_transaction_id, match_status, match_confidence,
                match_method, amount_difference, date_difference_days,
                description_similarity, accepted, rejected,
                reviewed_by, reviewed_at, created_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match.match_id,
            match.reconciliation_id,
            match.internal_transaction_id,
            match.statement_transaction_id,
            match.match_status.value,
            match.match_confidence,
            match.match_method,
            match.amount_difference,
            match.date_difference_days,
            match.description_similarity,
            1 if match.accepted else 0,
            1 if match.rejected else 0,
            match.reviewed_by,
            match.reviewed_at.isoformat() if match.reviewed_at else None,
            match.created_at.isoformat(),
            match.notes
        ))

        # Update statement transaction
        cursor.execute("""
            UPDATE statement_transactions
            SET match_status = 'matched',
                matched_transaction_id = ?,
                match_confidence = ?
            WHERE statement_transaction_id = ?
        """, (
            match.internal_transaction_id,
            match.match_confidence,
            match.statement_transaction_id
        ))

        conn.commit()
        conn.close()

    def _is_transaction_matched(self, transaction_id: str) -> bool:
        """Check if internal transaction is already matched."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM transaction_matches
            WHERE internal_transaction_id = ?
            AND match_status = 'matched'
        """, (transaction_id,))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    async def _get_statement_transactions(
        self,
        statement_id: str
    ) -> List[StatementTransaction]:
        """Get statement transactions."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM statement_transactions
            WHERE statement_id = ?
        """, (statement_id,))

        transactions = []
        for row in cursor.fetchall():
            transactions.append(StatementTransaction(
                statement_transaction_id=row[0],
                statement_id=row[1],
                date=date.fromisoformat(row[2]),
                description=row[3],
                amount=row[4],
                transaction_type=row[5],
                match_status=MatchStatus(row[6]),
                matched_transaction_id=row[7],
                match_confidence=row[8],
                raw_data=json.loads(row[11]) if row[11] else {}
            ))

        conn.close()
        return transactions

    async def _update_reconciliation_stats(self, reconciliation_id: str):
        """Update reconciliation statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count matched transactions
        cursor.execute("""
            SELECT COUNT(*) FROM transaction_matches
            WHERE reconciliation_id = ?
            AND match_status = 'matched'
        """, (reconciliation_id,))
        matched_count = cursor.fetchone()[0]

        # Get reconciliation
        cursor.execute("""
            SELECT total_statement_transactions, total_internal_transactions
            FROM reconciliations
            WHERE reconciliation_id = ?
        """, (reconciliation_id,))
        row = cursor.fetchone()

        if row:
            total_stmt = row[0]
            total_internal = row[1]
            unmatched_stmt = total_stmt - matched_count
            unmatched_internal = total_internal - matched_count
            match_rate = (matched_count / total_stmt * 100) if total_stmt > 0 else 0

            # Update stats
            cursor.execute("""
                UPDATE reconciliations
                SET matched_transactions = ?,
                    unmatched_statement_transactions = ?,
                    unmatched_internal_transactions = ?,
                    match_rate = ?,
                    updated_at = ?
                WHERE reconciliation_id = ?
            """, (
                matched_count,
                unmatched_stmt,
                unmatched_internal,
                match_rate,
                datetime.utcnow().isoformat(),
                reconciliation_id
            ))

        conn.commit()
        conn.close()

    async def accept_match(self, match_id: str, reviewed_by: str) -> Dict:
        """Accept a transaction match."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE transaction_matches
            SET accepted = 1,
                reviewed_by = ?,
                reviewed_at = ?
            WHERE match_id = ?
        """, (reviewed_by, datetime.utcnow().isoformat(), match_id))

        conn.commit()
        conn.close()

        return {"match_id": match_id, "accepted": True}

    async def reject_match(self, match_id: str, reviewed_by: str) -> Dict:
        """Reject a transaction match."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get match details
        cursor.execute("""
            SELECT statement_transaction_id FROM transaction_matches
            WHERE match_id = ?
        """, (match_id,))
        row = cursor.fetchone()

        if row:
            # Update match
            cursor.execute("""
                UPDATE transaction_matches
                SET rejected = 1,
                    reviewed_by = ?,
                    reviewed_at = ?
                WHERE match_id = ?
            """, (reviewed_by, datetime.utcnow().isoformat(), match_id))

            # Reset statement transaction
            cursor.execute("""
                UPDATE statement_transactions
                SET match_status = 'unmatched',
                    matched_transaction_id = NULL,
                    match_confidence = 0.0
                WHERE statement_transaction_id = ?
            """, (row[0],))

        conn.commit()
        conn.close()

        return {"match_id": match_id, "rejected": True}

    async def complete_reconciliation(self, reconciliation_id: str) -> Dict:
        """Complete reconciliation process."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE reconciliations
            SET status = 'completed',
                completed_at = ?
            WHERE reconciliation_id = ?
        """, (datetime.utcnow().isoformat(), reconciliation_id))

        conn.commit()
        conn.close()

        # Publish event
        if self.message_bus:
            await self.message_bus.publish(
                event_type="reconciliation.completed",
                payload={"reconciliation_id": reconciliation_id},
                source_agent=self.agent_id
            )

        return {"reconciliation_id": reconciliation_id, "status": "completed"}

    async def get_reconciliation(self, reconciliation_id: str) -> Optional[Dict]:
        """Get reconciliation by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM reconciliations
            WHERE reconciliation_id = ?
        """, (reconciliation_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        conn.close()

        return {
            "reconciliation_id": row[0],
            "account_id": row[1],
            "statement_id": row[2],
            "start_date": row[3],
            "end_date": row[4],
            "status": row[5],
            "balance_difference": row[10],
            "match_rate": row[15],
            "is_balanced": bool(row[21])
        }

    def _save_reconciliation(self, recon: Reconciliation):
        """Save reconciliation to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reconciliations (
                reconciliation_id, account_id, statement_id, start_date, end_date,
                status, opening_balance_statement, closing_balance_statement,
                opening_balance_internal, closing_balance_internal, balance_difference,
                total_statement_transactions, total_internal_transactions,
                matched_transactions, unmatched_statement_transactions,
                unmatched_internal_transactions, match_rate, discrepancy_count,
                total_discrepancy_amount, started_at, completed_at, reconciled_by,
                is_balanced, requires_adjustment, adjustment_amount,
                created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recon.reconciliation_id,
            recon.account_id,
            recon.statement_id,
            recon.start_date.isoformat(),
            recon.end_date.isoformat(),
            recon.status.value,
            recon.opening_balance_statement,
            recon.closing_balance_statement,
            recon.opening_balance_internal,
            recon.closing_balance_internal,
            recon.balance_difference,
            recon.total_statement_transactions,
            recon.total_internal_transactions,
            recon.matched_transactions,
            recon.unmatched_statement_transactions,
            recon.unmatched_internal_transactions,
            recon.match_rate,
            recon.discrepancy_count,
            recon.total_discrepancy_amount,
            recon.started_at.isoformat() if recon.started_at else None,
            recon.completed_at.isoformat() if recon.completed_at else None,
            recon.reconciled_by,
            1 if recon.is_balanced else 0,
            1 if recon.requires_adjustment else 0,
            recon.adjustment_amount,
            recon.created_at.isoformat(),
            recon.updated_at.isoformat(),
            recon.notes
        ))

        conn.commit()
        conn.close()

    async def list_discrepancies(
        self,
        reconciliation_id: str,
        status: Optional[str] = None
    ) -> List[Dict]:
        """List discrepancies for reconciliation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM discrepancies WHERE reconciliation_id = ?"
        params = [reconciliation_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        cursor.execute(query, params)

        discrepancies = []
        for row in cursor.fetchall():
            discrepancies.append({
                "discrepancy_id": row[0],
                "discrepancy_type": row[2],
                "severity": row[3],
                "description": row[6],
                "status": row[10]
            })

        conn.close()
        return discrepancies

    async def resolve_discrepancy(
        self,
        discrepancy_id: str,
        resolution: str,
        resolved_by: str
    ) -> Dict:
        """Resolve a discrepancy."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE discrepancies
            SET status = 'resolved',
                resolution = ?,
                resolved_by = ?,
                resolved_at = ?
            WHERE discrepancy_id = ?
        """, (resolution, resolved_by, datetime.utcnow().isoformat(), discrepancy_id))

        conn.commit()
        conn.close()

        return {"discrepancy_id": discrepancy_id, "status": "resolved"}

    async def create_adjustment(self, adjustment_data: Dict) -> Dict:
        """Create adjustment entry."""
        adjustment = AdjustmentEntry(**adjustment_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO adjustment_entries (
                adjustment_id, reconciliation_id, discrepancy_id, account_id,
                adjustment_type, amount, description, status, approved_by,
                approved_at, transaction_id, created_at, created_by, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            adjustment.adjustment_id,
            adjustment.reconciliation_id,
            adjustment.discrepancy_id,
            adjustment.account_id,
            adjustment.adjustment_type,
            adjustment.amount,
            adjustment.description,
            adjustment.status,
            adjustment.approved_by,
            adjustment.approved_at.isoformat() if adjustment.approved_at else None,
            adjustment.transaction_id,
            adjustment.created_at.isoformat(),
            adjustment.created_by,
            adjustment.notes
        ))

        conn.commit()
        conn.close()

        return adjustment.dict()

    async def schedule_payment(self, payment_data: Dict) -> Dict:
        """Schedule a payment."""
        payment = Payment(**payment_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO payments (
                payment_id, from_account_id, to_account_id, payee_name,
                amount, currency, scheduled_date, payment_method, payment_status,
                submitted_at, processed_at, completed_at, transaction_id,
                memo, reference_number, confirmation_number,
                is_recurring, recurring_payment_id, failure_reason,
                retry_count, max_retries, created_at, updated_at,
                created_by, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payment.payment_id,
            payment.from_account_id,
            payment.to_account_id,
            payment.payee_name,
            payment.amount,
            payment.currency,
            payment.scheduled_date.isoformat(),
            payment.payment_method.value,
            payment.payment_status.value,
            payment.submitted_at.isoformat() if payment.submitted_at else None,
            payment.processed_at.isoformat() if payment.processed_at else None,
            payment.completed_at.isoformat() if payment.completed_at else None,
            payment.transaction_id,
            payment.memo,
            payment.reference_number,
            payment.confirmation_number,
            1 if payment.is_recurring else 0,
            payment.recurring_payment_id,
            payment.failure_reason,
            payment.retry_count,
            payment.max_retries,
            payment.created_at.isoformat(),
            payment.updated_at.isoformat(),
            payment.created_by,
            payment.notes
        ))

        conn.commit()
        conn.close()

        # Publish event
        if self.message_bus:
            await self.message_bus.publish(
                event_type="payment.scheduled",
                payload={"payment": payment.dict()},
                source_agent=self.agent_id
            )

        return payment.dict()

    async def process_payments(self, scheduled_date: Optional[str] = None) -> Dict:
        """Process scheduled payments for a date."""
        if scheduled_date is None:
            scheduled_date = date.today().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM payments
            WHERE scheduled_date <= ?
            AND payment_status = 'scheduled'
        """, (scheduled_date,))

        payments_processed = 0
        for row in cursor.fetchall():
            # Update payment status
            cursor.execute("""
                UPDATE payments
                SET payment_status = 'completed',
                    processed_at = ?,
                    completed_at = ?
                WHERE payment_id = ?
            """, (
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
                row[0]
            ))
            payments_processed += 1

        conn.commit()
        conn.close()

        return {"payments_processed": payments_processed}

    async def get_payment(self, payment_id: str) -> Optional[Dict]:
        """Get payment by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        conn.close()

        return {
            "payment_id": row[0],
            "from_account_id": row[1],
            "payee_name": row[3],
            "amount": row[4],
            "scheduled_date": row[6],
            "payment_status": row[8]
        }

    async def cancel_payment(self, payment_id: str) -> Dict:
        """Cancel a scheduled payment."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE payments
            SET payment_status = 'cancelled',
                updated_at = ?
            WHERE payment_id = ?
            AND payment_status = 'scheduled'
        """, (datetime.utcnow().isoformat(), payment_id))

        conn.commit()
        conn.close()

        return {"payment_id": payment_id, "status": "cancelled"}

    async def create_recurring_payment(self, recurring_data: Dict) -> Dict:
        """Create recurring payment template."""
        recurring = RecurringPayment(**recurring_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO recurring_payments (
                recurring_payment_id, from_account_id, payee_name, amount,
                payment_method, frequency, day_of_month, day_of_week,
                start_date, end_date, next_payment_date, is_active,
                payments_created, last_payment_id, last_payment_date,
                created_at, updated_at, memo, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recurring.recurring_payment_id,
            recurring.from_account_id,
            recurring.payee_name,
            recurring.amount,
            recurring.payment_method.value,
            recurring.frequency,
            recurring.day_of_month,
            recurring.day_of_week,
            recurring.start_date.isoformat(),
            recurring.end_date.isoformat() if recurring.end_date else None,
            recurring.next_payment_date.isoformat() if recurring.next_payment_date else None,
            1 if recurring.is_active else 0,
            recurring.payments_created,
            recurring.last_payment_id,
            recurring.last_payment_date.isoformat() if recurring.last_payment_date else None,
            recurring.created_at.isoformat(),
            recurring.updated_at.isoformat(),
            recurring.memo,
            recurring.notes
        ))

        conn.commit()
        conn.close()

        return recurring.dict()

    async def generate_scheduled_payments(self, days_ahead: int = 30) -> Dict:
        """Generate scheduled payments from recurring templates."""
        # Placeholder - similar to recurring transactions
        return {"status": "not_implemented"}

    async def generate_reconciliation_summary(
        self,
        reconciliation_id: str
    ) -> Dict:
        """Generate reconciliation summary report."""
        recon_dict = await self.get_reconciliation(reconciliation_id)
        if not recon_dict:
            return {"error": "Reconciliation not found"}

        summary = ReconciliationSummary(
            reconciliation_id=reconciliation_id,
            account_id=recon_dict["account_id"],
            period_start=date.fromisoformat(recon_dict["start_date"]),
            period_end=date.fromisoformat(recon_dict["end_date"]),
            is_reconciled=recon_dict["is_balanced"],
            match_rate=recon_dict["match_rate"],
            discrepancy_count=0,
            total_discrepancy_amount=0.0,
            statement_balance=0.0,
            internal_balance=0.0,
            difference=recon_dict["balance_difference"],
            matched=0,
            unmatched_statement=0,
            unmatched_internal=0,
            adjustments_needed=False,
            adjustment_amount=0.0
        )

        return summary.dict()
