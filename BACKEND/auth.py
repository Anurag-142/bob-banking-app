"""
auth.py — Password security helpers.
The ONLY place in the application where plain-text passwords are handled.
Uses Werkzeug's PBKDF2-SHA256 implementation under the hood.
"""

from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain_text: str) -> str:
    """Accept a plain-text password and return a salted hash string.
    Called once during seeding — never called during a live login."""
    return generate_password_hash(plain_text)


def verify_password(plain_text: str, stored_hash: str) -> bool:
    """Return True if plain_text matches stored_hash, False otherwise.
    Uses a constant-time comparison to prevent timing attacks."""
    return check_password_hash(stored_hash, plain_text)
