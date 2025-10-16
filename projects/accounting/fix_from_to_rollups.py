#!/usr/bin/env python3
"""
Fix FROM/TO Rollup Fields with Filtered Formulas
=================================================
Replace the from_total and to_total rollup fields with formula fields that
properly filter distributions by their flow_direction.

Since Notion rollups can't filter, we need to use formulas that iterate
through the related distributions and sum only those with the matching
flow_direction.
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path
import json

# Load environment
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_JOURNAL_ENTRIES_DB_ID = os.getenv("NOTION_JOURNAL_ENTRIES_DB_ID")
NOTION_DISTRIBUTIONS_DB_ID = os.getenv("NOTION_DISTRIBUTIONS_DB_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def get_database_schema():
    """Get the current database schema to see the relation property name."""
    print("\n📋 Fetching current database schema...")

    url = f"https://api.notion.com/v1/databases/{NOTION_JOURNAL_ENTRIES_DB_ID}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"❌ Failed to fetch database: {response.status_code}")
        return None

    data = response.json()
    properties = data.get("properties", {})

    # Find the relation property to Distributions
    for prop_name, prop_data in properties.items():
        if prop_data.get("type") == "relation":
            relation = prop_data.get("relation", {})
            if relation.get("database_id") == NOTION_DISTRIBUTIONS_DB_ID:
                print(f"   ✅ Found relation property: '{prop_name}'")
                return prop_name

    print("   ⚠️  Could not find relation to Distributions")
    return None


def update_from_total_to_formula():
    """
    Replace from_total rollup with a formula that sums only FROM distributions.

    Unfortunately, Notion formulas cannot directly access related page properties
    to filter by flow_direction. We need a different approach.

    WORKAROUND: We'll update the Distributions database to add a computed field
    that returns the amount if flow_direction is FROM, otherwise 0. Then rollup
    can sum that computed field.
    """
    print("\n1️⃣  Updating Distributions database with FROM_amount formula...")

    url = f"https://api.notion.com/v1/databases/{NOTION_DISTRIBUTIONS_DB_ID}"

    # Add a formula field that returns amount if FROM, else 0
    payload = {
        "properties": {
            "from_amount": {
                "formula": {
                    "expression": 'if(prop("flow_direction") == "from", prop("amount"), 0)'
                }
            }
        }
    }

    response = requests.patch(url, headers=HEADERS, json=payload)

    if response.status_code == 200:
        print("   ✅ Added 'from_amount' formula to Distributions")
    else:
        print(f"   ❌ Failed to add formula: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    return True


def update_to_total_to_formula():
    """Add TO_amount formula to Distributions database."""
    print("\n2️⃣  Updating Distributions database with TO_amount formula...")

    url = f"https://api.notion.com/v1/databases/{NOTION_DISTRIBUTIONS_DB_ID}"

    # Add a formula field that returns amount if TO, else 0
    payload = {
        "properties": {
            "to_amount": {
                "formula": {
                    "expression": 'if(prop("flow_direction") == "to", prop("amount"), 0)'
                }
            }
        }
    }

    response = requests.patch(url, headers=HEADERS, json=payload)

    if response.status_code == 200:
        print("   ✅ Added 'to_amount' formula to Distributions")
    else:
        print(f"   ❌ Failed to add formula: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    return True


def update_journal_entries_rollups(relation_name):
    """Update Journal Entries rollups to use the new formula fields."""
    print(f"\n3️⃣  Updating Journal Entries rollups to use filtered amounts...")

    url = f"https://api.notion.com/v1/databases/{NOTION_JOURNAL_ENTRIES_DB_ID}"

    payload = {
        "properties": {
            "from_total": {
                "rollup": {
                    "relation_property_name": relation_name,
                    "rollup_property_name": "from_amount",
                    "function": "sum"
                }
            },
            "to_total": {
                "rollup": {
                    "relation_property_name": relation_name,
                    "rollup_property_name": "to_amount",
                    "function": "sum"
                }
            }
        }
    }

    response = requests.patch(url, headers=HEADERS, json=payload)

    if response.status_code == 200:
        print("   ✅ Updated 'from_total' rollup to sum from_amount")
        print("   ✅ Updated 'to_total' rollup to sum to_amount")
    else:
        print(f"   ❌ Failed to update rollups: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    return True


def update_is_balanced_formula():
    """Update the is_balanced formula to use the corrected rollups."""
    print("\n4️⃣  Updating 'is_balanced' formula...")

    url = f"https://api.notion.com/v1/databases/{NOTION_JOURNAL_ENTRIES_DB_ID}"

    # Now that from_total and to_total are correctly filtered, the formula should be:
    # amount == from_total AND amount == to_total
    payload = {
        "properties": {
            "is_balanced": {
                "formula": {
                    "expression": 'prop("amount") == prop("from_total") and prop("amount") == prop("to_total")'
                }
            }
        }
    }

    response = requests.patch(url, headers=HEADERS, json=payload)

    if response.status_code == 200:
        print("   ✅ Updated 'is_balanced' formula")
    else:
        print(f"   ❌ Failed to update formula: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    return True


def verify_fix():
    """Verify the fix by checking a few entries."""
    print("\n5️⃣  Verifying the fix...")

    url = f"https://api.notion.com/v1/databases/{NOTION_JOURNAL_ENTRIES_DB_ID}/query"

    payload = {
        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
        "page_size": 3
    }

    response = requests.post(url, headers=HEADERS, json=payload)

    if response.status_code != 200:
        print(f"   ❌ Failed to query entries: {response.status_code}")
        return False

    entries = response.json().get("results", [])

    print(f"\n   Checking {len(entries)} recent entries:")

    for entry in entries:
        props = entry.get("properties", {})

        name = props.get("Name", {}).get("title", [])
        entry_name = name[0].get("plain_text", "Untitled") if name else "Untitled"

        amount = props.get("amount", {}).get("number")

        from_total_obj = props.get("from_total", {}).get("rollup", {})
        from_total = from_total_obj.get("number") if from_total_obj.get("type") == "number" else None

        to_total_obj = props.get("to_total", {}).get("rollup", {})
        to_total = to_total_obj.get("number") if to_total_obj.get("type") == "number" else None

        is_balanced_obj = props.get("is_balanced", {}).get("formula", {})
        is_balanced = is_balanced_obj.get("boolean") if is_balanced_obj.get("type") == "boolean" else None

        print(f"\n   {'✅' if is_balanced else '❌'} {entry_name[:50]}")
        amount_str = f"${amount:.2f}" if amount is not None else "$0.00"
        from_str = f"${from_total:.2f}" if from_total is not None else "$0.00"
        to_str = f"${to_total:.2f}" if to_total is not None else "$0.00"
        print(f"      Amount: {amount_str}")
        print(f"      FROM:   {from_str}")
        print(f"      TO:     {to_str}")
        print(f"      Balanced: {is_balanced}")

    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Fixing FROM/TO Rollup Fields")
    print("="*80)

    # Get the relation property name
    relation_name = get_database_schema()

    if not relation_name:
        print("\n❌ Could not proceed without relation property name")
        exit(1)

    # Add formula fields to Distributions
    success = True
    success = update_from_total_to_formula() and success
    success = update_to_total_to_formula() and success

    # Update Journal Entries rollups
    success = update_journal_entries_rollups(relation_name) and success

    # Update is_balanced formula
    success = update_is_balanced_formula() and success

    # Verify
    verify_fix()

    if success:
        print("\n" + "="*80)
        print("✅ Successfully fixed FROM/TO rollups!")
        print("="*80)
        print("\n📝 What was done:")
        print("   1. Added 'from_amount' formula to Distributions (amount if FROM, else 0)")
        print("   2. Added 'to_amount' formula to Distributions (amount if TO, else 0)")
        print("   3. Updated 'from_total' rollup to sum from_amount")
        print("   4. Updated 'to_total' rollup to sum to_amount")
        print("   5. Updated 'is_balanced' formula (amount == from_total AND amount == to_total)")
        print("\n🎯 Result: Rollups now correctly filter by flow_direction!")
    else:
        print("\n" + "="*80)
        print("⚠️  Some operations failed. Check errors above.")
        print("="*80)
