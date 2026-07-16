"""
Gold: developer and publisher dimensions + bridges.

developers/publishers in silver are plain lists of name strings (no IDs),
so we generate stable surrogate integer IDs via a sorted factorize.

Produces:
  - dim_developer.parquet   : developer_id, developer_name
  - game_developer.parquet  : bridge (appid, developer_id)
  - dim_publisher.parquet   : publisher_id, publisher_name
  - game_publisher.parquet  : bridge (appid, publisher_id)

Run directly:
    python -m app.gold.build_dim_developer_publisher
"""

import pandas as pd

from config.settings import SILVER_DIR, GOLD_DIR


def build_name_dim(games, source_col, id_col, name_col):
    """Explode a list-of-strings column into a dim (surrogate id) + bridge."""
    exploded = (
        games[["appid", source_col]]
        .explode(source_col)
        .dropna(subset=[source_col])
    )
    exploded = exploded.rename(columns={source_col: name_col})
    # strip stray whitespace, drop any empties left behind
    exploded[name_col] = exploded[name_col].str.strip()
    exploded = exploded[exploded[name_col].str.len() > 0]

    # Dimension: unique names, sorted, with a generated surrogate id
    names = pd.Series(sorted(exploded[name_col].unique()), name=name_col)
    dim = names.to_frame()
    dim[id_col] = range(1, len(dim) + 1)
    dim = dim[[id_col, name_col]]

    # Bridge: map names back to ids
    name_to_id = dict(zip(dim[name_col], dim[id_col]))
    bridge = exploded.copy()
    bridge[id_col] = bridge[name_col].map(name_to_id)
    bridge = bridge[["appid", id_col]].drop_duplicates().reset_index(drop=True)

    return dim, bridge


def run():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    games = pd.read_parquet(SILVER_DIR / "games.parquet")

    dim_dev, game_dev = build_name_dim(
        games, "developers", "developer_id", "developer_name"
    )
    dim_pub, game_pub = build_name_dim(
        games, "publishers", "publisher_id", "publisher_name"
    )

    dim_dev.to_parquet(GOLD_DIR / "dim_developer.parquet", index=False)
    game_dev.to_parquet(GOLD_DIR / "game_developer.parquet", index=False)
    dim_pub.to_parquet(GOLD_DIR / "dim_publisher.parquet", index=False)
    game_pub.to_parquet(GOLD_DIR / "game_publisher.parquet", index=False)

    print(f"dim_developer:   {len(dim_dev)} rows")
    print(f"game_developer:  {len(game_dev)} rows (bridge)")
    print(f"dim_publisher:   {len(dim_pub)} rows")
    print(f"game_publisher:  {len(game_pub)} rows (bridge)")

    return dim_dev, game_dev, dim_pub, game_pub


if __name__ == "__main__":
    run()
