"""Local authenticated encryption for secure PollGuard report artifacts."""

from __future__ import annotations

import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class ReportEncryptionService:
    """Encrypt and decrypt report bytes with a persistent local Fernet key.

    SHA-256 report hashing and Fernet encryption solve different problems:
    hashing exposes later content changes (integrity), while encryption hides
    the report contents from anyone who does not possess this key
    (confidentiality). Fernet also authenticates its encrypted token.
    """

    def __init__(self, key_path: str | Path):
        self.key_path = Path(key_path)

    def _load_or_create_key(self) -> bytes:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.key_path.exists():
            key = Fernet.generate_key()
            try:
                # Exclusive creation avoids silently replacing a key if two
                # local processes generate the first report simultaneously.
                with self.key_path.open("xb") as key_file:
                    key_file.write(key)
                try:
                    os.chmod(self.key_path, 0o600)
                except OSError:
                    # Some platforms do not expose POSIX file permissions.
                    pass
            except FileExistsError:
                pass
        return self.key_path.read_bytes().strip()

    def encrypt(self, plaintext: bytes) -> bytes:
        """Return a Fernet-encrypted token containing the report bytes."""
        return Fernet(self._load_or_create_key()).encrypt(plaintext)

    def decrypt(self, encrypted_report: bytes) -> bytes:
        """Decrypt a local report, raising InvalidToken for the wrong key/data."""
        return Fernet(self._load_or_create_key()).decrypt(encrypted_report)


__all__ = ["InvalidToken", "ReportEncryptionService"]

