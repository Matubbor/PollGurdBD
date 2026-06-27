"""Tamper-evident local report generation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from database.repository import ElectionRepository
from security import report_hash


class ReportService:
    def __init__(
        self, repository: ElectionRepository, reports_directory: str | Path
    ):
        self.repository = repository
        self.reports_directory = Path(reports_directory)

    def build_summary(self) -> dict[str, Any]:
        counts = self.repository.get_ballot_counts()
        registered = self.repository.get_registered_voter_count()
        turnout = (counts["issued"] / registered * 100) if registered else 0.0
        return {
            "application": "PollGuard BD",
            "data_notice": "Fictional local demonstration data only",
            "total_registered_voters": registered,
            "issued_ballots": counts["issued"],
            "cast_ballots": counts["cast"],
            "spoiled_ballots": counts["spoiled"],
            "pending_ballots": counts["pending"],
            "turnout_percentage": round(turnout, 2),
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }

    def generate_report(self, officer_id: int) -> tuple[Path, dict[str, Any]]:
        """Write canonical report data and its SHA-256 digest to disk."""
        summary = self.build_summary()
        digest = report_hash(summary)
        report = {**summary, "report_hash_sha256": digest}

        self.reports_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.reports_directory / f"pollguard_report_{timestamp}.json"
        try:
            path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            self.repository.save_report_record(
                path.name,
                summary["generated_at"],
                digest,
                report,
                officer_id,
            )
        except Exception:
            # Avoid leaving an untracked report file if its database audit record fails.
            if path.exists():
                path.unlink()
            raise
        return path, report
