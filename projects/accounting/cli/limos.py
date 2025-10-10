#!/usr/bin/env python3
"""
LiMOS Accounting CLI Tool

Command-line interface for the LiMOS accounting system.

Usage:
    limos tx add "Description" --from ACCOUNT:AMOUNT --to ACCOUNT:AMOUNT
    limos budget allocate --month 2025-02
    limos forecast --account 1000 --date 2025-06-15
    limos recurring expand --start 2025-01-01 --end 2025-12-31
"""

import click
import requests
import json
from datetime import date, datetime
from typing import List, Tuple
from tabulate import tabulate

# API configuration
API_BASE_URL = "http://localhost:8000"

# Click CLI app
@click.group()
@click.version_option(version="1.0.0")
def cli():
    """LiMOS Accounting - Command Line Interface"""
    pass

# ============================================================================
# TRANSACTIONS (tx)
# ============================================================================

@cli.group()
def tx():
    """Transaction management commands"""
    pass

@tx.command("add")
@click.argument("description")
@click.option("--from", "from_specs", multiple=True, required=True,
              help="FROM distribution: ACCOUNT_ID:AMOUNT (can specify multiple)")
@click.option("--to", "to_specs", multiple=True, required=True,
              help="TO distribution: ACCOUNT_ID:AMOUNT (can specify multiple)")
@click.option("--date", "entry_date", default=None,
              help="Entry date (YYYY-MM-DD, defaults to today)")
@click.option("--post", is_flag=True, help="Post immediately (default is draft)")
def add_transaction(description: str, from_specs: Tuple[str], to_specs: Tuple[str],
                   entry_date: str, post: bool):
    """
    Add a new transaction.

    Example:
        limos tx add "Groceries at Whole Foods" \\
            --from 1000:125.50 \\
            --to 6300:125.50 \\
            --post
    """
    # Parse FROM distributions
    from_distributions = []
    for spec in from_specs:
        try:
            account_id, amount = spec.split(":")
            from_distributions.append({
                "account_id": account_id,
                "flow_direction": "from",
                "amount": float(amount)
            })
        except ValueError:
            click.echo(f"Error: Invalid FROM spec '{spec}'. Use format ACCOUNT:AMOUNT", err=True)
            return

    # Parse TO distributions
    to_distributions = []
    for spec in to_specs:
        try:
            account_id, amount = spec.split(":")
            to_distributions.append({
                "account_id": account_id,
                "flow_direction": "to",
                "amount": float(amount)
            })
        except ValueError:
            click.echo(f"Error: Invalid TO spec '{spec}'. Use format ACCOUNT:AMOUNT", err=True)
            return

    # Check balanced
    from_total = sum(d["amount"] for d in from_distributions)
    to_total = sum(d["amount"] for d in to_distributions)

    if abs(from_total - to_total) > 0.01:
        click.echo(f"Error: Transaction not balanced. FROM: ${from_total:.2f}, TO: ${to_total:.2f}", err=True)
        return

    # Get account types (would normally look up from API)
    # For now, infer from account number prefix
    def get_account_type(account_id: str) -> str:
        if account_id.startswith("1"):
            return "asset"
        elif account_id.startswith("2"):
            return "liability"
        elif account_id.startswith("3"):
            return "equity"
        elif account_id.startswith("5"):
            return "revenue"
        elif account_id.startswith("6"):
            return "expense"
        else:
            return "asset"  # default

    # Build complete distributions
    all_distributions = []

    for dist in from_distributions:
        account_type = get_account_type(dist["account_id"])
        all_distributions.append({
            "account_id": dist["account_id"],
            "account_type": account_type,
            "flow_direction": "from",
            "amount": dist["amount"],
            "multiplier": -1 if account_type in ["asset", "expense"] else 1,
            "debit_credit": "Cr" if account_type in ["asset", "expense"] else "Dr"
        })

    for dist in to_distributions:
        account_type = get_account_type(dist["account_id"])
        all_distributions.append({
            "account_id": dist["account_id"],
            "account_type": account_type,
            "flow_direction": "to",
            "amount": dist["amount"],
            "multiplier": 1 if account_type in ["asset", "expense"] else -1,
            "debit_credit": "Dr" if account_type in ["asset", "expense"] else "Cr"
        })

    # Create journal entry
    entry_data = {
        "entry_date": entry_date or date.today().isoformat(),
        "description": description,
        "distributions": all_distributions,
        "status": "posted" if post else "draft"
    }

    try:
        response = requests.post(f"{API_BASE_URL}/api/journal-entries", json=entry_data)
        response.raise_for_status()
        entry = response.json()

        click.echo(click.style("✓ Transaction created successfully!", fg="green"))
        click.echo(f"Entry ID: {entry['journal_entry_id']}")
        click.echo(f"Status: {entry['status']}")
        click.echo(f"Amount: ${from_total:.2f}")

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error creating transaction: {e}", fg="red"), err=True)

@tx.command("list")
@click.option("--start", help="Start date (YYYY-MM-DD)")
@click.option("--end", help="End date (YYYY-MM-DD)")
@click.option("--status", type=click.Choice(["draft", "posted", "void"]), help="Filter by status")
@click.option("--limit", default=20, help="Number of entries to show")
def list_transactions(start: str, end: str, status: str, limit: int):
    """List recent transactions"""
    params = {"limit": limit}
    if start:
        params["start_date"] = start
    if end:
        params["end_date"] = end
    if status:
        params["status"] = status

    try:
        response = requests.get(f"{API_BASE_URL}/api/journal-entries", params=params)
        response.raise_for_status()
        entries = response.json()

        if not entries:
            click.echo("No transactions found.")
            return

        # Format for display
        table_data = []
        for entry in entries:
            amount = sum(d["amount"] for d in entry["distributions"] if d["flow_direction"] == "from")
            table_data.append([
                entry["entry_date"],
                entry["description"][:50],
                entry["status"],
                f"${amount:,.2f}"
            ])

        click.echo(tabulate(table_data, headers=["Date", "Description", "Status", "Amount"], tablefmt="simple"))

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error fetching transactions: {e}", fg="red"), err=True)

# ============================================================================
# BUDGET
# ============================================================================

@cli.group()
def budget():
    """Budget envelope commands"""
    pass

@budget.command("allocate")
@click.option("--month", required=True, help="Month to allocate (YYYY-MM)")
@click.option("--source", default="1000", help="Source account ID (default: 1000)")
def allocate_budget(month: str, source: str):
    """Apply monthly budget allocations"""
    try:
        # Parse month
        year, month_num = month.split("-")
        allocation_date = f"{year}-{month_num}-01"
        period_label = month

        response = requests.post(
            f"{API_BASE_URL}/api/envelopes/allocate",
            params={
                "source_account_id": source,
                "allocation_date": allocation_date,
                "period_label": period_label
            }
        )
        response.raise_for_status()
        result = response.json()

        click.echo(click.style(f"✓ {result['message']}", fg="green"))

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error applying allocations: {e}", fg="red"), err=True)

@budget.command("list")
def list_budgets():
    """List all budget envelopes"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/envelopes/budget")
        response.raise_for_status()
        envelopes = response.json()

        if not envelopes:
            click.echo("No budget envelopes found.")
            return

        table_data = []
        for env in envelopes:
            table_data.append([
                env["envelope_name"],
                f"${env['monthly_allocation']:,.2f}",
                f"${env['current_balance']:,.2f}",
                env["rollover_policy"]
            ])

        click.echo(tabulate(table_data,
                          headers=["Envelope", "Monthly", "Balance", "Policy"],
                          tablefmt="simple"))

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error fetching envelopes: {e}", fg="red"), err=True)

# ============================================================================
# FORECAST
# ============================================================================

@cli.group()
def forecast():
    """Forecasting commands"""
    pass

@forecast.command("account")
@click.option("--account", "-a", required=True, help="Account ID")
@click.option("--date", "-d", required=True, help="Target date (YYYY-MM-DD)")
def forecast_account(account: str, date: str):
    """Forecast account balance on a future date"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/forecast/account/{account}",
            params={"target_date": date}
        )
        response.raise_for_status()
        forecast = response.json()

        click.echo(click.style(f"\n📊 Account Forecast: {forecast['account_name']}", fg="cyan", bold=True))
        click.echo(f"   Current Balance:    ${forecast['current_balance']:>12,.2f}  (as of {forecast['as_of_date']})")
        click.echo(f"   Projected Balance:  ${forecast['projected_balance']:>12,.2f}  (on {forecast['target_date']})")
        click.echo(f"   Change:             ${forecast['balance_change']:>12,.2f}")
        click.echo(f"   Transactions:       {forecast['transactions_applied']:>12} recurring entries applied")

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error fetching forecast: {e}", fg="red"), err=True)

# ============================================================================
# RECURRING
# ============================================================================

@cli.group()
def recurring():
    """Recurring transaction commands"""
    pass

@recurring.command("list")
def list_recurring():
    """List recurring transaction templates"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/recurring-templates")
        response.raise_for_status()
        templates = response.json()

        if not templates:
            click.echo("No recurring templates found.")
            return

        table_data = []
        for tmpl in templates:
            table_data.append([
                tmpl["template_name"][:40],
                tmpl["frequency"],
                tmpl["start_date"],
                "Active" if tmpl["is_active"] else "Inactive"
            ])

        click.echo(tabulate(table_data,
                          headers=["Template", "Frequency", "Start Date", "Status"],
                          tablefmt="simple"))

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error fetching templates: {e}", fg="red"), err=True)

@recurring.command("expand")
@click.option("--start", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", required=True, help="End date (YYYY-MM-DD)")
@click.option("--post", is_flag=True, help="Post generated entries immediately")
def expand_recurring(start: str, end: str, post: bool):
    """Expand recurring templates into transactions"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/recurring-templates/expand",
            params={
                "start_date": start,
                "end_date": end,
                "auto_post": post
            }
        )
        response.raise_for_status()
        entries = response.json()

        click.echo(click.style(f"✓ Generated {len(entries)} transactions from recurring templates", fg="green"))

        if entries:
            click.echo(f"\n📅 Date range: {entries[0]['entry_date']} to {entries[-1]['entry_date']}")

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error expanding templates: {e}", fg="red"), err=True)

# ============================================================================
# ACCOUNTS
# ============================================================================

@cli.group()
def accounts():
    """Chart of accounts commands"""
    pass

@accounts.command("list")
@click.option("--type", "account_type", type=click.Choice(["asset", "liability", "equity", "revenue", "expense"]),
              help="Filter by account type")
def list_accounts(account_type: str):
    """List all accounts"""
    params = {}
    if account_type:
        params["account_type"] = account_type

    try:
        response = requests.get(f"{API_BASE_URL}/api/accounts", params=params)
        response.raise_for_status()
        accounts = response.json()

        if not accounts:
            click.echo("No accounts found.")
            return

        table_data = []
        for acct in accounts:
            table_data.append([
                acct["account_number"],
                acct["account_name"][:40],
                acct["account_type"],
                f"${acct['current_balance']:,.2f}"
            ])

        click.echo(tabulate(table_data,
                          headers=["Number", "Name", "Type", "Balance"],
                          tablefmt="simple"))

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error fetching accounts: {e}", fg="red"), err=True)

@accounts.command("view")
@click.argument("account_id")
def view_account(account_id: str):
    """View account with envelope breakdown"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/accounts/{account_id}/view")
        response.raise_for_status()
        view = response.json()

        click.echo(click.style(f"\n💰 {view['account_name']}", fg="cyan", bold=True))
        click.echo(f"   Bank Balance:       ${view['bank_balance']:>12,.2f}")
        click.echo(f"   Budget Allocated:   ${view['budget_allocated']:>12,.2f}")
        click.echo(f"   Payment Reserved:   ${view['payment_reserved']:>12,.2f}")
        click.echo(f"   Available:          ${view['available_to_allocate']:>12,.2f}")
        click.echo(f"   Balanced: {click.style('✓', fg='green') if view['is_balanced'] else click.style('✗', fg='red')}")

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error fetching account view: {e}", fg="red"), err=True)

# ============================================================================
# STATS
# ============================================================================

@cli.command()
def stats():
    """Show system statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats/summary")
        response.raise_for_status()
        stats = response.json()

        click.echo(click.style("\n📊 LiMOS Accounting System Statistics\n", fg="cyan", bold=True))

        click.echo(click.style("Chart of Accounts:", fg="yellow"))
        click.echo(f"   Total: {stats['chart_of_accounts']['total']}")
        for acct_type, count in stats['chart_of_accounts']['by_type'].items():
            click.echo(f"   - {acct_type.capitalize()}: {count}")

        click.echo(click.style("\nJournal Entries:", fg="yellow"))
        click.echo(f"   Total: {stats['journal_entries']['total']}")
        click.echo(f"   - Posted: {stats['journal_entries']['posted']}")
        click.echo(f"   - Draft: {stats['journal_entries']['draft']}")

        click.echo(click.style("\nEnvelopes:", fg="yellow"))
        click.echo(f"   Budget Envelopes: {stats['envelopes']['budget']}")
        click.echo(f"   Payment Envelopes: {stats['envelopes']['payment']}")
        click.echo(f"   Total Budget Allocated: ${stats['envelopes']['total_budget_allocated']:,.2f}")
        click.echo(f"   Total Payment Reserved: ${stats['envelopes']['total_payment_reserved']:,.2f}")

        click.echo(click.style("\nRecurring Templates:", fg="yellow"))
        click.echo(f"   Total: {stats['recurring_templates']['total']}")
        click.echo(f"   Active: {stats['recurring_templates']['active']}")

    except requests.exceptions.RequestException as e:
        click.echo(click.style(f"✗ Error fetching stats: {e}", fg="red"), err=True)

# ============================================================================
# SERVER
# ============================================================================

@cli.command()
@click.option("--port", default=8000, help="Port to run server on")
def serve(port: int):
    """Start the API server"""
    click.echo(f"Starting LiMOS Accounting API on port {port}...")
    click.echo(f"Documentation: http://localhost:{port}/docs")

    import subprocess
    import sys

    # Run uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "projects.accounting.api.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ])

if __name__ == "__main__":
    cli()
