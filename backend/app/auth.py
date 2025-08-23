"""Simple authentication helpers for AI Tutoring MVP.

Provides password hashing and verification using Python's built-in hashlib. This
avoids dependencies on external libraries such as passlib. Note that SHA-256
hashing without salting is not secure for production, but suffices for a proof
of concept.
"""

import hashlib


def get_password_hash(password: str) -> str:
    """Hash a plain-text password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored SHA-256 hash."""
    return get_password_hash(plain_password) == hashed_password