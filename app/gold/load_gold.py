"""
Gold layer orchestrator.

Builds the full star schema from silver tables:
  dimensions : dim_game, dim_genre, dim_developer, dim_publisher,
               dim_category, dim_date
  bridges    : game_genre, game_developer, game_publisher, game_category
  facts      : fact_player_count, fact_reviews, fact_achievements

Fact tables hold real collected rows; their time depth grows as the
scheduled collection job accumulates timestamps.

The synthetic demo seeder (generate_demo_data.py) is intentionally NOT run
here — it's a manual, clearly-labeled tool for dashboard visuals only.

Run directly:
    python -m app.gold.load_gold
"""

import time

from app.gold import (
    build_dim_game,
    build_dim_developer_publisher,
    build_dim_category,
    build_dim_date,
    build_facts,
)


def _timed(label, func):
    print(f"\n{'=' * 60}")
    print(f"RUNNING: {label}")
    print("=" * 60)
    start = time.perf_counter()
    try:
        result = func()
    except FileNotFoundError as e:
        print(f"SKIPPED: {label} — {e}")
        result = None
    m, s = divmod(time.perf_counter() - start, 60)
    print(f"DONE: {label} — {int(m)}m {s:.1f}s")
    return result


def load_gold():
    total_start = time.perf_counter()

    _timed("Game + genre dimensions", build_dim_game.run)
    _timed("Developer + publisher dimensions", build_dim_developer_publisher.run)
    _timed("Category dimension", build_dim_category.run)
    _timed("Date dimension", build_dim_date.run)
    _timed("Fact tables", build_facts.run)

    m, s = divmod(time.perf_counter() - total_start, 60)
    print(f"\n{'=' * 60}")
    print(f"GOLD LAYER COMPLETE — total {int(m)}m {s:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    load_gold()
