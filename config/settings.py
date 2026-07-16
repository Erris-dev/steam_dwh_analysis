import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MASTER_LIST_DIR = DATA_DIR / "master_app_list"
APP_DETAILS_DIR = DATA_DIR / "game_storefront_details"
PLAYER_COUNTS_DIR = DATA_DIR / "player_counts"
REVIEWS_DIR = DATA_DIR / "reviews"
ACHIEVEMENTS_DIR = DATA_DIR / "achievement_percentages"
STEAMSPY_DIR = DATA_DIR / "steamspy"

SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"


REQUEST_TIMEOUT = 10
SLEEP_BETWEEN_CALLS = 1.5
TARGET_APP_COUNT = 600