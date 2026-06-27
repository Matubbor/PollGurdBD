"""Database schema creation and fictional demonstration data."""

from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path

from security import hash_password, hash_voter_id


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS officers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS voters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_id_hash TEXT NOT NULL UNIQUE,
    voter_reference TEXT NOT NULL,
    has_voted INTEGER NOT NULL DEFAULT 0 CHECK (has_voted IN (0, 1)),
    voted_at TEXT
);

CREATE TABLE IF NOT EXISTS ballots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ballot_code TEXT NOT NULL UNIQUE,
    voter_id_hash TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'Issued'
        CHECK (status IN ('Issued', 'Cast', 'Spoiled')),
    issued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    issued_by INTEGER NOT NULL,
    FOREIGN KEY (voter_id_hash) REFERENCES voters(voter_id_hash),
    FOREIGN KEY (issued_by) REFERENCES officers(id)
);

CREATE TABLE IF NOT EXISTS ballot_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ballot_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    officer_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ballot_id) REFERENCES ballots(id),
    FOREIGN KEY (officer_id) REFERENCES officers(id)
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    report_hash TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    generated_by INTEGER NOT NULL,
    FOREIGN KEY (generated_by) REFERENCES officers(id)
);

CREATE INDEX IF NOT EXISTS idx_ballots_status ON ballots(status);
CREATE INDEX IF NOT EXISTS idx_ballot_logs_created ON ballot_logs(created_at);
"""


DEMO_OFFICERS = (
    ("admin", "admin123", "Demo Presiding Officer"),
    ("officer1", "pollguard123", "Demo Polling Officer"),
)

# Clearly fictional identifiers reserved only for the local software demo.
DEMO_VOTER_IDS = tuple(str(1000000000 + number) for number in range(1, 16))


def connect_database(database_path: str | Path) -> sqlite3.Connection:
    """Open a configured SQLite connection."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    """Create all application tables and indexes."""
    connection.executescript(SCHEMA)
    connection.commit()


def seed_demo_data(connection: sqlite3.Connection) -> None:
    """Insert local demo accounts and fictional voters without overwriting data."""
    for username, password, full_name in DEMO_OFFICERS:
        existing = connection.execute(
            "SELECT id FROM officers WHERE username = ?", (username,)
        ).fetchone()
        if existing is None:
            salt = secrets.token_hex(16)
            connection.execute(
                """
                INSERT INTO officers (username, password_hash, salt, full_name)
                VALUES (?, ?, ?, ?)
                """,
                (username, hash_password(password, salt), salt, full_name),
            )

    for voter_id in DEMO_VOTER_IDS:
        voter_hash = hash_voter_id(voter_id)
        reference = f"DEMO-••••{voter_id[-4:]}"
        connection.execute(
            """
            INSERT OR IGNORE INTO voters (voter_id_hash, voter_reference)
            VALUES (?, ?)
            """,
            (voter_hash, reference),
        )
    connection.commit()


def initialize_database(database_path: str | Path) -> None:
    """Create the schema and insert demonstration records."""
    connection = connect_database(database_path)
    try:
        create_schema(connection)
        seed_demo_data(connection)
    finally:
        connection.close()
