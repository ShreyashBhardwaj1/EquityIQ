"""
Security interfaces for password hashing.
"""

from typing import Protocol


class PasswordHasher(Protocol):
    """
    Protocol defining contract for password hashing and verification.
    """

    def hash_password(self, password: str) -> str:
        """
        Hashes a raw plain-text password.

        Args:
            password: The raw password string.

        Returns:
            The salted, cryptographic hash string.
        """
        ...

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifies a raw password against its hash.

        Args:
            password: The raw password to verify.
            hashed: The stored hash to verify against.

        Returns:
            True if the password matches the hash, otherwise False.
        """
        ...
