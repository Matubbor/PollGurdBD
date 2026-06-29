"""SQLite repository containing all persistent election operations."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from database.schema import connect_database
from security import verify_password


class ElectionRepository:
    """Provide transaction-safe access to PollGuard BD records."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        return connect_database(self.database_path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Always close read and short-write connections after use."""
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def authenticate_officer(
        self, username: str, password: str
    ) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT id, username, password_hash, salt, full_name
                FROM officers
                WHERE username = ?
                """,
                (username,),
            ).fetchone()
        if row is None or not verify_password(
            password, row["salt"], row["password_hash"]
        ):
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "full_name": row["full_name"],
        }

    def record_vote_and_issue_ballot(
        self, voter_id_hash: str, officer_id: int
    ) -> dict[str, Any]:
        """Atomically mark a voter and create exactly one linked ballot."""
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            voter = connection.execute(
                """
                SELECT id, voter_reference, has_voted
                FROM voters
                WHERE voter_id_hash = ?
                """,
                (voter_id_hash,),
            ).fetchone()
            if voter is None:
                raise LookupError("Voter ID was not found in the local register.")
            if voter["has_voted"]:
                raise sqlite3.IntegrityError(
                    "This voter has already been recorded as voted."
                )

            ballot_code = f"PGBD-{uuid.uuid4().hex[:10].upper()}"
            connection.execute(
                """
                UPDATE voters
                SET has_voted = 1, voted_at = CURRENT_TIMESTAMP
                WHERE id = ? AND has_voted = 0
                """,
                (voter["id"],),
            )
            cursor = connection.execute(
                """
                INSERT INTO ballots
                    (ballot_code, voter_id_hash, status, issued_by)
                VALUES (?, ?, 'Issued', ?)
                """,
                (ballot_code, voter_id_hash, officer_id),
            )
            connection.execute(
                """
                INSERT INTO ballot_logs
                    (ballot_id, action, old_status, new_status, officer_id)
                VALUES (?, 'Ballot issued', NULL, 'Issued', ?)
                """,
                (cursor.lastrowid, officer_id),
            )
            connection.commit()
            return {
                "ballot_id": cursor.lastrowid,
                "ballot_code": ballot_code,
                "voter_reference": voter["voter_reference"],
                "status": "Issued",
            }
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_ballot_counts(self) -> dict[str, int]:
        """Calculate all ballot totals in one database query."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS issued,
                    SUM(CASE WHEN status = 'Cast' THEN 1 ELSE 0 END) AS cast,
                    SUM(CASE WHEN status = 'Spoiled' THEN 1 ELSE 0 END) AS spoiled,
                    SUM(CASE WHEN status = 'Issued' THEN 1 ELSE 0 END) AS pending
                FROM ballots
                """
            ).fetchone()
        return {
            "issued": int(row["issued"] or 0),
            "cast": int(row["cast"] or 0),
            "spoiled": int(row["spoiled"] or 0),
            "pending": int(row["pending"] or 0),
        }

    def get_registered_voter_count(self) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM voters"
            ).fetchone()
        return int(row["total"])

    def list_ballots(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, ballot_code, status, issued_at, updated_at
                FROM ballots
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_ballot_status(
        self, ballot_id: int, new_status: str, officer_id: int
    ) -> None:
        if new_status not in {"Cast", "Spoiled"}:
            raise ValueError("Ballot status must be Cast or Spoiled.")

        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            ballot = connection.execute(
                "SELECT status FROM ballots WHERE id = ?", (ballot_id,)
            ).fetchone()
            if ballot is None:
                raise LookupError("The selected ballot no longer exists.")
            if ballot["status"] != "Issued":
                raise ValueError(
                    f"This ballot is already marked {ballot['status']}."
                )
            connection.execute(
                """
                UPDATE ballots
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_status, ballot_id),
            )
            connection.execute(
                """
                INSERT INTO ballot_logs
                    (ballot_id, action, old_status, new_status, officer_id)
                VALUES (?, 'Status updated', ?, ?, ?)
                """,
                (ballot_id, ballot["status"], new_status, officer_id),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def recent_ballot_activity(self, limit: int = 12) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    l.id,
                    b.ballot_code,
                    l.action,
                    l.old_status,
                    l.new_status,
                    o.username,
                    l.created_at
                FROM ballot_logs AS l
                JOIN ballots AS b ON b.id = l.ballot_id
                JOIN officers AS o ON o.id = l.officer_id
                ORDER BY l.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_audit_activity(self, limit: int = 200) -> list[dict[str, Any]]:
        """Return ballot and report events as one read-only activity feed."""
        safe_limit = max(1, min(int(limit), 500))
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    event_time,
                    event_type,
                    reference,
                    username,
                    details
                FROM (
                    SELECT
                        l.created_at AS event_time,
                        CASE
                            WHEN l.old_status IS NULL THEN 'Ballot issued'
                            ELSE 'Ballot status updated'
                        END AS event_type,
                        b.ballot_code AS reference,
                        o.username AS username,
                        CASE
                            WHEN l.old_status IS NULL
                                THEN 'Status: ' || l.new_status
                            ELSE l.old_status || ' → ' || l.new_status
                        END AS details,
                        l.id AS event_id,
                        1 AS source_order
                    FROM ballot_logs AS l
                    JOIN ballots AS b ON b.id = l.ballot_id
                    LEFT JOIN officers AS o ON o.id = l.officer_id

                    UNION ALL

                    SELECT
                        r.generated_at AS event_time,
                        'Report generated' AS event_type,
                        r.filename AS reference,
                        o.username AS username,
                        'Encrypted .pgbd • SHA-256 '
                            || SUBSTR(r.report_hash, 1, 12) || '…' AS details,
                        r.id AS event_id,
                        2 AS source_order
                    FROM reports AS r
                    LEFT JOIN officers AS o ON o.id = r.generated_by
                )
                ORDER BY event_time DESC, source_order DESC, event_id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_report_record(
        self,
        filename: str,
        generated_at: str,
        digest: str,
        summary: dict[str, Any],
        officer_id: int,
    ) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO reports
                    (filename, generated_at, report_hash, summary_json, generated_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    generated_at,
                    digest,
                    json.dumps(summary, sort_keys=True),
                    officer_id,
                ),
            )
            connection.commit()
