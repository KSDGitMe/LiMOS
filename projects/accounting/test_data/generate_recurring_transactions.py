"""
Generate Recurring Transaction Templates and Expand for 2 Years

Creates realistic recurring transactions including:
- Biweekly salary
- Monthly mortgage (principal + interest)
- Monthly utilities
- Quarterly property tax
- Annual home insurance
- Bimonthly auto loan payment
- Monthly credit card payments

Then expands all templates for 2 years (2025-2026) for forecasting.
"""

import json
import sys
from datetime import date
from typing import List, Dict

# Add project root to path
sys.path.insert(0, '/Users/ksd/Projects/LiMOS')

from projects.accounting.models.journal_entries import (
    RecurringJournalEntry,
    RecurrenceFrequency,
    AccountType
)
from projects.accounting.services.recurring_transaction_service import (
    RecurringTransactionService
)


def create_recurring_templates() -> List[Dict]:
    """Create recurring journal entry templates."""

    templates = [
        # ================================================================
        # INCOME - Biweekly Salary
        # ================================================================
        {
            "recurring_entry_id": "rec-salary-biweekly",
            "template_name": "Salary - Biweekly Paycheck",
            "description": "Biweekly salary deposit",
            "frequency": "biweekly",
            "interval": 1,
            "start_date": "2025-01-03",  # First Friday
            "day_of_month": None,
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "5000",
                    "account_type": "revenue",
                    "flow_direction": "from",
                    "amount": 3500.00,
                    "multiplier": 1,
                    "description": "Salary income"
                },
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "to",
                    "amount": 3500.00,
                    "multiplier": 1,
                    "description": "Deposit to checking"
                }
            ]
        },

        # ================================================================
        # HOUSING - Monthly Mortgage Payment
        # ================================================================
        {
            "recurring_entry_id": "rec-mortgage-monthly",
            "template_name": "Mortgage Payment",
            "description": "Monthly mortgage payment (principal + interest)",
            "frequency": "monthly",
            "interval": 1,
            "day_of_month": 1,
            "start_date": "2025-01-01",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 1439.00,
                    "multiplier": -1,
                    "description": "Mortgage payment from checking"
                },
                {
                    "account_id": "2200",
                    "account_type": "liability",
                    "flow_direction": "to",
                    "amount": 766.00,
                    "multiplier": -1,
                    "description": "Mortgage principal reduction"
                },
                {
                    "account_id": "6000",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 673.00,
                    "multiplier": 1,
                    "description": "Mortgage interest expense (2.1% APR)"
                }
            ]
        },

        # ================================================================
        # HOUSING - Property Tax (Quarterly)
        # ================================================================
        {
            "recurring_entry_id": "rec-property-tax-quarterly",
            "template_name": "Property Tax Payment",
            "description": "Quarterly property tax payment",
            "frequency": "quarterly",
            "interval": 1,
            "day_of_month": 15,
            "start_date": "2025-01-15",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 1250.00,
                    "multiplier": -1,
                    "description": "Property tax payment"
                },
                {
                    "account_id": "6100",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 1250.00,
                    "multiplier": 1,
                    "description": "Property tax expense"
                }
            ]
        },

        # ================================================================
        # HOUSING - Home Insurance (Annual)
        # ================================================================
        {
            "recurring_entry_id": "rec-home-insurance-annual",
            "template_name": "Home Insurance Premium",
            "description": "Annual home insurance premium",
            "frequency": "annually",
            "interval": 1,
            "day_of_month": 1,
            "month_of_year": 3,  # March 1st
            "start_date": "2025-03-01",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 1800.00,
                    "multiplier": -1,
                    "description": "Home insurance payment"
                },
                {
                    "account_id": "6110",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 1800.00,
                    "multiplier": 1,
                    "description": "Home insurance expense"
                }
            ]
        },

        # ================================================================
        # UTILITIES - Electric Bill (Monthly)
        # ================================================================
        {
            "recurring_entry_id": "rec-electric-monthly",
            "template_name": "Electric Utility Bill",
            "description": "Monthly electric utility payment",
            "frequency": "monthly",
            "interval": 1,
            "day_of_month": 10,
            "start_date": "2025-01-10",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 185.00,
                    "multiplier": -1,
                    "description": "Electric bill payment"
                },
                {
                    "account_id": "6200",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 185.00,
                    "multiplier": 1,
                    "description": "Electric utility expense"
                }
            ]
        },

        # ================================================================
        # UTILITIES - Gas Bill (Monthly)
        # ================================================================
        {
            "recurring_entry_id": "rec-gas-monthly",
            "template_name": "Gas Utility Bill",
            "description": "Monthly gas utility payment",
            "frequency": "monthly",
            "interval": 1,
            "day_of_month": 15,
            "start_date": "2025-01-15",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 95.00,
                    "multiplier": -1,
                    "description": "Gas bill payment"
                },
                {
                    "account_id": "6210",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 95.00,
                    "multiplier": 1,
                    "description": "Gas utility expense"
                }
            ]
        },

        # ================================================================
        # UTILITIES - Internet/Cable (Monthly)
        # ================================================================
        {
            "recurring_entry_id": "rec-internet-monthly",
            "template_name": "Internet & Cable Bill",
            "description": "Monthly internet and cable payment",
            "frequency": "monthly",
            "interval": 1,
            "day_of_month": 20,
            "start_date": "2025-01-20",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 120.00,
                    "multiplier": -1,
                    "description": "Internet/cable payment"
                },
                {
                    "account_id": "6220",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 120.00,
                    "multiplier": 1,
                    "description": "Internet/cable expense"
                }
            ]
        },

        # ================================================================
        # AUTO - Auto Loan Payment (Monthly)
        # ================================================================
        {
            "recurring_entry_id": "rec-auto-loan-monthly",
            "template_name": "Auto Loan Payment",
            "description": "Monthly auto loan payment (principal + interest)",
            "frequency": "monthly",
            "interval": 1,
            "day_of_month": 5,
            "start_date": "2025-01-05",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 425.00,
                    "multiplier": -1,
                    "description": "Auto loan payment from checking"
                },
                {
                    "account_id": "2300",
                    "account_type": "liability",
                    "flow_direction": "to",
                    "amount": 375.00,
                    "multiplier": -1,
                    "description": "Auto loan principal reduction",
                    "payment_envelope_id": "1620"
                },
                {
                    "account_id": "6410",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 50.00,
                    "multiplier": 1,
                    "description": "Auto loan interest expense (3.2% APR)"
                }
            ]
        },

        # ================================================================
        # AUTO - Auto Insurance (Semiannual)
        # ================================================================
        {
            "recurring_entry_id": "rec-auto-insurance-semiannual",
            "template_name": "Auto Insurance Premium",
            "description": "Semiannual auto insurance premium",
            "frequency": "semiannually",
            "interval": 1,
            "day_of_month": 1,
            "start_date": "2025-01-01",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 650.00,
                    "multiplier": -1,
                    "description": "Auto insurance payment"
                },
                {
                    "account_id": "6420",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 650.00,
                    "multiplier": 1,
                    "description": "Auto insurance expense"
                }
            ]
        },

        # ================================================================
        # CREDIT CARDS - Credit Card A Payment (Monthly)
        # ================================================================
        {
            "recurring_entry_id": "rec-cc-a-payment-monthly",
            "template_name": "Credit Card A - Monthly Payment",
            "description": "Monthly payment to Credit Card A",
            "frequency": "monthly",
            "interval": 1,
            "day_of_month": 25,
            "start_date": "2025-01-25",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 500.00,
                    "multiplier": -1,
                    "description": "Payment to Credit Card A"
                },
                {
                    "account_id": "2100",
                    "account_type": "liability",
                    "flow_direction": "to",
                    "amount": 500.00,
                    "multiplier": -1,
                    "description": "Credit Card A payment",
                    "payment_envelope_id": "1600"
                }
            ]
        },

        # ================================================================
        # SUBSCRIPTIONS - Streaming Services (Monthly)
        # ================================================================
        {
            "recurring_entry_id": "rec-streaming-monthly",
            "template_name": "Streaming Services",
            "description": "Monthly streaming service subscriptions",
            "frequency": "monthly",
            "interval": 1,
            "day_of_month": 1,
            "start_date": "2025-01-01",
            "auto_post": True,
            "is_active": True,
            "distribution_template": [
                {
                    "account_id": "2100",
                    "account_type": "liability",
                    "flow_direction": "from",
                    "amount": 45.00,
                    "multiplier": 1,
                    "description": "Streaming subscriptions charged to CC",
                    "payment_envelope_id": "1600"
                },
                {
                    "account_id": "6500",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 45.00,
                    "multiplier": 1,
                    "description": "Entertainment - Streaming",
                    "budget_envelope_id": "1530"
                }
            ]
        }
    ]

    return templates


def main():
    """Generate recurring transactions and expand for 2 years."""
    print("=" * 80)
    print("Generating Recurring Transaction Templates")
    print("=" * 80)

    # Create templates
    templates_data = create_recurring_templates()
    print(f"\n✅ Created {len(templates_data)} recurring transaction templates")

    # Convert to model objects
    from projects.accounting.models.journal_entries import RecurringJournalEntry
    templates = []
    for template_data in templates_data:
        template = RecurringJournalEntry(**template_data)
        templates.append(template)

    # Print template summary
    print(f"\n📋 Template Summary:")
    for template in templates:
        print(f"   • {template.template_name:45} {template.frequency.value:15} "
              f"starting {template.start_date}")

    # Expand for 2 years (2025-2026)
    print(f"\n" + "=" * 80)
    print("Expanding Templates for 2 Years (2025-01-01 to 2026-12-31)")
    print("=" * 80)

    service = RecurringTransactionService()
    expanded_entries = service.expand_recurring_entries(
        recurring_templates=templates,
        start_date=date(2025, 1, 1),
        end_date=date(2026, 12, 31),
        auto_post=True
    )

    print(f"\n✅ Generated {len(expanded_entries)} journal entries")

    # Count by type
    from collections import Counter
    by_template = Counter(entry.recurring_entry_id for entry in expanded_entries)

    print(f"\n📊 Entries by Template:")
    for template in templates:
        count = by_template[template.recurring_entry_id]
        print(f"   • {template.template_name:45} {count:3} occurrences")

    # Save templates to JSON
    templates_json = [
        {
            "recurring_entry_id": t.recurring_entry_id,
            "template_name": t.template_name,
            "description": t.description,
            "frequency": t.frequency.value,
            "interval": t.interval,
            "day_of_month": t.day_of_month,
            "day_of_week": t.day_of_week,
            "month_of_quarter": t.month_of_quarter,
            "month_of_year": t.month_of_year,
            "start_date": t.start_date.isoformat(),
            "end_date": t.end_date.isoformat() if t.end_date else None,
            "auto_post": t.auto_post,
            "is_active": t.is_active,
            "distribution_template": t.distribution_template
        }
        for t in templates
    ]

    templates_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/recurring_templates.json"
    with open(templates_file, 'w') as f:
        json.dump(templates_json, f, indent=2)
    print(f"\n💾 Saved templates to: {templates_file}")

    # Convert expanded entries to JSON
    expanded_json = []
    for entry in expanded_entries:
        entry_dict = {
            "journal_entry_id": entry.journal_entry_id,
            "entry_number": entry.entry_number,
            "entry_date": entry.entry_date.isoformat(),
            "posting_date": entry.posting_date.isoformat() if entry.posting_date else None,
            "description": entry.description,
            "entry_type": entry.entry_type.value,
            "status": entry.status.value,
            "recurring_entry_id": entry.recurring_entry_id,
            "distributions": [
                {
                    "distribution_id": d.distribution_id,
                    "account_id": d.account_id,
                    "account_type": d.account_type.value,
                    "flow_direction": d.flow_direction.value,
                    "amount": d.amount,
                    "multiplier": d.multiplier,
                    "debit_credit": d.debit_credit.value,
                    "description": d.description,
                    "budget_envelope_id": d.budget_envelope_id,
                    "payment_envelope_id": d.payment_envelope_id
                }
                for d in entry.distributions
            ]
        }
        expanded_json.append(entry_dict)

    # Save expanded entries
    expanded_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/recurring_expanded_2years.json"
    with open(expanded_file, 'w') as f:
        json.dump(expanded_json, f, indent=2)
    print(f"💾 Saved expanded entries to: {expanded_file}")

    # Show date range and samples
    print(f"\n📅 Date Range:")
    print(f"   First entry: {expanded_entries[0].entry_date}")
    print(f"   Last entry:  {expanded_entries[-1].entry_date}")

    print(f"\n📝 Sample Entries (first 10):")
    for entry in expanded_entries[:10]:
        print(f"   {entry.entry_date} | {entry.description[:60]:60} | "
              f"${sum(d.amount for d in entry.distributions if d.flow_direction.value == 'from'):>10,.2f}")

    # Calculate summary statistics
    total_income = sum(
        d.amount for entry in expanded_entries
        for d in entry.distributions
        if d.account_type.value == "revenue"
    )

    total_expenses = sum(
        d.amount for entry in expanded_entries
        for d in entry.distributions
        if d.account_type.value == "expense"
    )

    print(f"\n💰 2-Year Summary:")
    print(f"   Total Income:   ${total_income:>12,.2f}")
    print(f"   Total Expenses: ${total_expenses:>12,.2f}")
    print(f"   Net:            ${total_income - total_expenses:>12,.2f}")

    print(f"\n✅ Recurring transaction generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
