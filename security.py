"""Hashing helpers used by the authentication and reporting layers."""

import hashlib
import hmac
import json
from typing import Any


PBKDF2_ITERATIONS = 600_000


def hash_voter_id(voter_id: str) -> str:
    """Return a stable SHA-256 digest for a normalized voter identifier."""
    normalized = voter_id.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def hash_password(password: str, salt: str) -> str:
    """Derive a password hash with a slow, salted PBKDF2-HMAC operation.

    Unlike a single SHA-256 call, PBKDF2 deliberately performs many iterations,
    making offline password guessing substantially more expensive.
    """
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    )
    return derived_key.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Compare password hashes in constant time."""
    actual_hash = hash_password(password, salt)
    return hmac.compare_digest(actual_hash, expected_hash)


def report_hash(payload: dict[str, Any]) -> str:
    """Create an integrity fingerprint; this does not encrypt report content."""
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
