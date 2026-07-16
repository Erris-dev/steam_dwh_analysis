"""
Silver transform: reviews.

Reads the latest bronze reviews JSON snapshot and produces a clean, typed
fact table: data/silver/reviews.parquet
(one row per game per collection timestamp).

The useful aggregates live in each record's nested `query_summary` dict;
the per-review text list is ignored here (that's an NLP concern for later).

Confirmed against bronze data:
  - query_summary fields: num_reviews, review_score, review_score_desc,
    total_positive, total_negative, total_reviews
  - num_reviews is the count returned in THIS response (capped at num_per_page,
    i.e. 20) — NOT a real metric. We use total_reviews (lifetime) instead.
  - ~39% of sampled games have 0 reviews ("No user reviews"); has_reviews
    flags the ones worth analysing, and positive_ratio is NaN for the rest.

Cleaning rules:
  - lift query_summary -> flat columns
  - attach appid + fetched_at from the pipeline metadata
  - parse fetched_at -> real UTC datetime
  - coerce count columns to numeric
  - derive positive_ratio (NaN when no reviews) + has_reviews flag
  - dedupe on the fact grain (appid, fetched_at)

Silver is fully rebuilt each run (overwrite), so it's idempotent.

Run directly:
    python -m app.transform.transform_reviews
"""

import json

import pandas as pd

from config.settings import REVIEWS_DIR, SILVER_DIR

# query_summary measures we keep (num_reviews deliberately excluded — it's the
# capped per-response count, not a real metric)
MEASURE_COLS = [
    "total_reviews",
    "total_positive",
    "total_negative",
    "review_score",
    "review_score_desc",
]


def load_latest_bronze():
    """Load the most recent reviews JSON snapshot."""
    files = sorted(REVIEWS_DIR.glob("reviews_*.json"))
    if not files:
        raise FileNotFoundError(
            f"No reviews snapshots in {REVIEWS_DIR}. Run bronze first."
        )
    with open(files[-1], encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records from {files[-1].name}")
    return records


def run():
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    records = load_latest_bronze()

    # Lift the nested query_summary dict into flat columns
    summary = pd.json_normalize([r.get("query_summary", {}) for r in records])

    # Attach pipeline metadata (the grain keys)
    summary["appid"] = [r.get("source_appid") for r in records]
    summary["fetched_at"] = [r.get("extracted_timestamp") for r in records]

    # --- types ---
    summary["fetched_at"] = pd.to_datetime(
        summary["fetched_at"], utc=True, errors="coerce"
    )
    for col in ["total_reviews", "total_positive", "total_negative", "review_score"]:
        if col in summary:
            summary[col] = pd.to_numeric(summary[col], errors="coerce")

    # --- select grain keys + measures ---
    keep = ["appid", "fetched_at"] + [c for c in MEASURE_COLS if c in summary]
    fact = summary[keep].copy()

    # --- derived measures ---
    # positive share, guarded against divide-by-zero (0-review games -> NaN)
    fact["positive_ratio"] = (
        fact["total_positive"] / fact["total_reviews"]
    ).where(fact["total_reviews"] > 0)
    # flag games that actually have reviews (~39% of the sample don't)
    fact["has_reviews"] = fact["total_reviews"] > 0

    # --- drop rows with no valid timestamp, then dedupe on grain ---
    fact = fact[fact["fetched_at"].notna()]
    before = len(fact)
    fact = fact.drop_duplicates(subset=["appid", "fetched_at"], keep="last")
    if before - len(fact):
        print(f"Dropped {before - len(fact)} duplicate (appid, fetched_at) rows")

    fact = fact.reset_index(drop=True)

    out_path = SILVER_DIR / "reviews.parquet"
    fact.to_parquet(out_path, index=False)
    print(
        f"Wrote {len(fact)} rows -> {out_path} "
        f"({int(fact['has_reviews'].sum())} with reviews, "
        f"{fact['fetched_at'].nunique()} distinct timestamps)"
    )
    return fact


if __name__ == "__main__":
    run()
