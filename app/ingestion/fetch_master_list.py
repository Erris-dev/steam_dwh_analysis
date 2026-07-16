"""
Bronze ingestion: Steam master app catalog.

Fetches the full list of games from IStoreService/GetAppList (paginated),
saves a dated Parquet snapshot to the bronze layer, and exposes
load_target_apps() for the other ingestion scripts to reuse.

Target selection combines two pools:
  1. POPULAR — SteamSpy's top-100 lists (guaranteed-active games with
     meaningful player counts, reviews, and price history)
  2. RANDOM  — a seeded random sample across the whole catalog
     (breadth: indie/older/obscure titles so analysis isn't only about hits)

Run directly:
    python -m app.ingestion.fetch_master_list
"""

import time
from datetime import datetime, timezone

import pandas as pd
import requests

from config.settings import (
    STEAM_API_KEY,
    MASTER_LIST_DIR,
    REQUEST_TIMEOUT,
    TARGET_APP_COUNT,
)

API_URL = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
STEAMSPY_URL = "https://steamspy.com/api.php"
PAGE_SIZE = 10_000  # max 50k per call; 10k keeps responses snappy

RANDOM_SEED = 42  # fixed seed -> same random sample every run (reproducible)
POPULAR_SHARE = 0.4  # fraction of targets taken from SteamSpy top lists


def fetch_all_apps():
    """Fetch the complete game catalog, following pagination via last_appid."""
    all_apps = []
    last_appid = 0

    while True:
        params = {
            "key": STEAM_API_KEY,
            "max_results": PAGE_SIZE,
            "last_appid": last_appid,
            "include_games": True,
        }
        resp = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            raise RuntimeError(f"Master list fetch failed: HTTP {resp.status_code}")

        data = resp.json().get("response", {})
        apps = data.get("apps", [])
        if not apps:
            break

        all_apps.extend(apps)
        last_appid = apps[-1]["appid"]
        print(f"  ...fetched {len(all_apps)} apps so far (last_appid={last_appid})")

        if not data.get("have_more_results", False):
            break

        time.sleep(1)  # be polite between pages

    return all_apps


def save_master_list(apps):
    """Save a dated Parquet snapshot so history isn't overwritten between runs."""
    MASTER_LIST_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(apps)
    df["ingested_at"] = datetime.now(timezone.utc)

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    out_path = MASTER_LIST_DIR / f"master_app_list_{date_str}.parquet"
    df.to_parquet(out_path, index=False)

    print(f"Saved {len(df)} rows to {out_path}")
    return out_path


def load_latest_master_list():
    """Load the most recent Parquet snapshot from disk (no API call)."""
    snapshots = sorted(MASTER_LIST_DIR.glob("master_app_list_*.parquet"))
    if not snapshots:
        raise FileNotFoundError(
            f"No master list snapshots found in {MASTER_LIST_DIR}. "
            "Run fetch_master_list first."
        )
    return pd.read_parquet(snapshots[-1])


def _fetch_steamspy_top(request_name):
    """Fetch one SteamSpy top-100 list; returns {appid: name} or {} on failure."""
    try:
        resp = requests.get(
            STEAMSPY_URL, params={"request": request_name}, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 200:
            return {
                int(appid): info.get("name", "")
                for appid, info in resp.json().items()
            }
    except Exception as e:
        print(f"  (SteamSpy {request_name} unavailable: {e})")
    return {}


def load_target_apps(count=None):
    """
    Return the list of apps the other ingestion scripts should process,
    as [{'appid': ..., 'name': ...}, ...].

    Blend of SteamSpy top lists (popular, data-rich games) and a seeded
    random sample of the full catalog (breadth). Falls back to pure
    random sampling if SteamSpy is unreachable.
    """
    count = count or TARGET_APP_COUNT
    df = load_latest_master_list()

    # Drop junk entries (empty names: tools, delisted items, placeholders)
    df = df[df["name"].str.strip().astype(bool)]
    catalog_ids = set(df["appid"])

    # --- Pool 1: popular games from SteamSpy top lists ---
    print("Selecting targets: fetching SteamSpy top lists...")
    popular = {}
    popular.update(_fetch_steamspy_top("top100in2weeks"))
    popular.update(_fetch_steamspy_top("top100forever"))

    # Keep only appids that exist in our catalog (consistency with master list)
    popular = {aid: nm for aid, nm in popular.items() if aid in catalog_ids}

    n_popular = min(len(popular), int(count * POPULAR_SHARE))
    popular_ids = list(popular.keys())[:n_popular]

    # --- Pool 2: seeded random sample from the rest of the catalog ---
    remaining = df[~df["appid"].isin(popular_ids)]
    n_random = count - len(popular_ids)
    random_sample = remaining.sample(
        n=min(n_random, len(remaining)), random_state=RANDOM_SEED
    )

    targets = [
        {"appid": aid, "name": popular[aid]} for aid in popular_ids
    ] + random_sample[["appid", "name"]].to_dict("records")

    print(
        f"Targets: {len(popular_ids)} popular + {len(random_sample)} random "
        f"= {len(targets)} apps"
    )
    return targets


def run():
    """Full ingestion: fetch from API, save snapshot, return target apps."""
    print("Fetching master application index from Steam...")
    apps = fetch_all_apps()
    print(f"Retrieved {len(apps)} total applications.")

    save_master_list(apps)
    return load_target_apps()


if __name__ == "__main__":
    run()