#!/usr/bin/env python3
"""
daily_entries_cron.py

Creates daily pages for both Journal and SoJournal (if provided) with a "primary template" layout.
Intended to be run at midnight via launchd/cron/systemd or any scheduler.

Environment (.env):
  NOTION_TOKEN=secret_xxx
  JOURNAL_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  SOJOURNAL_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   (optional, if you have a travel journal DB)
  TIMEZONE=America/Phoenix (optional; default UTC)
"""

import os, sys, json, requests, datetime
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

load_dotenv()
TOKEN = os.getenv("NOTION_TOKEN")
JOURNAL_DB_ID = os.getenv("JOURNAL_DB_ID")
SOJOURNAL_DB_ID = os.getenv("SOJOURNAL_DB_ID")
TZ = os.getenv("TIMEZONE", "UTC")

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

def today_block_title(dt):
    return dt.strftime("@%B %d, %Y")

def build_journal_children():
    return [
        {"object":"block","type":"callout","callout":{
            "icon":{"emoji":"💡"},
            "rich_text":[{"type":"text","text":{"content":"Notion Tip: Type '/' and choose 'Template' to make this your default daily layout."}}],
            "color":"gray_background"
        }},
        {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Intentions"}}]}},
        {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":"..."}}]}},
        {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":"..."}}]}},
        {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Happenings"}}]}},
        {"object":"block","type":"paragraph","paragraph":{"rich_text":[]}},
        {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Grateful for"}}]}},
        {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":"..."}}]}},
        {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Action Items"}}]}},
        {"object":"block","type":"to_do","to_do":{"rich_text":[{"type":"text","text":{"content":"..."}}],"checked":False}}
    ]

def create_daily_page(database_id: str, date_iso: str, display_title: str):
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"type":"text","text":{"content":display_title}}]},
            "Date": {"date": {"start": date_iso}}
        },
        "children": build_journal_children()
    }
    r = requests.post(f"{NOTION_API}/pages", headers=HEADERS, json=payload)
    ensure_ok(r)
    return r.json()["url"]

def main():
    if not TOKEN:
        die("NOTION_TOKEN missing in environment")
    now = datetime.datetime.now(ZoneInfo(TZ))
    date_iso = now.date().isoformat()
    title = today_block_title(now)

    created = {}

    if JOURNAL_DB_ID:
        url = create_daily_page(JOURNAL_DB_ID, date_iso, title)
        created["Journal"] = url

    if SOJOURNAL_DB_ID:
        url = create_daily_page(SOJOURNAL_DB_ID, date_iso, title)
        created["SoJournal"] = url

    if not created:
        die("Neither JOURNAL_DB_ID nor SOJOURNAL_DB_ID set; nothing to create.")

    print("[✓] Created daily pages:")
    for k, v in created.items():
        print(f"  - {k}: {v}")

if __name__ == "__main__":
    main()
