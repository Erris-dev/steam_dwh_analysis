"""
Silver layer orchestrator.

Runs all silver transforms in order, printing what ran and how long each
took. Each transform reads from bronze files and writes a clean Parquet
table to data/silver/. Called from main.py, or run directly:

    python -m app.transform.load_silver
"""

import time

from app.transform import (
    transform_games,
    transform_player_counts,
    transform_reviews,
    transform_achievements,
)


def _timed(label, func):
    """Run one transform, print its duration, and return its result."""
    print(f"\n{'=' * 60}")
    print(f"RUNNING: {label}")
    print("=" * 60)

    start = time.perf_counter()
    try:
        result = func()
    except FileNotFoundError as e:
        # A missing bronze source shouldn't kill the whole silver run —
        # report it and continue with the transforms that can run.
        print(f"SKIPPED: {label} — {e}")
        result = None

    elapsed = time.perf_counter() - start
    m, s = divmod(elapsed, 60)
    print(f"DONE: {label} — {int(m)}m {s:.1f}s")
    return result


def load_silver():
    """Build all silver tables from the latest bronze snapshots."""
    total_start = time.perf_counter()

    _timed("Games", transform_games.run)
    _timed("Player counts", transform_player_counts.run)
    _timed("Reviews", transform_reviews.run)
    _timed("Achievements", transform_achievements.run)

    total = time.perf_counter() - total_start
    m, s = divmod(total, 60)
    print(f"\n{'=' * 60}")
    print(f"SILVER LAYER COMPLETE — total {int(m)}m {s:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    load_silver()
