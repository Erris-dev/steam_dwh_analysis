"""
Gold: game dimension + genre dimension + game-genre bridge.

Reads silver games.parquet and produces star-schema tables:
  - dim_game.parquet      : one row per game, scalar attributes only
  - dim_genre.parquet     : one row per genre (Steam's global IDs as key)
  - game_genre.parquet    : bridge, one row per (appid, genre_id)

Genre note (from bronze exploration): appdetails returns genre descriptions
in the store's language, so the same genre_id can appear with different
descriptions (Action / Экшены / Aksiyon). IDs are global and stable, so we
key on id and pick the most common English-looking description per id.

Gold is fully rebuilt each run (overwrite), so it's idempotent.

Run directly:
    python -m app.gold.build_dim_game
"""

import pandas as pd

from config.settings import SILVER_DIR, GOLD_DIR


def build_dim_game(games):
    """Scalar game attributes only — nested lists are handled separately."""
    cols = [
        "appid", "name", "is_free", "price_final", "currency",
        "release_date", "coming_soon", "required_age",
        "on_windows", "on_mac", "on_linux", "short_description",
    ]
    dim = games[[c for c in cols if c in games.columns]].copy()
    dim = dim.drop_duplicates(subset="appid").reset_index(drop=True)
    return dim


def build_genre_tables(games):
    """Explode the nested genres list into a dim + bridge."""
    # One row per (appid, genre-dict); drop games with no genres
    exploded = games[["appid", "genres"]].explode("genres").dropna(subset=["genres"])

    # Lift the {id, description} dicts into columns
    genre_df = pd.json_normalize(exploded["genres"])
    genre_df["appid"] = exploded["appid"].values
    genre_df = genre_df.rename(columns={"id": "genre_id", "description": "genre_name"})

    # Bridge: distinct (appid, genre_id)
    game_genre = (
        genre_df[["appid", "genre_id"]].drop_duplicates().reset_index(drop=True)
    )

    # Dimension: one row per genre_id. The same id may carry several
    # translated names — pick the most frequent (English dominates an
    # English-heavy sample; for guaranteed English, refetch bronze with l=english).
    dim_genre = (
        genre_df.groupby("genre_id")["genre_name"]
        .agg(lambda s: s.value_counts().index[0])
        .reset_index()
        .sort_values("genre_id")
        .reset_index(drop=True)
    )

    return dim_genre, game_genre


def run():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    games = pd.read_parquet(SILVER_DIR / "games.parquet")
    print(f"Loaded {len(games)} games from silver")

    dim_game = build_dim_game(games)
    dim_genre, game_genre = build_genre_tables(games)

    dim_game.to_parquet(GOLD_DIR / "dim_game.parquet", index=False)
    dim_genre.to_parquet(GOLD_DIR / "dim_genre.parquet", index=False)
    game_genre.to_parquet(GOLD_DIR / "game_genre.parquet", index=False)

    print(f"dim_game:    {len(dim_game)} rows")
    print(f"dim_genre:   {len(dim_genre)} rows")
    print(f"game_genre:  {len(game_genre)} rows (bridge)")

    return dim_game, dim_genre, game_genre


if __name__ == "__main__":
    run()
