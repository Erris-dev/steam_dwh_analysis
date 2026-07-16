"""
Silver transform: achievement completion percentages.

Reads the append-only bronze CSV and produces a clean, typed, deduplicated
fact table: data/silver/achievements.parquet
(one row per game per achievement per collection timestamp).

Cleaning rules:
  - parse fetched_at -> real UTC datetime
  - coerce percent to numeric; normalise to a 0-100 scale defensively
    (Steam returns 0-100, but if a snapshot ever looks like 0-1 we scale it up)
  - drop rows with null percent or missing achievement_name
  - dedupe on the fact grain (appid, achievement_name, fetched_at)
  - drop the game `name` column (it's a dimension attribute, not a fact measure)

Silver is fully rebuilt each run (overwrite), so it's idempotent.

Run directly:
    python -m app.transform.transform_achievements
"""

import pandas as pd

from config.settings import ACHIEVEMENTS_DIR, SILVER_DIR


def run():
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    src = ACHIEVEMENTS_DIR / "achievement_percentages.csv"

    if not src.exists():
        raise FileNotFoundError(f"No bronze achievements at {src}. Run bronze first.")

    df = pd.read_csv(src)
    print(f"Loaded {len(df)} raw rows")

    # --- types ---
    df["fetched_at"] = pd.to_datetime(df["fetched_at"], utc=True, errors="coerce")
    df["percent"] = pd.to_numeric(df["percent"], errors="coerce")

    # --- drop bad rows ---
    before = len(df)
    df = df[df["fetched_at"].notna()]
    df = df[df["percent"].notna()]
    df = df[df["achievement_name"].notna() & (df["achievement_name"].str.len() > 0)]
    print(f"Dropped {before - len(df)} invalid rows")

    # --- normalise percent to 0-100 defensively ---
    # Steam returns 0-100. If the whole column looks like 0-1 (max <= 1),
    # it's on a fractional scale and we scale up. Guard against an empty frame.
    if len(df) and df["percent"].max() <= 1:
        print("percent looked like 0-1 scale — scaling up to 0-100")
        df["percent"] = df["percent"] * 100
    # Clip stray out-of-range values into [0, 100]
    df["percent"] = df["percent"].clip(lower=0, upper=100)

    # --- dedupe on the fact grain ---
    before = len(df)
    df = df.drop_duplicates(
        subset=["appid", "achievement_name", "fetched_at"], keep="last"
    )
    if before - len(df):
        print(f"Dropped {before - len(df)} duplicate rows")

    # --- fact table: grain keys + measure, no dimension attributes ---
    fact = df[["appid", "achievement_name", "percent", "fetched_at"]].reset_index(
        drop=True
    )

    out_path = SILVER_DIR / "achievements.parquet"
    fact.to_parquet(out_path, index=False)
    print(
        f"Wrote {len(fact)} rows -> {out_path} "
        f"({fact['appid'].nunique()} games, "
        f"{fact['fetched_at'].nunique()} distinct timestamps)"
    )
    return fact


if __name__ == "__main__":
    run()
