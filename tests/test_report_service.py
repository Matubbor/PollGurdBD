"""Tests for tamper-evident and encrypted report generation."""

import json
import tempfile
import unittest
from pathlib import Path

from database.repository import ElectionRepository
from database.schema import connect_database, initialize_database
from security import report_hash
from services.encryption_service import ReportEncryptionService
from services.report_service import ReportService


class ReportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.database_path = self.root / "test_pollguard.db"
        initialize_database(self.database_path)
        self.repository = ElectionRepository(self.database_path)
        officer = self.repository.authenticate_officer("admin", "admin123")
        assert officer is not None
        self.officer_id = officer["id"]
        self.encryption_service = ReportEncryptionService(
            self.root / "report_encryption.key"
        )
        self.report_service = ReportService(
            self.repository,
            self.root / "generated_reports",
            self.encryption_service,
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_report_hash_is_generated_and_both_files_are_saved(self) -> None:
        """Readable JSON, encrypted output, hash, and audit row must agree."""
        artifacts = self.report_service.generate_report(self.officer_id)

        self.assertTrue(artifacts.readable_path.exists())
        self.assertEqual(artifacts.readable_path.suffix, ".json")
        self.assertTrue(artifacts.encrypted_path.exists())
        self.assertEqual(artifacts.encrypted_path.suffix, ".pgbd")

        readable_bytes = artifacts.readable_path.read_bytes()
        report = json.loads(readable_bytes)
        digest = report.pop("report_hash_sha256")
        self.assertEqual(digest, report_hash(report))

        encrypted_bytes = artifacts.encrypted_path.read_bytes()
        self.assertNotEqual(encrypted_bytes, readable_bytes)
        self.assertEqual(
            self.encryption_service.decrypt(encrypted_bytes), readable_bytes
        )

        connection = connect_database(self.database_path)
        try:
            audit_row = connection.execute(
                """
                SELECT filename, report_hash
                FROM reports
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        finally:
            connection.close()
        self.assertIsNotNone(audit_row)
        self.assertEqual(audit_row["filename"], artifacts.encrypted_path.name)
        self.assertEqual(audit_row["report_hash"], digest)


if __name__ == "__main__":
    unittest.main()

