"""
Bcrypt implementation of PasswordHasher interface.
"""

import bcrypt

from app.domain.interfaces.security import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """
    Concrete implementation of PasswordHasher utilizing bcrypt hashing algorithms.
    """

    def hash_password(self, password: str) -> str:
        """
        Hashes a plain-text password using bcrypt.
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifies a raw password string against its stored bcrypt hash.
        """
        try:
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
