"""Basic unit tests for the core polling-station rules."""

import tempfile
import unittest
from pathlib import Path

from database.repository import ElectionRepository
from database.schema import initialize_database
from services.election_service import DuplicateVoteError, ElectionService


class ElectionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "test_pollguard.db"
        initialize_database(self.database_path)
        self.repository = ElectionRepository(self.database_path)
        self.service = ElectionService(self.repository)
        officer = self.repository.authenticate_officer("admin", "admin123")
        assert officer is not None
        self.officer_id = officer["id"]

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_duplicate_voter_is_rejected(self) -> None:
        """A second attempt must not create another ballot."""
        self.service.log_voter("1000000001", self.officer_id)

        with self.assertRaises(DuplicateVoteError):
            self.service.log_voter("1000000001", self.officer_id)

        self.assertEqual(self.service.ballot_summary()["issued"], 1)

    def test_ballot_counts_are_calculated_by_status(self) -> None:
        """Issued, cast, spoiled, and pending counts must stay consistent."""
        first = self.service.log_voter("1000000002", self.officer_id)
        second = self.service.log_voter("1000000003", self.officer_id)
        self.service.log_voter("1000000004", self.officer_id)

        self.service.update_ballot_status(
            first["ballot_id"], "Cast", self.officer_id
        )
        self.service.update_ballot_status(
            second["ballot_id"], "Spoiled", self.officer_id
        )

        self.assertEqual(
            self.service.ballot_summary(),
            {"issued": 3, "cast": 1, "spoiled": 1, "pending": 1},
        )


if __name__ == "__main__":
    unittest.main()

