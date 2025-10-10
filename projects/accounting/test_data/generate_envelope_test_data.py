"""
Generate Test Dataset with Budget and Payment Envelopes

Creates a comprehensive test dataset including:
1. Chart of Accounts with envelope links
2. Budget Envelopes (8 envelopes with different rollover policies)
3. Payment Envelopes (3 envelopes for liabilities)
4. Monthly budget allocations
5. Transactions that update envelopes
6. Expected balances and audit trails
"""

import json
from datetime import date, datetime, timedelta
from typing import Dict, List

def generate_chart_of_accounts() -> List[Dict]:
    """Generate Chart of Accounts with envelope links."""

    accounts = [
        # ASSETS (1000-1999)
        {
            "account_id": "1000",
            "account_number": "1000",
            "account_name": "Cash - Checking",
            "account_type": "asset",
            "opening_balance": 25000.00,
            "budget_envelope_id": None,
            "payment_envelope_id": None
        },
        {
            "account_id": "1100",
            "account_number": "1100",
            "account_name": "Cash - Savings",
            "account_type": "asset",
            "opening_balance": 50000.00,
            "budget_envelope_id": None,
            "payment_envelope_id": None
        },

        # LIABILITIES (2000-2999)
        {
            "account_id": "2100",
            "account_number": "2100",
            "account_name": "Credit Card A",
            "account_type": "liability",
            "opening_balance": 2500.00,
            "budget_envelope_id": None,
            "payment_envelope_id": "1600"  # Linked to payment envelope
        },
        {
            "account_id": "2110",
            "account_number": "2110",
            "account_name": "Credit Card B",
            "account_type": "liability",
            "opening_balance": 1200.00,
            "budget_envelope_id": None,
            "payment_envelope_id": "1610"
        },
        {
            "account_id": "2300",
            "account_number": "2300",
            "account_name": "Auto Loan Payable",
            "account_type": "liability",
            "opening_balance": 18500.00,
            "budget_envelope_id": None,
            "payment_envelope_id": "1620"
        },

        # EQUITY (3000-3999)
        {
            "account_id": "3000",
            "account_number": "3000",
            "account_name": "Owner's Equity",
            "account_type": "equity",
            "opening_balance": 52000.00,
            "budget_envelope_id": None,
            "payment_envelope_id": None
        },

        # REVENUE (5000-5999)
        {
            "account_id": "5000",
            "account_number": "5000",
            "account_name": "Salary Income",
            "account_type": "revenue",
            "opening_balance": 0.00,
            "budget_envelope_id": None,
            "payment_envelope_id": None
        },

        # EXPENSES (6000-6999) - All linked to budget envelopes
        {
            "account_id": "6300",
            "account_number": "6300",
            "account_name": "Grocery Stores",
            "account_type": "expense",
            "opening_balance": 0.00,
            "budget_envelope_id": "1500",  # Groceries envelope
            "payment_envelope_id": None
        },
        {
            "account_id": "6310",
            "account_number": "6310",
            "account_name": "Restaurants - Dining Out",
            "account_type": "expense",
            "opening_balance": 0.00,
            "budget_envelope_id": "1510",  # Dining Out envelope
            "payment_envelope_id": None
        },
        {
            "account_id": "6400",
            "account_number": "6400",
            "account_name": "Gas & Auto Fuel",
            "account_type": "expense",
            "opening_balance": 0.00,
            "budget_envelope_id": "1520",  # Gas & Auto envelope
            "payment_envelope_id": None
        },
        {
            "account_id": "6500",
            "account_number": "6500",
            "account_name": "Entertainment",
            "account_type": "expense",
            "opening_balance": 0.00,
            "budget_envelope_id": "1530",  # Entertainment envelope
            "payment_envelope_id": None
        },
        {
            "account_id": "6600",
            "account_number": "6600",
            "account_name": "Clothing & Shoes",
            "account_type": "expense",
            "opening_balance": 0.00,
            "budget_envelope_id": "1540",  # Clothing envelope
            "payment_envelope_id": None
        },
        {
            "account_id": "6700",
            "account_number": "6700",
            "account_name": "Home Maintenance",
            "account_type": "expense",
            "opening_balance": 0.00,
            "budget_envelope_id": "1550",  # Home Maintenance envelope
            "payment_envelope_id": None
        },
        {
            "account_id": "6800",
            "account_number": "6800",
            "account_name": "Gifts",
            "account_type": "expense",
            "opening_balance": 0.00,
            "budget_envelope_id": "1560",  # Gifts envelope
            "payment_envelope_id": None
        },
        {
            "account_id": "6900",
            "account_number": "6900",
            "account_name": "Personal Care",
            "account_type": "expense",
            "opening_balance": 0.00,
            "budget_envelope_id": "1570",  # Personal Care envelope
            "payment_envelope_id": None
        }
    ]

    return accounts


def generate_budget_envelopes() -> List[Dict]:
    """Generate Budget Envelopes with different rollover policies."""

    envelopes = [
        {
            "envelope_id": "1500",
            "envelope_number": "1500",
            "envelope_name": "Groceries",
            "envelope_type": "budget",
            "category": "Food & Dining",
            "monthly_allocation": 800.00,
            "rollover_policy": "accumulate",
            "rollover_cap": None,
            "current_balance": 0.00,
            "is_active": True,
            "display_order": 1
        },
        {
            "envelope_id": "1510",
            "envelope_number": "1510",
            "envelope_name": "Dining Out",
            "envelope_type": "budget",
            "category": "Food & Dining",
            "monthly_allocation": 300.00,
            "rollover_policy": "reset",
            "rollover_cap": None,
            "current_balance": 0.00,
            "is_active": True,
            "display_order": 2
        },
        {
            "envelope_id": "1520",
            "envelope_number": "1520",
            "envelope_name": "Gas & Auto",
            "envelope_type": "budget",
            "category": "Transportation",
            "monthly_allocation": 250.00,
            "rollover_policy": "accumulate",
            "rollover_cap": None,
            "current_balance": 0.00,
            "is_active": True,
            "display_order": 3
        },
        {
            "envelope_id": "1530",
            "envelope_number": "1530",
            "envelope_name": "Entertainment",
            "envelope_type": "budget",
            "category": "Leisure",
            "monthly_allocation": 150.00,
            "rollover_policy": "reset",
            "rollover_cap": None,
            "current_balance": 0.00,
            "is_active": True,
            "display_order": 4
        },
        {
            "envelope_id": "1540",
            "envelope_number": "1540",
            "envelope_name": "Clothing",
            "envelope_type": "budget",
            "category": "Personal",
            "monthly_allocation": 200.00,
            "rollover_policy": "cap",
            "rollover_cap": 600.00,
            "current_balance": 0.00,
            "is_active": True,
            "display_order": 5
        },
        {
            "envelope_id": "1550",
            "envelope_number": "1550",
            "envelope_name": "Home Maintenance",
            "envelope_type": "budget",
            "category": "Housing",
            "monthly_allocation": 500.00,
            "rollover_policy": "accumulate",
            "rollover_cap": None,
            "current_balance": 0.00,
            "is_active": True,
            "display_order": 6
        },
        {
            "envelope_id": "1560",
            "envelope_number": "1560",
            "envelope_name": "Gifts",
            "envelope_type": "budget",
            "category": "Personal",
            "monthly_allocation": 100.00,
            "rollover_policy": "accumulate",
            "rollover_cap": None,
            "current_balance": 0.00,
            "is_active": True,
            "display_order": 7
        },
        {
            "envelope_id": "1570",
            "envelope_number": "1570",
            "envelope_name": "Personal Care",
            "envelope_type": "budget",
            "category": "Personal",
            "monthly_allocation": 100.00,
            "rollover_policy": "reset",
            "rollover_cap": None,
            "current_balance": 0.00,
            "is_active": True,
            "display_order": 8
        }
    ]

    return envelopes


def generate_payment_envelopes() -> List[Dict]:
    """Generate Payment Envelopes for liabilities."""

    envelopes = [
        {
            "envelope_id": "1600",
            "envelope_number": "1600",
            "envelope_name": "Credit Card A - Payment Reserve",
            "envelope_type": "payment",
            "linked_account_id": "2100",
            "linked_account_name": "Credit Card A",
            "category": "Credit Cards",
            "current_balance": 2500.00,  # Matches opening liability balance
            "is_active": True,
            "display_order": 1
        },
        {
            "envelope_id": "1610",
            "envelope_number": "1610",
            "envelope_name": "Credit Card B - Payment Reserve",
            "envelope_type": "payment",
            "linked_account_id": "2110",
            "linked_account_name": "Credit Card B",
            "category": "Credit Cards",
            "current_balance": 1200.00,
            "is_active": True,
            "display_order": 2
        },
        {
            "envelope_id": "1620",
            "envelope_number": "1620",
            "envelope_name": "Auto Loan - Payment Reserve",
            "envelope_type": "payment",
            "linked_account_id": "2300",
            "linked_account_name": "Auto Loan Payable",
            "category": "Loans",
            "current_balance": 18500.00,
            "is_active": True,
            "display_order": 3
        }
    ]

    return envelopes


def generate_monthly_allocations() -> List[Dict]:
    """Generate budget allocations for 3 months."""

    allocations = []
    months = [
        ("2025-01", date(2025, 1, 1)),
        ("2025-02", date(2025, 2, 1)),
        ("2025-03", date(2025, 3, 1))
    ]

    budget_envelopes = generate_budget_envelopes()

    for period_label, allocation_date in months:
        for envelope in budget_envelopes:
            allocation = {
                "allocation_id": f"alloc-{envelope['envelope_id']}-{period_label}",
                "source_account_id": "1000",
                "envelope_id": envelope["envelope_id"],
                "envelope_type": "budget",
                "allocation_date": allocation_date.isoformat(),
                "amount": envelope["monthly_allocation"],
                "period_label": period_label,
                "description": f"Monthly allocation for {envelope['envelope_name']}",
                "is_automatic": True,
                "created_at": datetime.utcnow().isoformat()
            }
            allocations.append(allocation)

    return allocations


def generate_sample_transactions() -> List[Dict]:
    """Generate sample transactions that update envelopes."""

    transactions = [
        # January transactions
        {
            "journal_entry_id": "txn-2025-01-05",
            "entry_number": "JE-2025-001",
            "entry_date": "2025-01-05",
            "description": "Whole Foods groceries (cash)",
            "distributions": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 145.67,
                    "multiplier": -1
                },
                {
                    "account_id": "6300",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 145.67,
                    "multiplier": 1,
                    "budget_envelope_id": "1500"
                }
            ]
        },
        {
            "journal_entry_id": "txn-2025-01-08",
            "entry_number": "JE-2025-002",
            "entry_date": "2025-01-08",
            "description": "Costco on Credit Card A",
            "distributions": [
                {
                    "account_id": "2100",
                    "account_type": "liability",
                    "flow_direction": "from",
                    "amount": 287.43,
                    "multiplier": 1,
                    "payment_envelope_id": "1600"
                },
                {
                    "account_id": "6300",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 287.43,
                    "multiplier": 1,
                    "budget_envelope_id": "1500"
                }
            ]
        },
        {
            "journal_entry_id": "txn-2025-01-12",
            "entry_number": "JE-2025-003",
            "entry_date": "2025-01-12",
            "description": "Restaurant dinner",
            "distributions": [
                {
                    "account_id": "2100",
                    "account_type": "liability",
                    "flow_direction": "from",
                    "amount": 89.50,
                    "multiplier": 1,
                    "payment_envelope_id": "1600"
                },
                {
                    "account_id": "6310",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 89.50,
                    "multiplier": 1,
                    "budget_envelope_id": "1510"
                }
            ]
        },
        {
            "journal_entry_id": "txn-2025-01-15",
            "entry_number": "JE-2025-004",
            "entry_date": "2025-01-15",
            "description": "Pay Credit Card A",
            "distributions": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 1000.00,
                    "multiplier": -1
                },
                {
                    "account_id": "2100",
                    "account_type": "liability",
                    "flow_direction": "to",
                    "amount": 1000.00,
                    "multiplier": -1,
                    "payment_envelope_id": "1600"
                }
            ]
        },
        {
            "journal_entry_id": "txn-2025-01-20",
            "entry_number": "JE-2025-005",
            "entry_date": "2025-01-20",
            "description": "Gas station",
            "distributions": [
                {
                    "account_id": "1000",
                    "account_type": "asset",
                    "flow_direction": "from",
                    "amount": 65.00,
                    "multiplier": -1
                },
                {
                    "account_id": "6400",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 65.00,
                    "multiplier": 1,
                    "budget_envelope_id": "1520"
                }
            ]
        },
        {
            "journal_entry_id": "txn-2025-01-25",
            "entry_number": "JE-2025-006",
            "entry_date": "2025-01-25",
            "description": "Movie tickets",
            "distributions": [
                {
                    "account_id": "2110",
                    "account_type": "liability",
                    "flow_direction": "from",
                    "amount": 45.00,
                    "multiplier": 1,
                    "payment_envelope_id": "1610"
                },
                {
                    "account_id": "6500",
                    "account_type": "expense",
                    "flow_direction": "to",
                    "amount": 45.00,
                    "multiplier": 1,
                    "budget_envelope_id": "1530"
                }
            ]
        }
    ]

    return transactions


def calculate_expected_balances() -> Dict:
    """Calculate expected envelope balances after allocations and transactions."""

    # Starting balances (after January allocation)
    budget_balances = {
        "1500": 800.00,   # Groceries
        "1510": 300.00,   # Dining
        "1520": 250.00,   # Gas
        "1530": 150.00,   # Entertainment
        "1540": 200.00,   # Clothing
        "1550": 500.00,   # Home Maintenance
        "1560": 100.00,   # Gifts
        "1570": 100.00    # Personal Care
    }

    payment_balances = {
        "1600": 2500.00,  # CC-A
        "1610": 1200.00,  # CC-B
        "1620": 18500.00  # Auto Loan
    }

    # Apply transactions
    # JE-001: Groceries -145.67
    budget_balances["1500"] -= 145.67

    # JE-002: Groceries -287.43, CC-A +287.43
    budget_balances["1500"] -= 287.43
    payment_balances["1600"] += 287.43

    # JE-003: Dining -89.50, CC-A +89.50
    budget_balances["1510"] -= 89.50
    payment_balances["1600"] += 89.50

    # JE-004: CC-A payment -1000.00
    payment_balances["1600"] -= 1000.00

    # JE-005: Gas -65.00
    budget_balances["1520"] -= 65.00

    # JE-006: Entertainment -45.00, CC-B +45.00
    budget_balances["1530"] -= 45.00
    payment_balances["1610"] += 45.00

    return {
        "as_of_date": "2025-01-31",
        "budget_envelopes": budget_balances,
        "payment_envelopes": payment_balances,
        "total_budget_allocated": sum(budget_balances.values()),
        "total_payment_reserved": sum(payment_balances.values())
    }


def main():
    """Generate complete envelope test dataset."""

    print("Generating Envelope Test Dataset...")

    dataset = {
        "chart_of_accounts": generate_chart_of_accounts(),
        "budget_envelopes": generate_budget_envelopes(),
        "payment_envelopes": generate_payment_envelopes(),
        "budget_allocations": generate_monthly_allocations(),
        "transactions": generate_sample_transactions(),
        "expected_balances": calculate_expected_balances()
    }

    # Save dataset
    output_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/envelope_test_data.json"
    with open(output_file, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"\n✅ Dataset saved to: {output_file}")

    # Print summary
    print(f"\n📊 Dataset Summary:")
    print(f"   Chart of Accounts: {len(dataset['chart_of_accounts'])} accounts")
    print(f"   Budget Envelopes: {len(dataset['budget_envelopes'])} envelopes")
    print(f"   Payment Envelopes: {len(dataset['payment_envelopes'])} envelopes")
    print(f"   Budget Allocations: {len(dataset['budget_allocations'])} allocations (3 months)")
    print(f"   Transactions: {len(dataset['transactions'])} transactions")

    print(f"\n💰 Expected Balances (2025-01-31):")
    print(f"   Total Budget Allocated: ${dataset['expected_balances']['total_budget_allocated']:,.2f}")
    print(f"   Total Payment Reserved: ${dataset['expected_balances']['total_payment_reserved']:,.2f}")

    print(f"\n📋 Budget Envelope Balances:")
    for env_id, balance in dataset['expected_balances']['budget_envelopes'].items():
        env = next(e for e in dataset['budget_envelopes'] if e['envelope_id'] == env_id)
        print(f"   {env['envelope_name']}: ${balance:,.2f}")

    print(f"\n💳 Payment Envelope Balances:")
    for env_id, balance in dataset['expected_balances']['payment_envelopes'].items():
        env = next(e for e in dataset['payment_envelopes'] if e['envelope_id'] == env_id)
        print(f"   {env['envelope_name']}: ${balance:,.2f}")


if __name__ == "__main__":
    main()
