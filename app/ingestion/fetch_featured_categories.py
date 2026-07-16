"""
Bronze ingestion: Steam store featured/specials/top-sellers snapshot.

Single API call, no appid loop and no key needed. Each run writes a
timestamped JSON file so sale/featured history accumulates across runs.
Region-locked to cc=us (prices in USD).

Run directly:
    python -m app.ingestion.fetch_featured_categories
"""

import json
from datetime import datetime, timezone

import requests

from config.settings import DATA_DIR, REQUEST_TIMEOUT

API_URL = "https://store.steampowered.com/api/featuredcategories"
FEATURED_DIR = DATA_DIR / "featured_categories"


def run():
    FEATURED_DIR.mkdir(parents=True, exist_ok=True)

    resp = requests.get(API_URL, params={"cc": "us"}, timeout=REQUEST_TIMEOUT)

    if resp.status_code != 200:
        print(f"Failed: HTTP {resp.status_code}")
        return None

    data = resp.json()
    data["extracted_timestamp"] = datetime.now(timezone.utc).isoformat()

    # Timestamped filename so history isn't overwritten between runs
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    out_path = FEATURED_DIR / f"featured_{date_str}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"Saved featured categories snapshot to {out_path}")
    return data


if __name__ == "__main__":
    run()
