"""
Bronze ingestion: SteamSpy owner estimates, playtime, and tags.

Third-party source (steamspy.com) — the only source here for estimated
owner counts and median playtime, which Valve's official API doesn't
expose. Saves a dated raw JSON snapshot per run. No API key required.

Run directly:
    python -m app.ingestion.fetch_steamspy
"""

import json
import time
from datetime import datetime, timezone

import requests

from config.settings import STEAMSPY_DIR, REQUEST_TIMEOUT

API_URL = "https://steamspy.com/api.php"
CHECKPOINT_EVERY = 10


def _output_path():
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return STEAMSPY_DIR / f"steamspy_{date_str}.json"


def _save(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)


def _load_existing(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def run(target_apps):
    STEAMSPY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _output_path()

    all_steamspy = _load_existing(out_path)
    done_ids = {r.get("appid") for r in all_steamspy}
    if done_ids:
        print(f"Resuming: {len(done_ids)} apps already fetched today.")

    for i, app in enumerate(target_apps):
        appid = app["appid"]
        name = app["name"]

        if appid in done_ids:
            continue

        try:
            resp = requests.get(
                API_URL,
                params={"request": "appdetails", "appid": appid},
                timeout=REQUEST_TIMEOUT,
            )
            time.sleep(1)  # SteamSpy rate-limits too

            if resp.status_code == 200:
                data = resp.json()
                if data:
                    data["extracted_timestamp"] = datetime.now(timezone.utc).isoformat()
                    all_steamspy.append(data)
                    print(f"✓ {name}: owners ~{data.get('owners', 'N/A')}")
                else:
                    print(f"✗ No SteamSpy data for {name}")
            else:
                print(f"✗ Failed {name}: HTTP {resp.status_code}")

        except Exception as e:
            print(f"✗ Error on {appid}: {e}")

        if (i + 1) % CHECKPOINT_EVERY == 0:
            _save(all_steamspy, out_path)

    _save(all_steamspy, out_path)
    print(f"\nDone. {len(all_steamspy)} SteamSpy records in {out_path}")
    return all_steamspy


if __name__ == "__main__":
    from app.ingestion.fetch_master_list import load_target_apps

    run(load_target_apps())
