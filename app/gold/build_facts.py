"""
Gold: fact tables.

Wraps the clean silver time-series tables as star-schema facts, joining each
to dim_date via the collection date so they can be sliced by time alongside
the game/genre/etc. dimensions.

Produces:
  - fact_player_count.parquet  : grain (appid, date_id)
  - fact_reviews.parquet       : grain (appid, date_id)
  - fact_achievements.parquet  : grain (appid, achievement_name, date_id)

These are REAL rows from actual collection. The time dimension is only as
deep as the scheduled collection has run so far — the schema captures history
from day one and deepens as the daily job accumulates timestamps.

Run directly:
    python -m app.gold.build_facts
"""

import pandas as pd

from config.settings import SILVER_DIR, GOLD_DIR


def _date_id(ts):
    """Convert a UTC timestamp column to a yyyymmdd int date_id (dim_date FK)."""
    return ts.dt.strftime("%Y%m%d").astype(int)


def build_player_count():
    df = pd.read_parquet(SILVER_DIR / "player_counts.parquet")
    df["date_id"] = _date_id(df["fetched_at"])
    fact = df[["appid", "date_id", "fetched_at", "player_count"]].copy()
    return fact.reset_index(drop=True)


def build_reviews():
    df = pd.read_parquet(SILVER_DIR / "reviews.parquet")
    df["date_id"] = _date_id(df["fetched_at"])
    cols = ["appid", "date_id", "fetched_at", "total_reviews", "total_positive",
            "total_negative", "review_score", "positive_ratio", "has_reviews"]
    fact = df[[c for c in cols if c in df.columns]].copy()
    return fact.reset_index(drop=True)


def build_achievements():
    df = pd.read_parquet(SILVER_DIR / "achievements.parquet")
    df["date_id"] = _date_id(df["fetched_at"])
    fact = df[["appid", "achievement_name", "date_id", "fetched_at", "percent"]].copy()
    return fact.reset_index(drop=True)


def run():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    specs = [
        ("fact_player_count", build_player_count),
        ("fact_reviews", build_reviews),
        ("fact_achievements", build_achievements),
    ]

    results = {}
    for name, builder in specs:
        try:
            fact = builder()
            fact.to_parquet(GOLD_DIR / f"{name}.parquet", index=False)
            print(
                f"{name}: {len(fact)} rows "
                f"({fact['date_id'].nunique()} distinct dates)"
            )
            results[name] = fact
        except FileNotFoundError as e:
            print(f"SKIPPED {name}: {e}")

    return results


if __name__ == "__main__":
    run()
