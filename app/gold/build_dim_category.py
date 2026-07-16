"""
Gold: category dimension + game-category bridge.

categories in silver are lists of {id, description} dicts (like genres),
with integer ids. Steam's ids are global and stable, so we key on them
and pick the most common description per id (guards against multilingual
descriptions, same issue as genres).

Produces:
  - dim_category.parquet    : category_id, category_name
  - game_category.parquet   : bridge (appid, category_id)

Run directly:
    python -m app.gold.build_dim_category
"""

import pandas as pd

from config.settings import SILVER_DIR, GOLD_DIR


def run():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    games = pd.read_parquet(SILVER_DIR / "games.parquet")

    exploded = (
        games[["appid", "categories"]]
        .explode("categories")
        .dropna(subset=["categories"])
    )

    cat_df = pd.json_normalize(exploded["categories"])
    cat_df["appid"] = exploded["appid"].values
    cat_df = cat_df.rename(columns={"id": "category_id", "description": "category_name"})

    # Bridge: distinct (appid, category_id)
    game_category = (
        cat_df[["appid", "category_id"]].drop_duplicates().reset_index(drop=True)
    )

    # Dimension: one row per id, most common description wins
    dim_category = (
        cat_df.groupby("category_id")["category_name"]
        .agg(lambda s: s.value_counts().index[0])
        .reset_index()
        .sort_values("category_id")
        .reset_index(drop=True)
    )

    dim_category.to_parquet(GOLD_DIR / "dim_category.parquet", index=False)
    game_category.to_parquet(GOLD_DIR / "game_category.parquet", index=False)

    print(f"dim_category:   {len(dim_category)} rows")
    print(f"game_category:  {len(game_category)} rows (bridge)")

    return dim_category, game_category


if __name__ == "__main__":
    run()
