"""
Envelope Service - Virtual Envelope Balance Tracking

This service handles all operations related to budget and payment envelopes.
It provides the core business logic for:

1. Posting transactions and updating envelope balances
2. Validating allocations to prevent overspending
3. Calculating bank account breakdowns (Bank = Budget + Payment + Available)
4. Applying monthly allocations and rollover policies
5. Forecasting future balances based on budgets

IMPORTANT: Envelopes are VIRTUAL - money never physically moves to/from them.
All real money stays in bank accounts. Envelopes are metadata tracking allocations.
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from ..models.budget_envelopes import (
    BudgetEnvelope,
    PaymentEnvelope,
    BudgetAllocation,
    EnvelopeTransaction,
    BankAccountView,
    EnvelopeType,
    RolloverPolicy
)
from ..models.journal_entries import (
    JournalEntry,
    Distribution,
    FlowDirection,
    AccountType
)


class EnvelopeService:
    """
    Service for managing virtual budget and payment envelopes.

    This service coordinates envelope balance updates when transactions are posted.
    It ensures the fundamental equation always holds:
        Bank Balance = Budget Allocated + Payment Reserved + Available
    """

    def __init__(self):
        """Initialize the envelope service."""
        # In a real implementation, these would be database repositories
        self.budget_envelopes: Dict[str, BudgetEnvelope] = {}
        self.payment_envelopes: Dict[str, PaymentEnvelope] = {}
        self.envelope_transactions: List[EnvelopeTransaction] = []
        self.allocations: List[BudgetAllocation] = []

    # -------------------------------------------------------------------------
    # TRANSACTION POSTING - Update envelopes when transactions post
    # -------------------------------------------------------------------------

    def post_journal_entry(self, journal_entry: JournalEntry) -> List[EnvelopeTransaction]:
        """
        Post a journal entry and update all affected envelope balances.

        When a transaction is posted, this method:
        1. Checks each distribution for envelope references
        2. Updates budget envelopes (for expenses)
        3. Updates payment envelopes (for liability charges/payments)
        4. Creates audit trail records (EnvelopeTransaction)

        Args:
            journal_entry: The journal entry being posted

        Returns:
            List of EnvelopeTransaction records created

        Example - Credit Card Purchase:
            Distributions:
                1. Credit Card Liability (FROM) +$100, payment_envelope_id="1600"
                2. Grocery Expense (TO) +$100, budget_envelope_id="1500"

            Effects:
                - Budget Envelope 1500: -$100 (spent from groceries budget)
                - Payment Envelope 1600: +$100 (reserve cash for CC payment)
        """
        envelope_txns = []

        for dist in journal_entry.distributions:
            # Handle Budget Envelope updates (Expenses)
            if dist.budget_envelope_id:
                envelope_txn = self._update_budget_envelope(
                    envelope_id=dist.budget_envelope_id,
                    distribution=dist,
                    journal_entry=journal_entry
                )
                if envelope_txn:
                    envelope_txns.append(envelope_txn)

            # Handle Payment Envelope updates (Liabilities)
            if dist.payment_envelope_id:
                envelope_txn = self._update_payment_envelope(
                    envelope_id=dist.payment_envelope_id,
                    distribution=dist,
                    journal_entry=journal_entry
                )
                if envelope_txn:
                    envelope_txns.append(envelope_txn)

        return envelope_txns

    def _update_budget_envelope(
        self,
        envelope_id: str,
        distribution: Distribution,
        journal_entry: JournalEntry
    ) -> Optional[EnvelopeTransaction]:
        """
        Update a budget envelope based on an expense distribution.

        Rules:
        - Expense account with TO flow (normal): Decrease envelope (spending)
        - Expense account with FROM flow (refund): Increase envelope (refund)

        Args:
            envelope_id: ID of the budget envelope
            distribution: The distribution affecting the envelope
            journal_entry: Parent journal entry

        Returns:
            EnvelopeTransaction record if envelope was updated
        """
        envelope = self.budget_envelopes.get(envelope_id)
        if not envelope:
            raise ValueError(f"Budget envelope {envelope_id} not found")

        # Determine transaction type and amount
        if distribution.flow_direction == FlowDirection.TO:
            # Normal expense: decrease envelope
            transaction_type = "expense"
            balance_before = envelope.current_balance
            envelope.record_expense(distribution.amount)
            balance_after = envelope.current_balance

        else:  # FROM
            # Expense refund: increase envelope
            transaction_type = "refund"
            balance_before = envelope.current_balance
            envelope.record_refund(distribution.amount)
            balance_after = envelope.current_balance

        # Create audit trail
        envelope_txn = EnvelopeTransaction(
            envelope_id=envelope_id,
            envelope_type=EnvelopeType.BUDGET,
            journal_entry_id=journal_entry.journal_entry_id,
            distribution_id=distribution.distribution_id,
            transaction_date=journal_entry.entry_date,
            transaction_type=transaction_type,
            amount=-distribution.amount if transaction_type == "expense" else distribution.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=distribution.description or journal_entry.description
        )

        self.envelope_transactions.append(envelope_txn)
        return envelope_txn

    def _update_payment_envelope(
        self,
        envelope_id: str,
        distribution: Distribution,
        journal_entry: JournalEntry
    ) -> Optional[EnvelopeTransaction]:
        """
        Update a payment envelope based on a liability distribution.

        Rules:
        - Liability FROM (charge): Increase envelope (reserve more cash)
        - Liability TO (payment): Decrease envelope (release reserved cash)

        Args:
            envelope_id: ID of the payment envelope
            distribution: The distribution affecting the envelope
            journal_entry: Parent journal entry

        Returns:
            EnvelopeTransaction record if envelope was updated
        """
        envelope = self.payment_envelopes.get(envelope_id)
        if not envelope:
            raise ValueError(f"Payment envelope {envelope_id} not found")

        # Determine transaction type and amount
        if distribution.flow_direction == FlowDirection.FROM:
            # Liability increases (charge): increase payment reserve
            transaction_type = "charge"
            balance_before = envelope.current_balance
            envelope.record_charge(distribution.amount)
            balance_after = envelope.current_balance

        else:  # TO
            # Liability decreases (payment or credit): decrease payment reserve
            if distribution.account_type == AccountType.ASSET:
                # This is a payment (cash going out)
                transaction_type = "payment"
            else:
                # This is a credit/refund
                transaction_type = "credit"

            balance_before = envelope.current_balance
            envelope.record_payment(distribution.amount)
            balance_after = envelope.current_balance

        # Create audit trail
        envelope_txn = EnvelopeTransaction(
            envelope_id=envelope_id,
            envelope_type=EnvelopeType.PAYMENT,
            journal_entry_id=journal_entry.journal_entry_id,
            distribution_id=distribution.distribution_id,
            transaction_date=journal_entry.entry_date,
            transaction_type=transaction_type,
            amount=distribution.amount if transaction_type == "charge" else -distribution.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=distribution.description or journal_entry.description
        )

        self.envelope_transactions.append(envelope_txn)
        return envelope_txn

    # -------------------------------------------------------------------------
    # BUDGET ALLOCATION - Apply monthly allocations
    # -------------------------------------------------------------------------

    def apply_monthly_allocations(
        self,
        source_account_id: str,
        allocation_date: date,
        period_label: str
    ) -> List[BudgetAllocation]:
        """
        Apply monthly allocations to all active budget envelopes.

        This is typically run at the beginning of each month to "fund"
        the budget envelopes for the new period.

        Args:
            source_account_id: Bank account providing the allocation
            allocation_date: Date of the allocation
            period_label: Period identifier (e.g., "2025-01")

        Returns:
            List of BudgetAllocation records created
        """
        allocations = []

        for envelope in self.budget_envelopes.values():
            if not envelope.is_active or envelope.monthly_allocation <= 0:
                continue

            # Apply allocation based on rollover policy
            amount = envelope.apply_monthly_allocation(allocation_date)

            # Create allocation record
            allocation = BudgetAllocation(
                source_account_id=source_account_id,
                envelope_id=envelope.envelope_id,
                envelope_type=EnvelopeType.BUDGET,
                allocation_date=allocation_date,
                amount=amount,
                period_label=period_label,
                description=f"Monthly allocation for {envelope.envelope_name}",
                is_automatic=True
            )

            allocations.append(allocation)
            self.allocations.append(allocation)

            # Create envelope transaction record
            envelope_txn = EnvelopeTransaction(
                envelope_id=envelope.envelope_id,
                envelope_type=EnvelopeType.BUDGET,
                allocation_id=allocation.allocation_id,
                transaction_date=allocation_date,
                transaction_type="allocation",
                amount=amount,
                balance_before=envelope.current_balance - amount,
                balance_after=envelope.current_balance,
                description=f"Monthly allocation - {period_label}"
            )
            self.envelope_transactions.append(envelope_txn)

        return allocations

    # -------------------------------------------------------------------------
    # VALIDATION - Prevent overspending
    # -------------------------------------------------------------------------

    def validate_allocation(
        self,
        bank_account_id: str,
        allocation_amount: float,
        current_bank_balance: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a budget allocation won't exceed available funds.

        Args:
            bank_account_id: Bank account to allocate from
            allocation_amount: Amount to allocate
            current_bank_balance: Current balance of bank account

        Returns:
            Tuple of (is_valid, error_message)

        Validation:
            Bank Balance >= Budget Allocated + Payment Reserved + New Allocation
        """
        # Calculate current allocations
        budget_allocated = self.get_total_budget_allocated()
        payment_reserved = self.get_total_payment_reserved()

        # Calculate available
        available = current_bank_balance - budget_allocated - payment_reserved

        # Validate
        if allocation_amount > available:
            error_msg = (
                f"Cannot allocate ${allocation_amount:.2f}. "
                f"Only ${available:.2f} available. "
                f"(Bank: ${current_bank_balance:.2f}, "
                f"Budget: ${budget_allocated:.2f}, "
                f"Payment: ${payment_reserved:.2f})"
            )
            return False, error_msg

        return True, None

    def validate_expense(
        self,
        budget_envelope_id: str,
        expense_amount: float,
        allow_overspend: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that an expense won't overspend the budget envelope.

        Args:
            budget_envelope_id: Envelope to charge
            expense_amount: Amount of expense
            allow_overspend: Whether to allow overspending

        Returns:
            Tuple of (is_valid, warning_message)
        """
        envelope = self.budget_envelopes.get(budget_envelope_id)
        if not envelope:
            return False, f"Budget envelope {budget_envelope_id} not found"

        if not allow_overspend and envelope.current_balance < expense_amount:
            shortage = expense_amount - envelope.current_balance
            warning = (
                f"Expense ${expense_amount:.2f} exceeds budget '{envelope.envelope_name}' "
                f"balance ${envelope.current_balance:.2f} by ${shortage:.2f}"
            )
            return False, warning

        return True, None

    # -------------------------------------------------------------------------
    # REPORTING - Calculate balances and breakdowns
    # -------------------------------------------------------------------------

    def get_bank_account_view(
        self,
        account_id: str,
        account_name: str,
        bank_balance: float,
        as_of_date: date
    ) -> BankAccountView:
        """
        Generate a complete view of bank balance with envelope breakdown.

        Shows:
        - Real bank balance
        - Virtual allocations (budgets + payments)
        - Available to allocate
        - Breakdown by envelope

        Args:
            account_id: Bank account ID
            account_name: Bank account name
            bank_balance: Current bank balance
            as_of_date: Date for the view

        Returns:
            BankAccountView with complete breakdown
        """
        # Calculate totals
        budget_allocated = self.get_total_budget_allocated()
        payment_reserved = self.get_total_payment_reserved()
        total_allocated = budget_allocated + payment_reserved
        available = bank_balance - total_allocated

        # Get envelope details
        budget_envelope_details = [
            {
                "envelope_id": env.envelope_id,
                "envelope_name": env.envelope_name,
                "balance": env.current_balance,
                "monthly_allocation": env.monthly_allocation,
                "spent_this_period": env.spent_this_period
            }
            for env in self.budget_envelopes.values()
            if env.current_balance != 0 or env.is_active
        ]

        payment_envelope_details = [
            {
                "envelope_id": env.envelope_id,
                "envelope_name": env.envelope_name,
                "balance": env.current_balance,
                "linked_account": env.linked_account_id
            }
            for env in self.payment_envelopes.values()
            if env.current_balance != 0 or env.is_active
        ]

        return BankAccountView(
            account_id=account_id,
            account_name=account_name,
            bank_balance=bank_balance,
            budget_allocated=budget_allocated,
            payment_reserved=payment_reserved,
            total_allocated=total_allocated,
            available_to_allocate=available,
            as_of_date=as_of_date,
            budget_envelopes=budget_envelope_details,
            payment_envelopes=payment_envelope_details
        )

    def get_total_budget_allocated(self) -> float:
        """Get sum of all budget envelope balances."""
        return sum(env.current_balance for env in self.budget_envelopes.values())

    def get_total_payment_reserved(self) -> float:
        """Get sum of all payment envelope balances."""
        return sum(env.current_balance for env in self.payment_envelopes.values())

    # -------------------------------------------------------------------------
    # FORECASTING - Calculate expected future balances
    # -------------------------------------------------------------------------

    def forecast_envelope_balance(
        self,
        envelope_id: str,
        target_date: date,
        scheduled_expenses: List[Dict]
    ) -> Dict:
        """
        Forecast a budget envelope balance on a future date.

        Takes current balance and applies:
        1. Monthly allocations between now and target date
        2. Scheduled/recurring expenses

        Args:
            envelope_id: Budget envelope to forecast
            target_date: Date to forecast to
            scheduled_expenses: List of scheduled expenses
                Each: {date, amount, description}

        Returns:
            Dict with forecast details
        """
        envelope = self.budget_envelopes.get(envelope_id)
        if not envelope:
            raise ValueError(f"Budget envelope {envelope_id} not found")

        current_balance = envelope.current_balance
        current_date = date.today()

        # Calculate number of months until target
        months_until_target = (
            (target_date.year - current_date.year) * 12 +
            (target_date.month - current_date.month)
        )

        # Apply monthly allocations
        if envelope.rollover_policy == RolloverPolicy.RESET:
            # Only the final month's allocation applies
            projected_balance = envelope.monthly_allocation
        elif envelope.rollover_policy == RolloverPolicy.ACCUMULATE:
            # Add all intervening allocations
            projected_balance = current_balance + (envelope.monthly_allocation * months_until_target)
        else:  # CAP
            # Add allocations up to cap
            projected_balance = min(
                current_balance + (envelope.monthly_allocation * months_until_target),
                envelope.rollover_cap or float('inf')
            )

        # Subtract scheduled expenses
        total_scheduled = sum(
            exp['amount'] for exp in scheduled_expenses
            if exp['date'] <= target_date
        )
        projected_balance -= total_scheduled

        return {
            "envelope_id": envelope_id,
            "envelope_name": envelope.envelope_name,
            "current_balance": current_balance,
            "as_of_date": current_date,
            "target_date": target_date,
            "months_until_target": months_until_target,
            "monthly_allocation": envelope.monthly_allocation,
            "rollover_policy": envelope.rollover_policy.value,
            "scheduled_expenses": total_scheduled,
            "projected_balance": projected_balance
        }

    # -------------------------------------------------------------------------
    # ENVELOPE MANAGEMENT - CRUD operations
    # -------------------------------------------------------------------------

    def create_budget_envelope(self, envelope: BudgetEnvelope) -> BudgetEnvelope:
        """Create a new budget envelope."""
        self.budget_envelopes[envelope.envelope_id] = envelope
        return envelope

    def create_payment_envelope(self, envelope: PaymentEnvelope) -> PaymentEnvelope:
        """Create a new payment envelope."""
        self.payment_envelopes[envelope.envelope_id] = envelope
        return envelope

    def get_budget_envelope(self, envelope_id: str) -> Optional[BudgetEnvelope]:
        """Get a budget envelope by ID."""
        return self.budget_envelopes.get(envelope_id)

    def get_payment_envelope(self, envelope_id: str) -> Optional[PaymentEnvelope]:
        """Get a payment envelope by ID."""
        return self.payment_envelopes.get(envelope_id)

    def list_budget_envelopes(self, active_only: bool = True) -> List[BudgetEnvelope]:
        """List all budget envelopes."""
        envelopes = list(self.budget_envelopes.values())
        if active_only:
            envelopes = [e for e in envelopes if e.is_active]
        return sorted(envelopes, key=lambda e: e.display_order)

    def list_payment_envelopes(self, active_only: bool = True) -> List[PaymentEnvelope]:
        """List all payment envelopes."""
        envelopes = list(self.payment_envelopes.values())
        if active_only:
            envelopes = [e for e in envelopes if e.is_active]
        return sorted(envelopes, key=lambda e: e.display_order)

    def update_budget_envelope(self, envelope: BudgetEnvelope) -> BudgetEnvelope:
        """Update an existing budget envelope."""
        if envelope.envelope_id not in self.budget_envelopes:
            raise ValueError(f"Budget envelope {envelope.envelope_id} not found")
        envelope.updated_at = datetime.utcnow()
        self.budget_envelopes[envelope.envelope_id] = envelope
        return envelope

    def update_payment_envelope(self, envelope: PaymentEnvelope) -> PaymentEnvelope:
        """Update an existing payment envelope."""
        if envelope.envelope_id not in self.payment_envelopes:
            raise ValueError(f"Payment envelope {envelope.envelope_id} not found")
        envelope.updated_at = datetime.utcnow()
        self.payment_envelopes[envelope.envelope_id] = envelope
        return envelope

    def delete_budget_envelope(self, envelope_id: str) -> None:
        """Delete a budget envelope."""
        if envelope_id not in self.budget_envelopes:
            raise ValueError(f"Budget envelope {envelope_id} not found")
        del self.budget_envelopes[envelope_id]

    def delete_payment_envelope(self, envelope_id: str) -> None:
        """Delete a payment envelope."""
        if envelope_id not in self.payment_envelopes:
            raise ValueError(f"Payment envelope {envelope_id} not found")
        del self.payment_envelopes[envelope_id]
