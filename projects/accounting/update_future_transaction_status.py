#!/usr/bin/env python3
"""
Update Future Transaction Status Script

Updates all transactions with future dates to have status='draft' instead of 'posted'.
Updates both test dataset files and the live API database.
"""

import json
import requests
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any

API_BASE_URL = "http://localhost:8000/api"


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json_file(file_path: Path, data: List[Dict[str, Any]]):
    """Save JSON file with formatting."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def is_future_date(date_str: str) -> bool:
    """Check if date string is in the future."""
    try:
        entry_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        return entry_date > date.today()
    except Exception as e:
        print(f"Error parsing date {date_str}: {e}")
        return False


def update_test_dataset(file_path: Path):
    """Update transaction status in test dataset file."""
    print(f"\nUpdating {file_path.name}...")

    data = load_json_file(file_path)
    updated_count = 0

    # Check if data is a dict with a 'journal_entries' key or a list
    if isinstance(data, dict):
        transactions = data.get('journal_entries', data.get('transactions', []))
    elif isinstance(data, list):
        transactions = data
    else:
        print(f"   ✗ Unknown data format")
        return

    for transaction in transactions:
        entry_date = transaction.get('entry_date')
        if entry_date and is_future_date(entry_date):
            if transaction.get('status') == 'posted':
                transaction['status'] = 'draft'
                # Clear posting_date for draft transactions
                transaction['posting_date'] = None
                updated_count += 1

    save_json_file(file_path, data)
    print(f"   Updated {updated_count} future transactions to draft status")
    print(f"   Total transactions in file: {len(transactions)}")


def update_live_database():
    """Update transaction status in live API database."""
    print(f"\nUpdating live database via API...")

    try:
        # Get all transactions
        response = requests.get(f"{API_BASE_URL}/journal-entries", params={"limit": 1000}, timeout=10)
        response.raise_for_status()
        transactions = response.json()

        print(f"   Found {len(transactions)} total transactions")

        updated_count = 0
        error_count = 0

        for transaction in transactions:
            entry_date = transaction.get('entry_date')
            journal_entry_id = transaction.get('journal_entry_id')

            if entry_date and is_future_date(entry_date) and transaction.get('status') == 'posted':
                try:
                    # Update transaction status to draft
                    update_payload = transaction.copy()
                    update_payload['status'] = 'draft'
                    update_payload['posting_date'] = None

                    update_response = requests.put(
                        f"{API_BASE_URL}/journal-entries/{journal_entry_id}",
                        json=update_payload,
                        timeout=5
                    )

                    if update_response.status_code == 200:
                        updated_count += 1
                        print(f"   ✓ Updated {journal_entry_id} ({entry_date})")
                    else:
                        error_count += 1
                        print(f"   ✗ Failed to update {journal_entry_id}: {update_response.status_code}")

                except Exception as e:
                    error_count += 1
                    print(f"   ✗ Error updating {journal_entry_id}: {e}")

        print(f"\n   Updated {updated_count} future transactions to draft status")
        if error_count > 0:
            print(f"   {error_count} errors occurred")

    except requests.exceptions.ConnectionError:
        print("   ✗ Could not connect to API server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"   ✗ Error: {e}")


def main():
    """Main function."""
    print("=" * 70)
    print("UPDATE FUTURE TRANSACTION STATUS")
    print("=" * 70)
    print("\nThis script will update all future-dated transactions from")
    print("status='posted' to status='draft' in both test datasets and")
    print("the live database.")
    print("\nRule: Transactions dated TODAY or in the PAST = posted")
    print("      Transactions dated in the FUTURE = draft")
    print("=" * 70)

    test_data_dir = Path(__file__).parent / "test_data"

    # Update test dataset files
    dataset_files = [
        test_data_dir / "recurring_expanded_2years.json",
        test_data_dir / "three_month_dataset.json",
    ]

    for file_path in dataset_files:
        if file_path.exists():
            update_test_dataset(file_path)
        else:
            print(f"\nSkipping {file_path.name} (file not found)")

    # Update live database
    update_live_database()

    print("\n" + "=" * 70)
    print("COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
