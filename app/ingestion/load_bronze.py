"""
Bronze layer orchestrator.

Runs all ingestion scripts in order, printing what ran and how long
each step took. Called from main.py, or run directly:

    python -m app.ingestion.load_bronze
"""

import time

from app.ingestion import (
    fetch_master_list,
    fetch_app_details,
    fetch_player_counts,
    fetch_reviews,
    fetch_achievements,
    fetch_steamspy,
    fetch_featured_categories,
)


def _timed(label, func, *args):
    """Run one step, print its duration, and return its result."""
    print(f"\n{'=' * 60}")
    print(f"RUNNING: {label}")
    print("=" * 60)

    start = time.perf_counter()
    result = func(*args)
    elapsed = time.perf_counter() - start

    minutes, seconds = divmod(elapsed, 60)
    print(f"DONE: {label} — {int(minutes)}m {seconds:.1f}s")
    return result


def load_bronze():
    """Full bronze ingestion run, in dependency order."""
    total_start = time.perf_counter()

    # Master list first — everything else depends on target_apps from it
    target_apps = _timed("Master app list", fetch_master_list.run)

    _timed("Storefront details (appdetails)", fetch_app_details.run, target_apps)
    _timed("Player counts", fetch_player_counts.run, target_apps)
    _timed("Reviews", fetch_reviews.run, target_apps)
    _timed("Achievement percentages", fetch_achievements.run, target_apps)
    _timed("SteamSpy estimates", fetch_steamspy.run, target_apps)
    _timed("Featured categories", fetch_featured_categories.run)

    total = time.perf_counter() - total_start
    minutes, seconds = divmod(total, 60)
    print(f"\n{'=' * 60}")
    print(f"BRONZE LAYER COMPLETE — total {int(minutes)}m {seconds:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    load_bronze()
