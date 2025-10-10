"""
Load comprehensive test data into the Accounting API for testing.

This script loads:
- Chart of Accounts (15 accounts)
- Budget Envelopes (8 envelopes)
- Payment Envelopes (3 envelopes)
- Recurring Templates (11 templates)
- Journal Entries (2 years of expanded transactions from recurring templates)
"""

import requests
import json
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api"

def load_json_file(filepath):
    """Load JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def main():
    """Load all test data."""
    test_data_dir = Path("/Users/ksd/Projects/LiMOS/projects/accounting/test_data")

    print("🚀 Loading comprehensive test data into API...")
    print(f"📁 Data directory: {test_data_dir}")
    print(f"🌐 API URL: {API_BASE_URL}\n")

    # Check API health
    try:
        response = requests.get("http://localhost:8000/health")
        health = response.json()
        print(f"✅ API Health Check:")
        print(f"   Status: {health['status']}")
        print(f"   Chart of Accounts: {health['data_loaded']['chart_of_accounts']}")
        print(f"   Budget Envelopes: {health['data_loaded']['budget_envelopes']}")
        print(f"   Payment Envelopes: {health['data_loaded']['payment_envelopes']}")
        print(f"   Recurring Templates: {health['data_loaded']['recurring_templates']}")
        print(f"   Journal Entries: {health['data_loaded']['journal_entries']}\n")
    except Exception as e:
        print(f"❌ Error: Could not connect to API at {API_BASE_URL}")
        print(f"   Make sure the API server is running: python run_api_server.py")
        sys.exit(1)

    # Load expanded recurring transactions (2 years of data)
    print("📥 Loading 2-year transaction dataset...")
    transactions_file = test_data_dir / "recurring_expanded_2years.json"

    if not transactions_file.exists():
        print(f"❌ Error: {transactions_file} not found")
        sys.exit(1)

    transactions = load_json_file(transactions_file)
    print(f"   Found {len(transactions)} transactions to load")

    # Post all transactions
    posted_count = 0
    draft_count = 0
    error_count = 0

    for i, transaction in enumerate(transactions, 1):
        try:
            # Post transaction to API
            response = requests.post(
                f"{API_BASE_URL}/journal-entries",
                json=transaction,
                timeout=5
            )

            if response.status_code == 201:
                if transaction.get('status') == 'posted':
                    posted_count += 1
                else:
                    draft_count += 1

                # Print progress every 50 transactions
                if i % 50 == 0:
                    print(f"   Progress: {i}/{len(transactions)} transactions loaded...")
            else:
                error_count += 1
                if error_count < 5:  # Only show first few errors
                    print(f"   ⚠️  Warning: Transaction {i} failed (status {response.status_code})")

        except requests.exceptions.Timeout:
            error_count += 1
            if error_count < 5:
                print(f"   ⚠️  Warning: Transaction {i} timed out")
        except Exception as e:
            error_count += 1
            if error_count < 5:
                print(f"   ⚠️  Warning: Transaction {i} error: {str(e)}")

    print(f"\n✅ Data loading complete!")
    print(f"\n📊 Summary:")
    print(f"   ✅ Posted transactions: {posted_count}")
    print(f"   📝 Draft transactions: {draft_count}")
    if error_count > 0:
        print(f"   ⚠️  Errors: {error_count}")
    print(f"   📈 Total loaded: {posted_count + draft_count}")

    # Final health check
    print(f"\n🔍 Final health check:")
    response = requests.get("http://localhost:8000/health")
    health = response.json()
    print(f"   Chart of Accounts: {health['data_loaded']['chart_of_accounts']}")
    print(f"   Budget Envelopes: {health['data_loaded']['budget_envelopes']}")
    print(f"   Payment Envelopes: {health['data_loaded']['payment_envelopes']}")
    print(f"   Recurring Templates: {health['data_loaded']['recurring_templates']}")
    print(f"   Journal Entries: {health['data_loaded']['journal_entries']}")

    print(f"\n✨ Test data is ready! You can now test the Web UI at http://localhost:5173")

if __name__ == "__main__":
    main()
