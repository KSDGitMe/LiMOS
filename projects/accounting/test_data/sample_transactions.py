"""
Sample Transaction Dataset for Testing

Creates 3 months (January - March 2025) of posted journal entries with:
- 12+ recurring transactions (mortgage, utilities, subscriptions, etc.)
- Various one-time transactions
- Real-world scenarios with proper FROM/TO flow
"""

from datetime import date, datetime, timedelta
from typing import List, Dict
import json
from decimal import Decimal

# Import models
import sys
sys.path.append('/Users/ksd/Projects/LiMOS')

from projects.accounting.models.journal_entries import (
    JournalEntry,
    Distribution,
    AccountType,
    FlowDirection,
    DebitCredit,
    JournalEntryType,
    JournalEntryStatus,
    RecurringJournalEntry,
    ChartOfAccounts,
    AccountBalance
)


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

CHART_OF_ACCOUNTS = [
    # ASSETS (1000-1999)
    {
        "account_id": "1000",
        "account_number": "1000",
        "account_name": "Cash - Checking",
        "account_type": "asset",
        "opening_balance": 25000.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "1100",
        "account_number": "1100",
        "account_name": "Cash - Savings",
        "account_type": "asset",
        "opening_balance": 50000.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "1200",
        "account_number": "1200",
        "account_name": "Accounts Receivable",
        "account_type": "asset",
        "opening_balance": 8500.00,
        "opening_balance_date": "2025-01-01"
    },

    # LIABILITIES (2000-2999)
    {
        "account_id": "2000",
        "account_number": "2000",
        "account_name": "Accounts Payable",
        "account_type": "liability",
        "opening_balance": 3200.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "2100",
        "account_number": "2100",
        "account_name": "Credit Card Payable",
        "account_type": "liability",
        "opening_balance": 2500.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "2200",
        "account_number": "2200",
        "account_name": "Mortgage Payable - Principal",
        "account_type": "liability",
        "opening_balance": 385000.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "2300",
        "account_number": "2300",
        "account_name": "Auto Loan Payable",
        "account_type": "liability",
        "opening_balance": 18500.00,
        "opening_balance_date": "2025-01-01"
    },

    # EQUITY (3000-3999)
    {
        "account_id": "3000",
        "account_number": "3000",
        "account_name": "Owner's Equity",
        "account_type": "equity",
        "opening_balance": -254300.00,  # Balancing entry
        "opening_balance_date": "2025-01-01"
    },

    # REVENUE (4000-4999)
    {
        "account_id": "4000",
        "account_number": "4000",
        "account_name": "Salary Income",
        "account_type": "revenue",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "4100",
        "account_number": "4100",
        "account_name": "Consulting Income",
        "account_type": "revenue",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "4200",
        "account_number": "4200",
        "account_name": "Interest Income",
        "account_type": "revenue",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },

    # EXPENSES (5000-9999)
    {
        "account_id": "6000",
        "account_number": "6000",
        "account_name": "Mortgage Interest Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6010",
        "account_number": "6010",
        "account_name": "Property Tax Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6020",
        "account_number": "6020",
        "account_name": "Home Insurance Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6100",
        "account_number": "6100",
        "account_name": "Electric Utility Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6110",
        "account_number": "6110",
        "account_name": "Gas Utility Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6120",
        "account_number": "6120",
        "account_name": "Water/Sewer Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6130",
        "account_number": "6130",
        "account_name": "Internet/Cable Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6140",
        "account_number": "6140",
        "account_name": "Mobile Phone Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6200",
        "account_number": "6200",
        "account_name": "Auto Loan Interest Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6210",
        "account_number": "6210",
        "account_name": "Auto Insurance Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6220",
        "account_number": "6220",
        "account_name": "Auto Fuel Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6300",
        "account_number": "6300",
        "account_name": "Groceries Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6310",
        "account_number": "6310",
        "account_name": "Dining Out Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6400",
        "account_number": "6400",
        "account_name": "Streaming Services Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6410",
        "account_number": "6410",
        "account_name": "Gym Membership Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
    {
        "account_id": "6500",
        "account_number": "6500",
        "account_name": "Medical Expense",
        "account_type": "expense",
        "opening_balance": 0.00,
        "opening_balance_date": "2025-01-01"
    },
]


# ============================================================================
# RECURRING TRANSACTION TEMPLATES
# ============================================================================

RECURRING_TEMPLATES = [
    # 1. Monthly Mortgage Payment (Principal + Interest at 2.1% APR)
    # $385,000 loan, 30 years, 2.1% = ~$1,439/month
    # Interest: ~$673, Principal: ~$766
    {
        "template_name": "Monthly Mortgage Payment",
        "frequency": "monthly",
        "day_of_month": 1,
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 1439.00, "desc": "Mortgage payment"},
            {"account_id": "2200", "account_type": "liability", "flow": "to", "amount": 766.00, "desc": "Principal payment"},
            {"account_id": "6000", "account_type": "expense", "flow": "to", "amount": 673.00, "desc": "Interest expense (2.1% APR)"}
        ]
    },

    # 2. Semi-Annual Property Tax ($6,000/year = $3,000 every 6 months)
    {
        "template_name": "Property Tax Payment",
        "frequency": "semiannual",
        "months": [1, 7],  # January and July
        "day_of_month": 15,
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 3000.00, "desc": "Property tax payment"},
            {"account_id": "6010", "account_type": "expense", "flow": "to", "amount": 3000.00, "desc": "Property tax expense"}
        ]
    },

    # 3. Annual Home Insurance ($1,800/year - paid in January)
    {
        "template_name": "Home Insurance Payment",
        "frequency": "annual",
        "month": 1,
        "day_of_month": 5,
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 1800.00, "desc": "Home insurance payment"},
            {"account_id": "6020", "account_type": "expense", "flow": "to", "amount": 1800.00, "desc": "Home insurance expense"}
        ]
    },

    # 4. Monthly Electric Bill (varies by season)
    {
        "template_name": "Electric Bill",
        "frequency": "monthly",
        "day_of_month": 10,
        "amount_variance": True,  # Varies by month
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": "variable", "desc": "Electric bill payment"},
            {"account_id": "6100", "account_type": "expense", "flow": "to", "amount": "variable", "desc": "Electric expense"}
        ],
        "monthly_amounts": [185.00, 195.00, 175.00]  # Jan, Feb, Mar
    },

    # 5. Monthly Gas Bill (higher in winter)
    {
        "template_name": "Gas Bill",
        "frequency": "monthly",
        "day_of_month": 12,
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": "variable", "desc": "Gas bill payment"},
            {"account_id": "6110", "account_type": "expense", "flow": "to", "amount": "variable", "desc": "Gas expense"}
        ],
        "monthly_amounts": [125.00, 115.00, 95.00]  # Jan, Feb, Mar
    },

    # 6. Monthly Water/Sewer Bill
    {
        "template_name": "Water/Sewer Bill",
        "frequency": "monthly",
        "day_of_month": 8,
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 78.00, "desc": "Water/Sewer payment"},
            {"account_id": "6120", "account_type": "expense", "flow": "to", "amount": 78.00, "desc": "Water/Sewer expense"}
        ]
    },

    # 7. Monthly Internet/Cable
    {
        "template_name": "Internet/Cable Service",
        "frequency": "monthly",
        "day_of_month": 5,
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 129.99, "desc": "Internet/Cable (credit card)"},
            {"account_id": "6130", "account_type": "expense", "flow": "to", "amount": 129.99, "desc": "Internet/Cable expense"}
        ]
    },

    # 8. Monthly Mobile Phone
    {
        "template_name": "Mobile Phone Service",
        "frequency": "monthly",
        "day_of_month": 18,
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 85.00, "desc": "Mobile phone (credit card)"},
            {"account_id": "6140", "account_type": "expense", "flow": "to", "amount": 85.00, "desc": "Mobile phone expense"}
        ]
    },

    # 9. Monthly Auto Loan Payment ($18,500 loan, 5 years, 4.5% APR = ~$345/month)
    # Interest: ~$69, Principal: ~$276
    {
        "template_name": "Auto Loan Payment",
        "frequency": "monthly",
        "day_of_month": 3,
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 345.00, "desc": "Auto loan payment"},
            {"account_id": "2300", "account_type": "liability", "flow": "to", "amount": 276.00, "desc": "Auto loan principal"},
            {"account_id": "6200", "account_type": "expense", "flow": "to", "amount": 69.00, "desc": "Auto loan interest (4.5% APR)"}
        ]
    },

    # 10. Quarterly Auto Insurance ($1,200/year = $300/quarter)
    {
        "template_name": "Auto Insurance",
        "frequency": "quarterly",
        "months": [1, 4, 7, 10],
        "day_of_month": 20,
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 300.00, "desc": "Auto insurance payment"},
            {"account_id": "6210", "account_type": "expense", "flow": "to", "amount": 300.00, "desc": "Auto insurance expense"}
        ]
    },

    # 11. Monthly Streaming Services (Netflix, Spotify, etc.)
    {
        "template_name": "Streaming Services",
        "frequency": "monthly",
        "day_of_month": 1,
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 45.98, "desc": "Streaming services (credit card)"},
            {"account_id": "6400", "account_type": "expense", "flow": "to", "amount": 45.98, "desc": "Streaming services expense"}
        ]
    },

    # 12. Monthly Gym Membership
    {
        "template_name": "Gym Membership",
        "frequency": "monthly",
        "day_of_month": 1,
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 59.99, "desc": "Gym membership (credit card)"},
            {"account_id": "6410", "account_type": "expense", "flow": "to", "amount": 59.99, "desc": "Gym membership expense"}
        ]
    },

    # 13. Bi-weekly Salary (15th and 30th of month)
    {
        "template_name": "Salary Deposit",
        "frequency": "biweekly",
        "days_of_month": [15, 30],
        "distributions": [
            {"account_id": "4000", "account_type": "revenue", "flow": "from", "amount": 3500.00, "desc": "Salary income"},
            {"account_id": "1000", "account_type": "asset", "flow": "to", "amount": 3500.00, "desc": "Salary deposit"}
        ]
    },

    # 14. Monthly Savings Interest (0.5% APY on $50,000 = ~$20.83/month)
    {
        "template_name": "Savings Interest",
        "frequency": "monthly",
        "day_of_month": 1,
        "distributions": [
            {"account_id": "4200", "account_type": "revenue", "flow": "from", "amount": 20.83, "desc": "Savings interest earned"},
            {"account_id": "1100", "account_type": "asset", "flow": "to", "amount": 20.83, "desc": "Interest deposited"}
        ]
    },
]


# ============================================================================
# ONE-TIME TRANSACTIONS
# ============================================================================

ONE_TIME_TRANSACTIONS = [
    # January
    {
        "date": "2025-01-03",
        "description": "Grocery shopping - Whole Foods",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 245.67},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 245.67}
        ]
    },
    {
        "date": "2025-01-07",
        "description": "Gas station - Shell",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 52.00},
            {"account_id": "6220", "account_type": "expense", "flow": "to", "amount": 52.00}
        ]
    },
    {
        "date": "2025-01-12",
        "description": "Dining - Italian Restaurant",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 87.50},
            {"account_id": "6310", "account_type": "expense", "flow": "to", "amount": 87.50}
        ]
    },
    {
        "date": "2025-01-16",
        "description": "Grocery shopping - Trader Joe's",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 189.34},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 189.34}
        ]
    },
    {
        "date": "2025-01-22",
        "description": "Consulting invoice payment received",
        "distributions": [
            {"account_id": "1200", "account_type": "asset", "flow": "from", "amount": 2500.00},
            {"account_id": "1000", "account_type": "asset", "flow": "to", "amount": 2500.00}
        ]
    },
    {
        "date": "2025-01-25",
        "description": "Medical co-pay - Doctor visit",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 35.00},
            {"account_id": "6500", "account_type": "expense", "flow": "to", "amount": 35.00}
        ]
    },
    {
        "date": "2025-01-28",
        "description": "Pay off credit card balance",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 1500.00},
            {"account_id": "2100", "account_type": "liability", "flow": "to", "amount": 1500.00}
        ]
    },

    # February
    {
        "date": "2025-02-04",
        "description": "Grocery shopping - Whole Foods",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 267.89},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 267.89}
        ]
    },
    {
        "date": "2025-02-09",
        "description": "Gas station - Chevron",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 48.75},
            {"account_id": "6220", "account_type": "expense", "flow": "to", "amount": 48.75}
        ]
    },
    {
        "date": "2025-02-14",
        "description": "Valentine's dinner",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 156.00},
            {"account_id": "6310", "account_type": "expense", "flow": "to", "amount": 156.00}
        ]
    },
    {
        "date": "2025-02-18",
        "description": "Grocery shopping - Costco",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 342.15},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 342.15}
        ]
    },
    {
        "date": "2025-02-20",
        "description": "Consulting project completed - invoice",
        "distributions": [
            {"account_id": "4100", "account_type": "revenue", "flow": "from", "amount": 3500.00},
            {"account_id": "1200", "account_type": "asset", "flow": "to", "amount": 3500.00}
        ]
    },
    {
        "date": "2025-02-25",
        "description": "Pay off credit card balance",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 1200.00},
            {"account_id": "2100", "account_type": "liability", "flow": "to", "amount": 1200.00}
        ]
    },

    # March
    {
        "date": "2025-03-05",
        "description": "Grocery shopping - Whole Foods",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 223.45},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 223.45}
        ]
    },
    {
        "date": "2025-03-10",
        "description": "Gas station - Shell",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 55.30},
            {"account_id": "6220", "account_type": "expense", "flow": "to", "amount": 55.30}
        ]
    },
    {
        "date": "2025-03-15",
        "description": "Consulting payment received",
        "distributions": [
            {"account_id": "1200", "account_type": "asset", "flow": "from", "amount": 3500.00},
            {"account_id": "1000", "account_type": "asset", "flow": "to", "amount": 3500.00}
        ]
    },
    {
        "date": "2025-03-19",
        "description": "Grocery shopping - Trader Joe's",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 198.76},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 198.76}
        ]
    },
    {
        "date": "2025-03-22",
        "description": "Dining - Steakhouse",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 142.00},
            {"account_id": "6310", "account_type": "expense", "flow": "to", "amount": 142.00}
        ]
    },
    {
        "date": "2025-03-28",
        "description": "Pay off credit card balance",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 1400.00},
            {"account_id": "2100", "account_type": "liability", "flow": "to", "amount": 1400.00}
        ]
    },

    # Additional January Transactions
    {
        "date": "2025-01-08",
        "description": "Amazon - Office supplies",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 127.45},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 127.45}
        ]
    },
    {
        "date": "2025-01-11",
        "description": "Coffee shop - Morning latte",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 6.75},
            {"account_id": "6310", "account_type": "expense", "flow": "to", "amount": 6.75}
        ]
    },
    {
        "date": "2025-01-14",
        "description": "Target - Household items",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 89.32},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 89.32}
        ]
    },
    {
        "date": "2025-01-17",
        "description": "Pharmacy - Prescription medication",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 25.00},
            {"account_id": "6500", "account_type": "expense", "flow": "to", "amount": 25.00}
        ]
    },
    {
        "date": "2025-01-19",
        "description": "Gas station - Exxon",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 58.90},
            {"account_id": "6220", "account_type": "expense", "flow": "to", "amount": 58.90}
        ]
    },
    {
        "date": "2025-01-21",
        "description": "Home Depot - Light fixtures",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 215.67},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 215.67}
        ]
    },
    {
        "date": "2025-01-24",
        "description": "Chipotle - Lunch",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 14.50},
            {"account_id": "6310", "account_type": "expense", "flow": "to", "amount": 14.50}
        ]
    },
    {
        "date": "2025-01-27",
        "description": "Dry cleaning services",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 42.00},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 42.00}
        ]
    },
    {
        "date": "2025-01-29",
        "description": "Book purchase - Amazon",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 32.99},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 32.99}
        ]
    },

    # Additional February Transactions
    {
        "date": "2025-02-02",
        "description": "Pet store - Dog food and supplies",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 78.45},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 78.45}
        ]
    },
    {
        "date": "2025-02-06",
        "description": "Starbucks - Coffee meeting",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 12.80},
            {"account_id": "6310", "account_type": "expense", "flow": "to", "amount": 12.80}
        ]
    },
    {
        "date": "2025-02-08",
        "description": "Dentist - Cleaning appointment",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 125.00},
            {"account_id": "6500", "account_type": "expense", "flow": "to", "amount": 125.00}
        ]
    },
    {
        "date": "2025-02-11",
        "description": "Gas station - Shell",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 51.25},
            {"account_id": "6220", "account_type": "expense", "flow": "to", "amount": 51.25}
        ]
    },
    {
        "date": "2025-02-13",
        "description": "Flowers for Valentine's Day",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 65.00},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 65.00}
        ]
    },
    {
        "date": "2025-02-16",
        "description": "Movie theater - Date night",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 38.00},
            {"account_id": "6310", "account_type": "expense", "flow": "to", "amount": 38.00}
        ]
    },
    {
        "date": "2025-02-19",
        "description": "Consulting invoice sent",
        "distributions": [
            {"account_id": "4100", "account_type": "revenue", "flow": "from", "amount": 2800.00},
            {"account_id": "1200", "account_type": "asset", "flow": "to", "amount": 2800.00}
        ]
    },
    {
        "date": "2025-02-22",
        "description": "Hardware store - Paint supplies",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 156.89},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 156.89}
        ]
    },
    {
        "date": "2025-02-27",
        "description": "Uber rides - Business meeting",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 42.50},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 42.50}
        ]
    },

    # Additional March Transactions
    {
        "date": "2025-03-02",
        "description": "Haircut and styling",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 55.00},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 55.00}
        ]
    },
    {
        "date": "2025-03-06",
        "description": "Farmers market - Fresh produce",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 47.80},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 47.80}
        ]
    },
    {
        "date": "2025-03-09",
        "description": "Gas station - BP",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 49.60},
            {"account_id": "6220", "account_type": "expense", "flow": "to", "amount": 49.60}
        ]
    },
    {
        "date": "2025-03-12",
        "description": "Office Max - Printer ink",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 67.99},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 67.99}
        ]
    },
    {
        "date": "2025-03-17",
        "description": "St. Patrick's Day dinner",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 95.75},
            {"account_id": "6310", "account_type": "expense", "flow": "to", "amount": 95.75}
        ]
    },
    {
        "date": "2025-03-21",
        "description": "Veterinarian - Dog checkup",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 185.00},
            {"account_id": "6500", "account_type": "expense", "flow": "to", "amount": 185.00}
        ]
    },
    {
        "date": "2025-03-24",
        "description": "Car wash and detailing",
        "distributions": [
            {"account_id": "1000", "account_type": "asset", "flow": "from", "amount": 45.00},
            {"account_id": "6220", "account_type": "expense", "flow": "to", "amount": 45.00}
        ]
    },
    {
        "date": "2025-03-26",
        "description": "Sports equipment - Tennis racket",
        "distributions": [
            {"account_id": "2100", "account_type": "liability", "flow": "from", "amount": 189.99},
            {"account_id": "6300", "account_type": "expense", "flow": "to", "amount": 189.99}
        ]
    },
]


# ============================================================================
# TRANSACTION GENERATOR
# ============================================================================

def generate_recurring_transactions(start_date: date, end_date: date) -> List[Dict]:
    """Generate recurring transactions for the date range."""
    transactions = []
    entry_counter = 1000

    for template in RECURRING_TEMPLATES:
        current_date = start_date
        month_index = 0

        while current_date <= end_date:
            should_generate = False
            transaction_date = None

            # Monthly transactions
            if template["frequency"] == "monthly":
                if "day_of_month" in template:
                    transaction_date = date(current_date.year, current_date.month, template["day_of_month"])
                    if start_date <= transaction_date <= end_date:
                        should_generate = True
                elif "days_of_month" in template:
                    # Bi-weekly (15th and 30th)
                    for day in template["days_of_month"]:
                        try:
                            transaction_date = date(current_date.year, current_date.month, day)
                            if start_date <= transaction_date <= end_date:
                                transactions.append(create_transaction_from_template(
                                    template, transaction_date, entry_counter, month_index
                                ))
                                entry_counter += 1
                        except ValueError:
                            pass  # Invalid day for month

            # Semi-annual transactions
            elif template["frequency"] == "semiannual":
                if current_date.month in template["months"]:
                    transaction_date = date(current_date.year, current_date.month, template["day_of_month"])
                    if start_date <= transaction_date <= end_date:
                        should_generate = True

            # Annual transactions
            elif template["frequency"] == "annual":
                if current_date.month == template["month"]:
                    transaction_date = date(current_date.year, current_date.month, template["day_of_month"])
                    if start_date <= transaction_date <= end_date:
                        should_generate = True

            # Quarterly transactions
            elif template["frequency"] == "quarterly":
                if current_date.month in template["months"]:
                    transaction_date = date(current_date.year, current_date.month, template["day_of_month"])
                    if start_date <= transaction_date <= end_date:
                        should_generate = True

            if should_generate and transaction_date:
                transactions.append(create_transaction_from_template(
                    template, transaction_date, entry_counter, month_index
                ))
                entry_counter += 1

            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
            month_index += 1

    return sorted(transactions, key=lambda x: x["entry_date"])


def create_transaction_from_template(template: Dict, transaction_date: date, entry_num: int, month_index: int) -> Dict:
    """Create a journal entry from a recurring template."""
    distributions = []

    for dist_template in template["distributions"]:
        amount = dist_template["amount"]

        # Handle variable amounts
        if amount == "variable" and "monthly_amounts" in template:
            amount = template["monthly_amounts"][month_index % len(template["monthly_amounts"])]

        distributions.append({
            "account_id": dist_template["account_id"],
            "account_type": dist_template["account_type"],
            "flow_direction": dist_template["flow"],
            "amount": amount,
            "multiplier": Distribution.calculate_multiplier(
                AccountType(dist_template["account_type"]),
                FlowDirection(dist_template["flow"])
            ),
            "description": dist_template.get("desc", template["template_name"])
        })

    return {
        "journal_entry_id": f"je-recur-{entry_num}",
        "entry_number": f"JE-2025-{entry_num:04d}",
        "entry_type": "standard",
        "entry_date": transaction_date.isoformat(),
        "posting_date": transaction_date.isoformat(),
        "description": template["template_name"],
        "status": "posted",
        "distributions": distributions,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


def generate_onetime_transactions() -> List[Dict]:
    """Generate one-time transactions."""
    transactions = []
    entry_counter = 2000

    for txn in ONE_TIME_TRANSACTIONS:
        distributions = []

        for dist in txn["distributions"]:
            distributions.append({
                "account_id": dist["account_id"],
                "account_type": dist["account_type"],
                "flow_direction": dist["flow"],
                "amount": dist["amount"],
                "multiplier": Distribution.calculate_multiplier(
                    AccountType(dist["account_type"]),
                    FlowDirection(dist["flow"])
                ),
                "description": txn["description"]
            })

        transactions.append({
            "journal_entry_id": f"je-onetime-{entry_counter}",
            "entry_number": f"JE-2025-{entry_counter:04d}",
            "entry_type": "standard",
            "entry_date": txn["date"],
            "posting_date": txn["date"],
            "description": txn["description"],
            "status": "posted",
            "distributions": distributions,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })
        entry_counter += 1

    return sorted(transactions, key=lambda x: x["entry_date"])


def generate_complete_dataset():
    """Generate complete 3-month dataset."""
    start_date = date(2025, 1, 1)
    end_date = date(2025, 3, 31)

    # Generate all transactions
    recurring = generate_recurring_transactions(start_date, end_date)
    onetime = generate_onetime_transactions()

    all_transactions = sorted(recurring + onetime, key=lambda x: x["entry_date"])

    # Renumber sequentially
    for idx, txn in enumerate(all_transactions, start=1):
        txn["entry_number"] = f"JE-2025-{idx:04d}"

    dataset = {
        "chart_of_accounts": CHART_OF_ACCOUNTS,
        "transactions": all_transactions,
        "summary": {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_transactions": len(all_transactions),
            "recurring_transactions": len(recurring),
            "onetime_transactions": len(onetime)
        }
    }

    return dataset


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("Generating 3-month transaction dataset...")

    dataset = generate_complete_dataset()

    # Save to JSON file
    output_file = "/Users/ksd/Projects/LiMOS/projects/accounting/test_data/three_month_dataset.json"
    with open(output_file, 'w') as f:
        json.dump(dataset, f, indent=2, default=str)

    print(f"\n✅ Dataset generated successfully!")
    print(f"📁 Saved to: {output_file}")
    print(f"\n📊 Summary:")
    print(f"   Period: {dataset['summary']['period_start']} to {dataset['summary']['period_end']}")
    print(f"   Total Transactions: {dataset['summary']['total_transactions']}")
    print(f"   Recurring: {dataset['summary']['recurring_transactions']}")
    print(f"   One-time: {dataset['summary']['onetime_transactions']}")
    print(f"   Chart of Accounts: {len(dataset['chart_of_accounts'])} accounts")

    # Print sample transactions
    print(f"\n📝 Sample Transactions:")
    for txn in dataset['transactions'][:5]:
        print(f"   {txn['entry_date']} - {txn['description']} ({len(txn['distributions'])} distributions)")
