"""
Silver transform: games.

Reads the latest bronze appdetails snapshot and produces one clean, flat,
typed table: data/silver/games.parquet (one row per game).

Cleaning rules (derived from bronze exploration):
  - keep only type == "game", dedupe on appid (latest extracted_timestamp wins)
  - release_date: parse "%d %b, %Y" -> date; unparseable -> NaT; keep coming_soon
  - price: extract price_final (dollars) + currency; NaN when absent.
    is_free kept as an INDEPENDENT column — many non-free games also lack a
    price_overview, so price must never be derived from is_free or vice versa.
  - required_age: coerce to numeric (bronze had it as both int and str)
  - short_description: strip HTML tags
  - platforms: split into on_windows / on_mac / on_linux bools
  - nested lists (genres, developers, publishers, categories) pass through
    untouched — gold explodes them into dims/bridges.

Silver is fully rebuilt each run (overwrite), so it's idempotent.

Run directly:
    python -m app.transform.transform_games
"""

import json
import re

import pandas as pd

from config.settings import APP_DETAILS_DIR, SILVER_DIR

HTML_TAG = re.compile(r"<[^>]+>")

# Flat columns carried straight through (renamed where noted)
PASSTHROUGH = ["name", "is_free", "type"]
# Nested list columns kept as-is for gold to model later
NESTED = ["genres", "developers", "publishers", "categories"]


def load_latest_bronze():
    """Load the most recent appdetails JSON snapshot into a DataFrame."""
    files = sorted(APP_DETAILS_DIR.glob("game_details_*.json"))
    if not files:
        raise FileNotFoundError(
            f"No appdetails snapshots in {APP_DETAILS_DIR}. Run bronze first."
        )
    with open(files[-1], encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records from {files[-1].name}")
    return pd.DataFrame(records)


def strip_html(text):
    if not isinstance(text, str):
        return None
    return HTML_TAG.sub("", text).strip()


def transform(df):
    # --- filter + dedupe ---
    df = df[df["type"] == "game"].copy()
    df = df.rename(columns={"source_appid": "appid"})
    df = df.sort_values("extracted_timestamp").drop_duplicates(
        subset="appid", keep="last"
    )
    print(f"{len(df)} games after filter + dedupe")

    out = pd.DataFrame()
    out["appid"] = df["appid"]
    for col in PASSTHROUGH:
        out[col] = df[col]

    # --- release_date: dict column -> date + coming_soon flag ---
    rd = pd.json_normalize(df["release_date"]).set_index(df.index)
    out["coming_soon"] = rd["coming_soon"].fillna(False)
    out["release_date"] = pd.to_datetime(
        rd["date"], format="%d %b, %Y", errors="coerce"
    )

    # --- price: independent of is_free; NaN when absent ---
    price = pd.json_normalize(df["price_overview"]).set_index(df.index)
    out["price_final"] = price.get("final") / 100 if "final" in price else pd.NA
    out["currency"] = price.get("currency") if "currency" in price else pd.NA

    # --- required_age: mixed int/str in bronze -> numeric ---
    out["required_age"] = pd.to_numeric(df["required_age"], errors="coerce")

    # --- short_description: strip HTML ---
    out["short_description"] = df["short_description"].map(strip_html)

    # --- platforms: dict -> three bools ---
    plat = pd.json_normalize(df["platforms"]).set_index(df.index)
    out["on_windows"] = plat.get("windows", False)
    out["on_mac"] = plat.get("mac", False)
    out["on_linux"] = plat.get("linux", False)

    # --- nested lists pass through for gold ---
    for col in NESTED:
        out[col] = df[col]

    return out.reset_index(drop=True)


def run():
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    df = load_latest_bronze()
    games = transform(df)

    out_path = SILVER_DIR / "games.parquet"
    games.to_parquet(out_path, index=False)
    print(f"Wrote {len(games)} rows -> {out_path}")
    return games


if __name__ == "__main__":
    run()
