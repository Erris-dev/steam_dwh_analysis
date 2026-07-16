"""
Bronze ingestion: review summaries + a sample of recent review text.

Saves a dated raw JSON snapshot per run (so review totals become a
time series across runs). Checkpoints every N apps — this is the loop
that crashed mid-run in the notebook and lost all progress.
No API key required.

Run directly:
    python -m app.ingestion.fetch_reviews
"""

import json
import time
from datetime import datetime, timezone

import requests

from config.settings import REVIEWS_DIR, REQUEST_TIMEOUT

CHECKPOINT_EVERY = 10


def _output_path():
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return REVIEWS_DIR / f"reviews_{date_str}.json"


def _save(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)


def _load_existing(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def run(target_apps):
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _output_path()

    all_reviews = _load_existing(out_path)
    done_ids = {r.get("source_appid") for r in all_reviews}
    if done_ids:
        print(f"Resuming: {len(done_ids)} apps already fetched today.")

    for i, app in enumerate(target_apps):
        appid = app["appid"]
        name = app["name"]

        if appid in done_ids:
            continue

        url = f"https://store.steampowered.com/appreviews/{appid}"
        params = {"json": 1, "num_per_page": 20, "filter": "recent"}

        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            time.sleep(1)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") == 1:
                    data["source_appid"] = appid
                    data["source_name"] = name
                    data["extracted_timestamp"] = datetime.now(timezone.utc).isoformat()
                    all_reviews.append(data)
                    total = data.get("query_summary", {}).get("total_reviews", 0)
                    print(f"✓ {name}: {total} total reviews")
                else:
                    print(f"✗ No review data for {name}")
            else:
                print(f"✗ Failed {name}: HTTP {resp.status_code}")

        except Exception as e:
            print(f"✗ Error on {appid}: {e}")

        if (i + 1) % CHECKPOINT_EVERY == 0:
            _save(all_reviews, out_path)

    _save(all_reviews, out_path)
    print(f"\nDone. {len(all_reviews)} review records in {out_path}")
    return all_reviews


if __name__ == "__main__":
    from app.ingestion.fetch_master_list import load_target_apps

    run(load_target_apps())
