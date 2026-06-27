"""Hashing helpers used by the authentication and reporting layers."""

import hashlib
import hmac
import json
from typing import Any


def hash_voter_id(voter_id: str) -> str:
    """Return a stable SHA-256 digest for a normalized voter identifier."""
    normalized = voter_id.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def hash_password(password: str, salt: str) -> str:
    """Hash a local officer password with its per-account salt."""
    value = f"{salt}:{password}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Compare password hashes in constant time."""
    actual_hash = hash_password(password, salt)
    return hmac.compare_digest(actual_hash, expected_hash)


def report_hash(payload: dict[str, Any]) -> str:
    """Hash canonical JSON so field ordering cannot change the digest."""
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

