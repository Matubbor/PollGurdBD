"""Validation rules for voter identifiers entered by polling officers."""


MIN_VOTER_ID_LENGTH = 10
MAX_VOTER_ID_LENGTH = 17


def normalize_voter_id(value: str) -> str:
    """Remove surrounding whitespace without altering the identifier."""
    return value.strip()


def validate_voter_id(value: str) -> str:
    """Validate and return a normalized demo voter ID.

    PollGuard BD accepts numeric identifiers between 10 and 17 digits. The
    range is intentionally broad because this coursework app is not connected
    to any real national identity system.
    """
    normalized = normalize_voter_id(value)
    if not normalized:
        raise ValueError("Enter a voter ID.")
    if not normalized.isdigit():
        raise ValueError("Voter ID must contain digits only.")
    if not MIN_VOTER_ID_LENGTH <= len(normalized) <= MAX_VOTER_ID_LENGTH:
        raise ValueError(
            f"Voter ID must be {MIN_VOTER_ID_LENGTH} to "
            f"{MAX_VOTER_ID_LENGTH} digits long."
        )
    return normalized

