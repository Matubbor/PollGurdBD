"""Create the local PollGuard BD database and insert training records."""

import argparse
import sys
from pathlib import Path

# Allow `python database/db_init.py` to import modules from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import DATABASE_PATH  # noqa: E402
from database.schema import initialize_database  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize PollGuard BD.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing local database before adding fresh training data.",
    )
    args = parser.parse_args()

    if args.reset and DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        print(f"Removed existing database: {DATABASE_PATH}")

    initialize_database(DATABASE_PATH)
    print(f"PollGuard BD database is ready: {DATABASE_PATH}")
    print("Officer login: admin / admin123")
    print("Registered voters: 1000000001 to 1000000005 (training environment)")


if __name__ == "__main__":
    main()
