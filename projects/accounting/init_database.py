"""
Initialize Database with Schema and Test Data

This script creates the database tables and optionally loads test data.
Run this script before starting the API server for the first time.
"""

import sys
from pathlib import Path

# Add project root to path
limos_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(limos_root))
project_root = Path(__file__).parent

from projects.accounting.database.database import init_database, reset_database, get_db
from projects.accounting.database.repositories import (
    ChartOfAccountsRepository,
    BudgetEnvelopeRepository,
    PaymentEnvelopeRepository,
    RecurringJournalEntryRepository
)
from projects.accounting.models.journal_entries import ChartOfAccounts, RecurringJournalEntry
from projects.accounting.models.budget_envelopes import BudgetEnvelope, PaymentEnvelope
import json
import os


def load_test_data():
    """Load test data from JSON files into the database."""
    print("📥 Loading test data into database...")

    with get_db() as db:
        # Load chart of accounts
        coa_file = project_root / "test_data" / "envelope_test_data.json"
        if os.path.exists(coa_file):
            with open(coa_file, 'r') as f:
                data = json.load(f)

                # Load accounts
                for account_data in data.get('chart_of_accounts', []):
                    account = ChartOfAccounts(**account_data)
                    try:
                        ChartOfAccountsRepository.create(db, account)
                        print(f"  ✅ Created account: {account.account_name}")
                    except Exception as e:
                        print(f"  ⚠️  Account {account.account_name} already exists or error: {e}")

                # Load budget envelopes
                for env_data in data.get('budget_envelopes', []):
                    envelope = BudgetEnvelope(**env_data)
                    try:
                        BudgetEnvelopeRepository.create(db, envelope)
                        print(f"  ✅ Created budget envelope: {envelope.envelope_name}")
                    except Exception as e:
                        print(f"  ⚠️  Budget envelope {envelope.envelope_name} already exists or error: {e}")

                # Load payment envelopes
                for env_data in data.get('payment_envelopes', []):
                    envelope = PaymentEnvelope(**env_data)
                    try:
                        PaymentEnvelopeRepository.create(db, envelope)
                        print(f"  ✅ Created payment envelope: {envelope.envelope_name}")
                    except Exception as e:
                        print(f"  ⚠️  Payment envelope {envelope.envelope_name} already exists or error: {e}")

        # Load recurring templates
        templates_file = project_root / "test_data" / "recurring_templates.json"
        if os.path.exists(templates_file):
            with open(templates_file, 'r') as f:
                templates_data = json.load(f)
                for template_data in templates_data:
                    template = RecurringJournalEntry(**template_data)
                    try:
                        RecurringJournalEntryRepository.create(db, template)
                        print(f"  ✅ Created recurring template: {template.template_name}")
                    except Exception as e:
                        print(f"  ⚠️  Recurring template {template.template_name} already exists or error: {e}")

    print("✅ Test data loaded successfully!")


def main():
    """Main entry point for database initialization."""
    print("🚀 LiMOS Accounting - Database Initialization")
    print("=" * 60)

    # Check if user wants to reset
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("\n⚠️  WARNING: This will delete all existing data!")
        response = input("Are you sure you want to reset the database? (yes/no): ")
        if response.lower() == "yes":
            reset_database()
        else:
            print("❌ Reset cancelled")
            return
    else:
        # Initialize database (create tables if they don't exist)
        init_database()

    # Ask if user wants to load test data
    print("\n" + "=" * 60)
    response = input("Do you want to load test data? (yes/no): ")
    if response.lower() == "yes":
        load_test_data()
    else:
        print("ℹ️  Skipping test data load")

    print("\n" + "=" * 60)
    print("✅ Database initialization complete!")
    print("You can now start the API server with: python run_api_server.py")


if __name__ == "__main__":
    main()
