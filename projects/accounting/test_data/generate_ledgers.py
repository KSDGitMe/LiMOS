"""
Generate Account Ledgers and Monthly Account Balances

Reads the transaction dataset and creates:
1. AccountLedger entries (transaction-by-transaction detail)
2. AccountBalance summaries (monthly summaries per account)
"""

import json
from datetime import datetime, date
from collections import defaultdict
from typing import Dict, List

# Import models
import sys
sys.path.append('/Users/ksd/Projects/LiMOS')

from projects.accounting.models.journal_entries import (
    AccountType,
    FlowDirection,
    DebitCredit
)


def load_dataset(file_path: str) -> Dict:
    """Load the transaction dataset."""
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_account_ledgers(dataset: Dict) -> List[Dict]:
    """
    Generate AccountLedger entries from transactions.

    Each distribution creates one ledger entry showing the running balance.
    """
    ledger_entries = []
    account_balances = {}  # Track current balance per account

    # Initialize account balances with opening balances
    for account in dataset['chart_of_accounts']:
        account_balances[account['account_id']] = account['opening_balance']

    # Sort transactions by date
    transactions = sorted(dataset['transactions'], key=lambda x: x['entry_date'])

    # Process each transaction
    for txn in transactions:
        # Process each distribution in the transaction
        for dist in txn['distributions']:
            account_id = dist['account_id']

            # Get account info from chart of accounts
            account_info = next(
                (acc for acc in dataset['chart_of_accounts'] if acc['account_id'] == account_id),
                None
            )

            if not account_info:
                print(f"Warning: Account {account_id} not found in chart of accounts")
                continue

            # Get current balance
            balance_before = account_balances.get(account_id, 0.0)

            # Calculate balance impact
            balance_impact = dist['amount'] * dist['multiplier']
            balance_after = balance_before + balance_impact

            # Calculate debit/credit indicator
            account_type = AccountType(dist['account_type'])
            multiplier = dist['multiplier']

            # Determine Dr/Cr based on account type and multiplier
            if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                debit_credit = 'Dr' if multiplier == 1 else 'Cr'
            else:
                debit_credit = 'Cr' if multiplier == 1 else 'Dr'

            # Determine debit/credit amounts
            if debit_credit == 'Dr':
                debit_amount = dist['amount']
                credit_amount = 0.0
            else:
                debit_amount = 0.0
                credit_amount = dist['amount']

            # Create ledger entry
            ledger_entry = {
                "ledger_entry_id": f"ledger-{txn['journal_entry_id']}-{dist.get('distribution_id', len(ledger_entries))}",
                "account_id": account_id,
                "account_number": account_info['account_number'],
                "account_name": account_info['account_name'],
                "account_type": dist['account_type'],
                "journal_entry_id": txn['journal_entry_id'],
                "distribution_id": dist.get('distribution_id', f"dist-{len(ledger_entries)}"),
                "entry_number": txn['entry_number'],
                "transaction_date": txn['entry_date'],
                "posting_date": txn.get('posting_date', txn['entry_date']),
                "description": dist.get('description', txn['description']),
                "reference": dist.get('reference_id'),
                "flow_direction": dist['flow_direction'],
                "amount": dist['amount'],
                "debit_credit": debit_credit,
                "debit_amount": debit_amount,
                "credit_amount": credit_amount,
                "multiplier": dist['multiplier'],
                "balance_impact": balance_impact,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "posted_at": txn.get('created_at', datetime.utcnow().isoformat()),
                "created_at": txn.get('created_at', datetime.utcnow().isoformat())
            }

            ledger_entries.append(ledger_entry)

            # Update running balance
            account_balances[account_id] = balance_after

    return ledger_entries


def generate_monthly_balances(dataset: Dict, ledger_entries: List[Dict]) -> List[Dict]:
    """
    Generate monthly AccountBalance summaries.

    Creates one AccountBalance record per account per month.
    """
    monthly_balances = []

    # Group ledger entries by account and month
    by_account_month = defaultdict(list)

    for entry in ledger_entries:
        account_id = entry['account_id']
        txn_date = date.fromisoformat(entry['transaction_date'])
        month_key = f"{txn_date.year}-{txn_date.month:02d}"
        by_account_month[(account_id, month_key)].append(entry)

    # Generate monthly summary for each account/month combination
    for (account_id, month_key), entries in sorted(by_account_month.items()):
        if not entries:
            continue

        # Get account info
        account_info = next(
            (acc for acc in dataset['chart_of_accounts'] if acc['account_id'] == account_id),
            None
        )

        if not account_info:
            continue

        # Sort entries by date
        entries = sorted(entries, key=lambda x: x['transaction_date'])

        # Parse month
        year, month = map(int, month_key.split('-'))

        # Determine period dates
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year, 12, 31)
        else:
            next_month = date(year, month + 1, 1)
            period_end = date(year, month, (next_month - timedelta(days=1)).day)

        # Get opening balance (balance_before of first entry)
        opening_balance = entries[0]['balance_before']

        # Get closing balance (balance_after of last entry)
        closing_balance = entries[-1]['balance_after']

        # Calculate totals
        total_from_amount = sum(e['amount'] for e in entries if e['flow_direction'] == 'from')
        total_to_amount = sum(e['amount'] for e in entries if e['flow_direction'] == 'to')
        total_debits = sum(e['debit_amount'] for e in entries)
        total_credits = sum(e['credit_amount'] for e in entries)
        net_change = closing_balance - opening_balance
        transaction_count = len(entries)

        # Create monthly balance record
        balance_record = {
            "balance_id": f"bal-{account_id}-{month_key}",
            "account_id": account_id,
            "account_number": account_info['account_number'],
            "account_name": account_info['account_name'],
            "account_type": account_info['account_type'],
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "period_label": month_key,
            "opening_balance": round(opening_balance, 2),
            "opening_balance_date": period_start.isoformat(),
            "total_from_amount": round(total_from_amount, 2),
            "total_to_amount": round(total_to_amount, 2),
            "transaction_count": transaction_count,
            "total_debits": round(total_debits, 2),
            "total_credits": round(total_credits, 2),
            "net_change": round(net_change, 2),
            "closing_balance": round(closing_balance, 2),
            "is_reconciled": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        monthly_balances.append(balance_record)

    return sorted(monthly_balances, key=lambda x: (x['period_label'], x['account_number']))


def generate_summary_report(monthly_balances: List[Dict]) -> Dict:
    """Generate a summary report of all monthly balances."""
    summary = {
        "total_account_months": len(monthly_balances),
        "months": ["2025-01", "2025-02", "2025-03"],
        "accounts_tracked": len(set(b['account_id'] for b in monthly_balances)),
        "by_month": {}
    }

    for month in summary["months"]:
        month_records = [b for b in monthly_balances if b['period_label'] == month]
        summary["by_month"][month] = {
            "accounts": len(month_records),
            "total_transactions": sum(b['transaction_count'] for b in month_records),
            "total_debits": sum(b['total_debits'] for b in month_records),
            "total_credits": sum(b['total_credits'] for b in month_records)
        }

    return summary


def main():
    """Main execution."""
    print("Generating Account Ledgers and Monthly Balances...")

    # Load dataset
    dataset_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/three_month_dataset.json"
    dataset = load_dataset(dataset_file)

    print(f"\n📊 Processing {len(dataset['transactions'])} transactions...")

    # Generate account ledgers
    print("\n🔄 Generating account ledger entries...")
    ledger_entries = generate_account_ledgers(dataset)
    print(f"   ✅ Created {len(ledger_entries)} ledger entries")

    # Generate monthly balances
    print("\n📅 Generating monthly account balances...")
    monthly_balances = generate_monthly_balances(dataset, ledger_entries)
    print(f"   ✅ Created {len(monthly_balances)} monthly balance records")

    # Generate summary
    summary = generate_summary_report(monthly_balances)

    # Save ledger entries
    ledger_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/account_ledgers.json"
    with open(ledger_file, 'w') as f:
        json.dump(ledger_entries, f, indent=2)
    print(f"\n💾 Saved ledger entries to: {ledger_file}")

    # Save monthly balances
    balances_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/monthly_balances.json"
    with open(balances_file, 'w') as f:
        json.dump(monthly_balances, f, indent=2)
    print(f"💾 Saved monthly balances to: {balances_file}")

    # Save summary
    summary_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/ledger_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"💾 Saved summary to: {summary_file}")

    # Print summary
    print(f"\n📈 Summary Report:")
    print(f"   Total Account-Months: {summary['total_account_months']}")
    print(f"   Accounts Tracked: {summary['accounts_tracked']}")
    print(f"\n   By Month:")
    for month, stats in summary['by_month'].items():
        print(f"   {month}:")
        print(f"      Accounts: {stats['accounts']}")
        print(f"      Transactions: {stats['total_transactions']}")
        print(f"      Total Debits: ${stats['total_debits']:,.2f}")
        print(f"      Total Credits: ${stats['total_credits']:,.2f}")

    # Show sample ledger entries
    print(f"\n📝 Sample Ledger Entries (first 5):")
    for entry in ledger_entries[:5]:
        print(f"   {entry['transaction_date']} | {entry['account_name'][:30]:30} | "
              f"{entry['debit_credit']} ${entry['amount']:>10,.2f} | "
              f"Balance: ${entry['balance_after']:>12,.2f}")

    # Show sample monthly balances
    print(f"\n📊 Sample Monthly Balances (first 5):")
    for bal in monthly_balances[:5]:
        print(f"   {bal['period_label']} | {bal['account_name'][:30]:30} | "
              f"Open: ${bal['opening_balance']:>12,.2f} | "
              f"Close: ${bal['closing_balance']:>12,.2f} | "
              f"Txns: {bal['transaction_count']}")

    print(f"\n✅ Ledger generation complete!")


if __name__ == "__main__":
    from datetime import timedelta
    main()
