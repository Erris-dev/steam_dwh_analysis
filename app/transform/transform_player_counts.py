"""
Silver transform: player counts.

Reads the append-only bronze CSV and produces a clean, typed, deduplicated
fact table: data/silver/player_counts.parquet
(one row per game per collection timestamp).

Cleaning rules:
  - parse fetched_at -> real UTC datetime
  - drop rows with null/negative player_count (failed fetches)
  - dedupe on (appid, fetched_at) in case a run was accidentally repeated
  - drop the name column (belongs in the game dimension, not the fact table)

Silver is fully rebuilt each run (overwrite), so it's idempotent.

Run directly:
    python -m app.transform.transform_player_counts
"""

import pandas as pd

from config.settings import PLAYER_COUNTS_DIR, SILVER_DIR


def run():
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    src = PLAYER_COUNTS_DIR / "player_counts.csv"

    if not src.exists():
        raise FileNotFoundError(f"No bronze player counts at {src}. Run bronze first.")

    df = pd.read_csv(src)
    print(f"Loaded {len(df)} raw rows")

    # --- types ---
    df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True, errors="coerce")
    df["player_count"] = pd.to_numeric(df["player_count"], errors="coerce")

    # --- drop bad rows: unparseable timestamp or missing/negative count ---
    before = len(df)
    df = df[df["fetched_at"].notna()]
    df = df[df["player_count"].notna() & (df["player_count"] >= 0)]
    df["player_count"] = df["player_count"].astype("int64")
    print(f"Dropped {before - len(df)} invalid rows")

    # --- dedupe on the fact grain: one row per game per timestamp ---
    before = len(df)
    df = df.drop_duplicates(subset=["appid", "fetched_at"], keep="last")
    if before - len(df):
        print(f"Dropped {before - len(df)} duplicate (appid, fetched_at) rows")

    # --- fact table: keep the grain keys + measure, drop name (it's a dim attr) ---
    fact = df[["appid", "fetched_at", "player_count"]].reset_index(drop=True)

    out_path = SILVER_DIR / "player_counts.parquet"
    fact.to_parquet(out_path, index=False)
    print(
        f"Wrote {len(fact)} rows -> {out_path} "
        f"({fact['fetched_at'].nunique()} distinct timestamps, "
        f"{fact['appid'].nunique()} games)"
    )
    return fact


if __name__ == "__main__":
    run()
