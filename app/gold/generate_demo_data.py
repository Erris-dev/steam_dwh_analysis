"""
=============================================================================
  SYNTHETIC DEMO DATA  —  NOT REAL COLLECTION
=============================================================================

Generates fake historical player-count and review time-series so dashboards
have something to render BEFORE the scheduled collection has accumulated real
history. This exists purely for visual/demo purposes.

IMPORTANT — how to talk about this honestly:
  * This data is INVENTED. It is NOT collected from Steam.
  * Output goes to data/gold_demo/ (a SEPARATE folder) so it never mixes
    with real fact tables in data/gold/.
  * Every row carries is_synthetic=True.
  * In an interview/portfolio, introduce it as: "seeded sample data so the
    dashboard renders before real collection fills in" — never as real data.

Real facts live in data/gold/ (build_facts.py). This script does not touch them.

Run directly:
    python -m app.gold.generate_demo_data
"""

import numpy as np
import pandas as pd

from config.settings import GOLD_DIR, DATA_DIR

DEMO_DIR = DATA_DIR / "gold_demo"
N_DAYS = 30          # how many days of fake history to synthesize
SEED = 42


def _banner():
    print("=" * 70)
    print("  GENERATING SYNTHETIC DEMO DATA — NOT REAL COLLECTION")
    print("  Output -> data/gold_demo/  (separate from real data/gold/)")
    print("=" * 70)


def run():
    _banner()
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    # Seed from the real games so appids are valid, but invent the time-series
    games = pd.read_parquet(GOLD_DIR / "dim_game.parquet")
    sample = games.sample(min(50, len(games)), random_state=SEED)

    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=N_DAYS)

    pc_rows = []
    for appid in sample["appid"]:
        base = rng.integers(50, 50000)          # each game's baseline popularity
        trend = rng.normal(0, 0.02)             # gentle up/down drift
        for i, d in enumerate(dates):
            # baseline * drift * daily noise, floored at 0
            noise = rng.normal(1.0, 0.15)
            value = max(0, int(base * (1 + trend) ** i * noise))
            pc_rows.append({
                "appid": appid,
                "date_id": int(d.strftime("%Y%m%d")),
                "date": d,
                "player_count": value,
                "is_synthetic": True,
            })

    pc = pd.DataFrame(pc_rows)
    pc.to_parquet(DEMO_DIR / "fact_player_count_demo.parquet", index=False)
    print(f"fact_player_count_demo: {len(pc)} synthetic rows "
          f"({pc['appid'].nunique()} games x {N_DAYS} days)")

    print("\nReminder: this is DEMO data. Real facts are in data/gold/.")
    return pc


if __name__ == "__main__":
    run()
