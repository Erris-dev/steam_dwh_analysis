"""
Bronze ingestion: rich storefront metadata per game (appdetails).

Fetches nested JSON (genres, price, developers, release date, ...) for each
target app and saves a dated raw JSON snapshot. Checkpoints every N apps so
a crash mid-run doesn't lose everything.

Run directly:
    python -m app.ingestion.fetch_app_details
"""

import json
import time
from datetime import datetime, timezone

import requests

from app.ingestion.progress import StatusLine
from config.settings import (
    APP_DETAILS_DIR,
    REQUEST_TIMEOUT,
    SLEEP_BETWEEN_CALLS,
)

API_URL = "https://store.steampowered.com/api/appdetails"
CHECKPOINT_EVERY = 10  # save progress every N apps


def _output_path():
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return APP_DETAILS_DIR / f"game_details_{date_str}.json"


def _save(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)


def _load_existing(path):
    """Resume support: load records already fetched today, if any."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def run(target_apps):
    APP_DETAILS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _output_path()

    detailed_games = _load_existing(out_path)
    done_ids = {g.get("source_appid") for g in detailed_games}
    if done_ids:
        print(f"Resuming: {len(done_ids)} apps already fetched today.")

    with StatusLine("Fetching storefront details", skip_label="no storefront page") as status:
        for i, app in enumerate(target_apps):
            app_id = app["appid"]
            app_name = app["name"]

            if app_id in done_ids:
                continue

            try:
                resp = requests.get(
                    API_URL, params={"appids": app_id}, timeout=REQUEST_TIMEOUT
                )
                time.sleep(SLEEP_BETWEEN_CALLS)  # storefront API rate-limits aggressively

                if resp.status_code == 200:
                    entry = resp.json().get(str(app_id), {})

                    if entry.get("success"):
                        data = entry["data"]
                        data["extracted_timestamp"] = datetime.now(
                            timezone.utc
                        ).isoformat()
                        data["source_appid"] = app_id
                        detailed_games.append(data)
                        status.log(f"✓ {app_name} (ID: {app_id})")
                    else:
                        status.skip()

                elif resp.status_code == 429:
                    status.log("Rate limited — cooling down 30s...")
                    time.sleep(30)

                else:
                    status.log(f"✗ Failed {app_name}: HTTP {resp.status_code}")

            except Exception as e:
                status.log(f"✗ Error on {app_id}: {e}")

            # Checkpoint so a crash loses at most CHECKPOINT_EVERY apps of work
            if (i + 1) % CHECKPOINT_EVERY == 0:
                _save(detailed_games, out_path)

    _save(detailed_games, out_path)
    print(f"\nDone. {len(detailed_games)} detailed records in {out_path}")
    return detailed_games


if __name__ == "__main__":
    from app.ingestion.fetch_master_list import load_target_apps

    run(load_target_apps())
