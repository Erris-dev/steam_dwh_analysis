"""
Bronze ingestion: live concurrent player counts (time series).

Each run appends one row per app to a growing CSV — the value of this
source comes from running it repeatedly on a schedule (e.g. hourly/daily
via Task Scheduler) to build a real time series. No API key required.

Run directly:
    python -m app.ingestion.fetch_player_counts
"""

import time
from datetime import datetime, timezone

import pandas as pd
import requests

from config.settings import PLAYER_COUNTS_DIR, REQUEST_TIMEOUT

API_URL = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"


def run(target_apps):
    PLAYER_COUNTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PLAYER_COUNTS_DIR / "player_counts.csv"

    rows = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    for app in target_apps:
        appid = app["appid"]
        name = app["name"]

        try:
            resp = requests.get(
                API_URL, params={"appid": appid}, timeout=REQUEST_TIMEOUT
            )
            time.sleep(1)

            if resp.status_code == 200:
                data = resp.json().get("response", {})
                if data.get("result") == 1:
                    rows.append(
                        {
                            "appid": appid,
                            "name": name,
                            "player_count": data.get("player_count"),
                            "fetched_at": fetched_at,
                        }
                    )
                    print(f"✓ {name}: {data.get('player_count'):,} players")
                else:
                    print(f"✗ No data for {name}")
            else:
                print(f"✗ Failed for {name}: HTTP {resp.status_code}")

        except Exception as e:
            print(f"✗ Error on {appid}: {e}")

    if rows:
        df = pd.DataFrame(rows)
        # True append: new rows only, header written once
        df.to_csv(out_path, mode="a", header=not out_path.exists(), index=False)
        print(f"\nAppended {len(rows)} snapshot rows to {out_path}")

    return rows


if __name__ == "__main__":
    from app.ingestion.fetch_master_list import load_target_apps

    run(load_target_apps())
