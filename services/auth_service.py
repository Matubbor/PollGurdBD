"""Officer authentication use cases."""

from typing import Any

from database.repository import ElectionRepository


class AuthenticationService:
    def __init__(self, repository: ElectionRepository):
        self.repository = repository

    def login(self, username: str, password: str) -> dict[str, Any]:
        username = username.strip()
        if not username or not password:
            raise ValueError("Enter both username and password.")
        officer = self.repository.authenticate_officer(username, password)
        if officer is None:
            raise PermissionError("Incorrect username or password.")
        return officer

