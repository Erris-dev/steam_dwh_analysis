"""
Gold: date dimension.

A generated calendar table (not sourced from any API) that the fact tables
(player counts, reviews, achievements) join against for time-based analysis.

Spans from the earliest game release date in the data through today, so it
covers both release-date joins and the growing time-series of collections.

Produces:
  - dim_date.parquet : date_id (yyyymmdd int), date, year, quarter, month,
                       day, day_of_week, day_name, is_weekend

Run directly:
    python -m app.gold.build_dim_date
"""

from datetime import date

import pandas as pd

from config.settings import SILVER_DIR, GOLD_DIR


def run():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # Range: earliest known release date (fallback 2000) -> today
    games = pd.read_parquet(SILVER_DIR / "games.parquet")
    min_release = games["release_date"].min()
    start = (
        min_release.date()
        if pd.notna(min_release)
        else date(2000, 1, 1)
    )
    end = date.today()

    dates = pd.date_range(start=start, end=end, freq="D")
    dim = pd.DataFrame({"date": dates})

    dim["date_id"] = dim["date"].dt.strftime("%Y%m%d").astype(int)
    dim["year"] = dim["date"].dt.year
    dim["quarter"] = dim["date"].dt.quarter
    dim["month"] = dim["date"].dt.month
    dim["day"] = dim["date"].dt.day
    dim["day_of_week"] = dim["date"].dt.dayofweek  # Mon=0
    dim["day_name"] = dim["date"].dt.day_name()
    dim["is_weekend"] = dim["day_of_week"] >= 5

    dim = dim[
        ["date_id", "date", "year", "quarter", "month", "day",
         "day_of_week", "day_name", "is_weekend"]
    ]

    dim.to_parquet(GOLD_DIR / "dim_date.parquet", index=False)
    print(f"dim_date: {len(dim)} rows ({start} -> {end})")
    return dim


if __name__ == "__main__":
    run()
