"""
Recurring Transaction Service

Expands recurring journal entry templates into actual journal entries
for forecasting and automated transaction creation.
"""

from datetime import date, timedelta
from typing import List, Optional, Dict
from calendar import monthrange

# Handle relativedelta import
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # Fallback implementation for month/year arithmetic
    class relativedelta:
        def __init__(self, months=0, years=0):
            self.months = months
            self.years = years

        def __radd__(self, other):
            if isinstance(other, date):
                # Add years
                new_year = other.year + self.years
                # Add months
                new_month = other.month + self.months
                while new_month > 12:
                    new_month -= 12
                    new_year += 1
                while new_month < 1:
                    new_month += 12
                    new_year -= 1
                # Handle day overflow
                max_day = monthrange(new_year, new_month)[1]
                new_day = min(other.day, max_day)
                return date(new_year, new_month, new_day)
            return NotImplemented

from ..models.journal_entries import (
    RecurringJournalEntry,
    JournalEntry,
    Distribution,
    RecurrenceFrequency,
    JournalEntryType,
    JournalEntryStatus,
    AccountType,
    FlowDirection
)


class RecurringTransactionService:
    """
    Service for expanding recurring transaction templates into actual transactions.

    Handles all recurrence patterns: daily, weekly, biweekly, monthly, quarterly,
    semiannually, and annually.
    """

    def __init__(self):
        """Initialize the recurring transaction service."""
        pass

    def expand_recurring_entries(
        self,
        recurring_templates: List[RecurringJournalEntry],
        start_date: date,
        end_date: date,
        auto_post: bool = False
    ) -> List[JournalEntry]:
        """
        Expand all recurring templates into journal entries for date range.

        Args:
            recurring_templates: List of recurring journal entry templates
            start_date: Start date for expansion
            end_date: End date for expansion
            auto_post: Whether to mark generated entries as POSTED

        Returns:
            List of generated journal entries sorted by entry_date
        """
        all_entries = []

        for template in recurring_templates:
            if not template.is_active:
                continue

            entries = self.expand_single_template(
                template=template,
                start_date=start_date,
                end_date=end_date,
                auto_post=auto_post
            )
            all_entries.extend(entries)

        # Sort by entry date
        all_entries.sort(key=lambda e: e.entry_date)

        return all_entries

    def expand_single_template(
        self,
        template: RecurringJournalEntry,
        start_date: date,
        end_date: date,
        auto_post: bool = False
    ) -> List[JournalEntry]:
        """
        Expand a single recurring template into journal entries.

        Args:
            template: Recurring journal entry template
            start_date: Start date for expansion
            end_date: End date for expansion
            auto_post: Whether to mark generated entries as POSTED

        Returns:
            List of generated journal entries
        """
        # Calculate occurrence dates
        occurrence_dates = self.calculate_occurrence_dates(
            template=template,
            start_date=start_date,
            end_date=end_date
        )

        # Generate journal entries for each occurrence
        entries = []
        for occurrence_date in occurrence_dates:
            entry = self.create_journal_entry_from_template(
                template=template,
                occurrence_date=occurrence_date,
                auto_post=auto_post or template.auto_post
            )
            entries.append(entry)

        return entries

    def calculate_occurrence_dates(
        self,
        template: RecurringJournalEntry,
        start_date: date,
        end_date: date
    ) -> List[date]:
        """
        Calculate all occurrence dates for a recurring template within date range.

        Args:
            template: Recurring journal entry template
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of occurrence dates
        """
        occurrence_dates = []

        # Start from template start_date or range start_date, whichever is later
        current_date = max(template.start_date, start_date)

        # End at template end_date or range end_date, whichever is earlier
        final_date = end_date
        if template.end_date:
            final_date = min(template.end_date, end_date)

        occurrence_count = 0

        while current_date <= final_date:
            # Check if we've hit occurrence limit
            if template.end_after_occurrences:
                if occurrence_count >= template.end_after_occurrences:
                    break

            # Add this occurrence
            occurrence_dates.append(current_date)
            occurrence_count += 1

            # Calculate next occurrence
            current_date = self.calculate_next_occurrence(
                current_date=current_date,
                frequency=template.frequency,
                interval=template.interval,
                day_of_month=template.day_of_month,
                day_of_week=template.day_of_week,
                month_of_quarter=template.month_of_quarter,
                month_of_year=template.month_of_year
            )

        return occurrence_dates

    def calculate_next_occurrence(
        self,
        current_date: date,
        frequency: RecurrenceFrequency,
        interval: int = 1,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None,
        month_of_quarter: Optional[int] = None,
        month_of_year: Optional[int] = None
    ) -> date:
        """
        Calculate the next occurrence date from the current date.

        Args:
            current_date: Current occurrence date
            frequency: Recurrence frequency
            interval: Number of periods between occurrences
            day_of_month: Specific day of month (1-31)
            day_of_week: Specific day of week (0=Monday, 6=Sunday)
            month_of_quarter: Month within quarter (1-3)
            month_of_year: Specific month (1-12)

        Returns:
            Next occurrence date
        """
        if frequency == RecurrenceFrequency.DAILY:
            return current_date + timedelta(days=interval)

        elif frequency == RecurrenceFrequency.WEEKLY:
            return current_date + timedelta(weeks=interval)

        elif frequency == RecurrenceFrequency.BIWEEKLY:
            return current_date + timedelta(weeks=2 * interval)

        elif frequency == RecurrenceFrequency.MONTHLY:
            next_date = current_date + relativedelta(months=interval)
            if day_of_month:
                # Adjust to specific day of month
                next_date = next_date.replace(day=min(day_of_month, monthrange(next_date.year, next_date.month)[1]))
            return next_date

        elif frequency == RecurrenceFrequency.QUARTERLY:
            next_date = current_date + relativedelta(months=3 * interval)
            if day_of_month:
                next_date = next_date.replace(day=min(day_of_month, monthrange(next_date.year, next_date.month)[1]))
            return next_date

        elif frequency == RecurrenceFrequency.SEMIANNUALLY:
            next_date = current_date + relativedelta(months=6 * interval)
            if day_of_month:
                next_date = next_date.replace(day=min(day_of_month, monthrange(next_date.year, next_date.month)[1]))
            return next_date

        elif frequency == RecurrenceFrequency.ANNUALLY:
            next_date = current_date + relativedelta(years=interval)
            if month_of_year:
                next_date = next_date.replace(month=month_of_year)
            if day_of_month:
                next_date = next_date.replace(day=min(day_of_month, monthrange(next_date.year, next_date.month)[1]))
            return next_date

        else:
            raise ValueError(f"Unsupported frequency: {frequency}")

    def create_journal_entry_from_template(
        self,
        template: RecurringJournalEntry,
        occurrence_date: date,
        auto_post: bool = False
    ) -> JournalEntry:
        """
        Create a journal entry from a recurring template for a specific date.

        Args:
            template: Recurring journal entry template
            occurrence_date: Date for this occurrence
            auto_post: Whether to mark as POSTED

        Returns:
            Generated journal entry
        """
        # Create distributions from template
        distributions = []
        for dist_template in template.distribution_template:
            account_type = AccountType(dist_template['account_type'])
            flow_direction = FlowDirection(dist_template['flow_direction'])

            # Calculate multiplier if not provided
            multiplier = dist_template.get('multiplier', Distribution.calculate_multiplier(
                account_type, flow_direction
            ))

            # Calculate debit_credit indicator
            from ..models.journal_entries import DebitCredit
            if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                # Normal debit balance accounts
                debit_credit = DebitCredit.DEBIT if multiplier == 1 else DebitCredit.CREDIT
            else:
                # Normal credit balance accounts (LIABILITY, EQUITY, REVENUE)
                debit_credit = DebitCredit.CREDIT if multiplier == 1 else DebitCredit.DEBIT

            distribution = Distribution(
                account_id=dist_template['account_id'],
                account_type=account_type,
                flow_direction=flow_direction,
                amount=dist_template['amount'],
                multiplier=multiplier,
                debit_credit=debit_credit,
                description=dist_template.get('description'),
                budget_envelope_id=dist_template.get('budget_envelope_id'),
                payment_envelope_id=dist_template.get('payment_envelope_id'),
                reference_id=dist_template.get('reference_id')
            )
            distributions.append(distribution)

        # Determine status based on occurrence date
        # Posted if today or in the past, Draft if future
        today = date.today()
        is_posted = occurrence_date <= today

        # Create journal entry
        entry = JournalEntry(
            entry_date=occurrence_date,
            posting_date=occurrence_date if is_posted else None,
            description=template.description,
            distributions=distributions,
            entry_type=JournalEntryType.RECURRING,
            status=JournalEntryStatus.POSTED if is_posted else JournalEntryStatus.DRAFT,
            recurring_entry_id=template.recurring_entry_id,
            notes=f"Auto-generated from template: {template.template_name}",
            tags=template.tags
        )

        return entry

    def calculate_next_occurrence_from_template(
        self,
        template: RecurringJournalEntry
    ) -> Optional[date]:
        """
        Calculate the next occurrence date for a recurring template.

        Uses last_generated_date if available, otherwise uses start_date.

        Args:
            template: Recurring journal entry template

        Returns:
            Next occurrence date, or None if template has ended
        """
        # Determine starting point
        if template.last_generated_date:
            base_date = template.last_generated_date
        else:
            base_date = template.start_date

        # Calculate next occurrence
        next_date = self.calculate_next_occurrence(
            current_date=base_date,
            frequency=template.frequency,
            interval=template.interval,
            day_of_month=template.day_of_month,
            day_of_week=template.day_of_week,
            month_of_quarter=template.month_of_quarter,
            month_of_year=template.month_of_year
        )

        # Check if we've exceeded end conditions
        if template.end_date and next_date > template.end_date:
            return None

        if template.end_after_occurrences:
            if template.total_generated >= template.end_after_occurrences:
                return None

        return next_date

    def get_upcoming_occurrences(
        self,
        template: RecurringJournalEntry,
        days_ahead: int = 30
    ) -> List[date]:
        """
        Get upcoming occurrence dates for a template.

        Args:
            template: Recurring journal entry template
            days_ahead: Number of days to look ahead

        Returns:
            List of upcoming occurrence dates
        """
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        return self.calculate_occurrence_dates(
            template=template,
            start_date=today,
            end_date=end_date
        )
