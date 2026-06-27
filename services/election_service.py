"""Voter logging and ballot-tracking application logic."""

import sqlite3
from typing import Any

from database.repository import ElectionRepository
from security import hash_voter_id
from voter_verification import validate_voter_id


class DuplicateVoteError(Exception):
    """Raised when an officer attempts to log a voter more than once."""


class ElectionService:
    def __init__(self, repository: ElectionRepository):
        self.repository = repository

    def log_voter(self, voter_id: str, officer_id: int) -> dict[str, Any]:
        validated_id = validate_voter_id(voter_id)
        try:
            return self.repository.record_vote_and_issue_ballot(
                hash_voter_id(validated_id), officer_id
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateVoteError(str(exc)) from exc

    def ballot_summary(self) -> dict[str, int]:
        return self.repository.get_ballot_counts()

    def list_ballots(self) -> list[dict[str, Any]]:
        return self.repository.list_ballots()

    def update_ballot_status(
        self, ballot_id: int, status: str, officer_id: int
    ) -> None:
        self.repository.update_ballot_status(ballot_id, status, officer_id)

    def recent_activity(self) -> list[dict[str, Any]]:
        return self.repository.recent_ballot_activity()

