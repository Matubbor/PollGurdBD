"""Application-wide paths and display settings."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "pollguard.db"
REPORTS_DIR = BASE_DIR / "reports" / "generated_reports"

APP_NAME = "PollGuard BD"
APP_SUBTITLE = "Offline Polling Station Assistant"

