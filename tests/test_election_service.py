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

    def test_invalid_voter_id_format_is_rejected(self) -> None:
        """Non-numeric and incorrectly sized identifiers must fail validation."""
        invalid_values = ("", "ABC1234567", "12345", "123456789012345678")

        for voter_id in invalid_values:
            with self.subTest(voter_id=voter_id):
                with self.assertRaises(ValueError):
                    self.service.log_voter(voter_id, self.officer_id)

        self.assertEqual(self.service.ballot_summary()["issued"], 0)

    def test_unknown_voter_id_is_rejected(self) -> None:
        """A validly formatted ID absent from the local register cannot vote."""
        with self.assertRaises(LookupError):
            self.service.log_voter("9999999999", self.officer_id)

        self.assertEqual(self.service.ballot_summary()["issued"], 0)

    def test_final_ballot_status_cannot_be_updated_again(self) -> None:
        """Cast and spoiled ballots are terminal and cannot transition again."""
        for voter_id, final_status, attempted_status in (
            ("1000000005", "Cast", "Spoiled"),
            ("1000000004", "Spoiled", "Cast"),
        ):
            with self.subTest(final_status=final_status):
                ballot = self.service.log_voter(voter_id, self.officer_id)
                self.service.update_ballot_status(
                    ballot["ballot_id"], final_status, self.officer_id
                )

                with self.assertRaises(ValueError):
                    self.service.update_ballot_status(
                        ballot["ballot_id"], attempted_status, self.officer_id
                    )

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
