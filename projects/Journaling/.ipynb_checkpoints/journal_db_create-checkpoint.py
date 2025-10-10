#!/usr/bin/env python3
"""
journal_db_create.py

Creates (or verifies) a "Journals" page and a "Journal" database under it.
Optionally verifies an existing "SoJournal" DB by name.

Usage:
  1) Copy .env.example to .env and fill in:
     - NOTION_TOKEN=secret_xxx
     - LIMOS_ROOT_PAGE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  (optional if JOURNALS_PAGE_ID provided)
     - JOURNALS_PAGE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx    (optional: if omitted, script creates the "Journals" page)
  2) Run:  pip install requests python-dotenv
  3) Run:  python3 journal_db_create.py
"""

import os, sys, time, requests
from dotenv import load_dotenv

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

load_dotenv()
TOKEN = os.getenv("NOTION_TOKEN")
LIMOS_ROOT_PAGE_ID = os.getenv("LIMOS_ROOT_PAGE_ID")
JOURNALS_PAGE_ID = os.getenv("JOURNALS_PAGE_ID")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

def die(msg):
    print(f"[ERROR] {msg}")
    sys.exit(1)

def ensure_ok(resp):
    if not resp.ok:
        die(f"HTTP {resp.status_code}: {resp.text}")

def create_page(parent_page_id: str, title: str, icon_emoji: str = None) -> str:
    payload = {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {
                "title": [{"text": {"content": title}}]
            }
        }
    }
    if icon_emoji:
        payload["icon"] = {"type":"emoji","emoji":icon_emoji}
    r = requests.post(f"{NOTION_API}/pages", headers=HEADERS, json=payload)
    ensure_ok(r)
    data = r.json()
    return data["id"]

def find_database_under_parent(parent_page_id: str, name: str):
    # Notion API lacks a direct "list children" databases endpoint;
    # we use the search API filtered by name and hope for a match.
    # You may narrow by "filter": {"value":"database","property":"object"} if needed.
    r = requests.post(f"{NOTION_API}/search", headers=HEADERS, json={
        "query": name,
        "filter": {"value":"database","property":"object"}
    })
    ensure_ok(r)
    results = r.json().get("results", [])
    for item in results:
        if item.get("object") == "database":
            title_parts = item.get("title", [])
            title_text = "".join(part.get("plain_text","") for part in title_parts)
            if title_text.strip() == name:
                # best-effort match; Notion doesn't expose parent path here.
                return item["id"]
    return None

def create_journal_database(parent_page_id: str) -> str:
    # Define properties for Everyday Journal
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "Journal"}}],
        "icon": {"type":"emoji","emoji":"📖"},
        "properties": {
            "Name": {"title": {}},
            "Date": {"date": {}},
            "Mood": {"select": {"options": [
                {"name":"Happy"},{"name":"Focused"},{"name":"Tired"},{"name":"Stressed"},{"name":"Inspired"}
            ]}},
            "Sleep Hours": {"number": {}},
            "Activities": {"relation": {}},  # user can wire to Tasks DB later
            "Notes": {"relation": {}},       # user can wire to Notes DB later
            "Tags": {"multi_select": {}}
        }
    }
    r = requests.post(f"{NOTION_API}/databases", headers=HEADERS, json=payload)
    ensure_ok(r)
    return r.json()["id"]

def main():
    if not TOKEN:
        die("NOTION_TOKEN missing. Put it in .env")

    journals_page_id = JOURNALS_PAGE_ID
    if not journals_page_id:
        if not LIMOS_ROOT_PAGE_ID:
            die("Either JOURNALS_PAGE_ID or LIMOS_ROOT_PAGE_ID must be provided in .env")
        print("[i] Creating 'Journals' page under LiMOS root…")
        journals_page_id = create_page(LIMOS_ROOT_PAGE_ID, "Journals", icon_emoji="🗒️")
        print(f"[✓] Journals page id: {journals_page_id}")

    # Create Journal database if not found
    print("[i] Ensuring 'Journal' database exists…")
    existing = find_database_under_parent(journals_page_id, "Journal")
    if existing:
        print(f"[✓] 'Journal' DB already exists: {existing}")
        journal_db_id = existing
    else:
        journal_db_id = create_journal_database(journals_page_id)
        print(f"[✓] Created 'Journal' DB: {journal_db_id}")

    print("\n[RESULT]")
    print(f"JOURNALS_PAGE_ID={journals_page_id}")
    print(f"JOURNAL_DB_ID={journal_db_id}")
    print("\nNote: If you already have a SoJournal DB, you can set SOJOURNAL_DB_ID in the env for the daily runner.")

if __name__ == '__main__':
    main()
