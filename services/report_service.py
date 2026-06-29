"""Tamper-evident local report generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from database.repository import ElectionRepository
from security import report_hash
from services.encryption_service import ReportEncryptionService


@dataclass(frozen=True)
class ReportArtifacts:
    """Paths and report data produced by one generation operation."""

    readable_path: Path
    encrypted_path: Path
    report: dict[str, Any]


class ReportService:
    def __init__(
        self,
        repository: ElectionRepository,
        reports_directory: str | Path,
        encryption_service: ReportEncryptionService,
    ):
        self.repository = repository
        self.reports_directory = Path(reports_directory)
        self.encryption_service = encryption_service

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

    def generate_report(self, officer_id: int) -> ReportArtifacts:
        """Write readable and encrypted copies of a tamper-evident report.

        The embedded SHA-256 digest provides an integrity check. It does not
        conceal data. Fernet separately encrypts the same JSON bytes to provide
        confidentiality for the secure `.pgbd` output.
        """
        summary = self.build_summary()
        digest = report_hash(summary)
        report = {**summary, "report_hash_sha256": digest}

        self.reports_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        stem = f"pollguard_report_{timestamp}"
        readable_path = self.reports_directory / f"{stem}.json"
        encrypted_path = self.reports_directory / f"{stem}.pgbd"
        readable_bytes = (
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        try:
            readable_path.write_bytes(readable_bytes)
            encrypted_path.write_bytes(
                self.encryption_service.encrypt(readable_bytes)
            )
            self.repository.save_report_record(
                encrypted_path.name,
                summary["generated_at"],
                digest,
                report,
                officer_id,
            )
        except Exception:
            # Avoid partial artifacts if encryption or the audit insert fails.
            for path in (readable_path, encrypted_path):
                if path.exists():
                    path.unlink()
            raise
        return ReportArtifacts(readable_path, encrypted_path, report)
