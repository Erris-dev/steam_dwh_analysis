"""
Bronze ingestion: global achievement completion percentages.

Flat rows appended to a growing CSV (appid + achievement + percent +
fetched_at), so completion rates become a time series across runs.
No API key required.

Note: HTTP 403 from this endpoint is NOT an error — it's Steam's response
for apps that have no achievement data at all (pre-achievement era games).

Run directly:
    python -m app.ingestion.fetch_achievements
"""

import time
from datetime import datetime, timezone

import pandas as pd
import requests

from app.ingestion.progress import StatusLine
from config.settings import ACHIEVEMENTS_DIR, REQUEST_TIMEOUT

API_URL = (
    "https://api.steampowered.com/"
    "ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/"
)


def run(target_apps):
    ACHIEVEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ACHIEVEMENTS_DIR / "achievement_percentages.csv"

    rows = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    with StatusLine(
        "Fetching achievement percentages", skip_label="no achievement data"
    ) as status:
        for app in target_apps:
            appid = app["appid"]
            name = app["name"]

            try:
                resp = requests.get(
                    API_URL, params={"gameid": appid}, timeout=REQUEST_TIMEOUT
                )
                time.sleep(1)

                if resp.status_code == 200:
                    achievements = (
                        resp.json()
                        .get("achievementpercentages", {})
                        .get("achievements", [])
                    )
                    for ach in achievements:
                        rows.append(
                            {
                                "appid": appid,
                                "name": name,
                                "achievement_name": ach.get("name"),
                                "percent": ach.get("percent"),
                                "fetched_at": fetched_at,
                            }
                        )
                    status.log(f"✓ {name}: {len(achievements)} achievements")

                elif resp.status_code == 403:
                    # Legitimate "no data" outcome, not a pipeline failure
                    status.skip()

                else:
                    status.log(f"✗ Failed {name}: HTTP {resp.status_code}")

            except Exception as e:
                status.log(f"✗ Error on {appid}: {e}")

    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(out_path, mode="a", header=not out_path.exists(), index=False)
        print(f"\nAppended {len(rows)} rows to {out_path}")

    return rows


if __name__ == "__main__":
    from app.ingestion.fetch_master_list import load_target_apps

    run(load_target_apps())
