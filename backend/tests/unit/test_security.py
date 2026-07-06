"""
Unit tests for password hashing and token operations.
"""

from datetime import UTC
from uuid import uuid4

import jwt

from app.infrastructure.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.infrastructure.security.password import BcryptPasswordHasher


def test_password_hasher() -> None:
    """
    Verifies BcryptPasswordHasher hashing and correct/incorrect verification.
    """
    hasher = BcryptPasswordHasher()
    password = "SuperSecurePassword123!"

    hashed = hasher.hash_password(password)
    assert hashed != password
    assert len(hashed) > 20

    # Test correct verification
    assert hasher.verify_password(password, hashed) is True

    # Test incorrect verification
    assert hasher.verify_password("WrongPassword!", hashed) is False
    assert hasher.verify_password(password, "invalidhash") is False


def test_jwt_access_token() -> None:
    """
    Verifies JWT access token generation and field mapping.
    """
    user_id = uuid4()
    role = "analyst"

    from datetime import datetime

    token, expires_at = create_access_token(user_id, role)
    assert token is not None
    assert expires_at > datetime.now(UTC)

    # Decode and inspect
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload


def test_jwt_refresh_token() -> None:
    """
    Verifies JWT refresh token generation and field mapping.
    """
    user_id = uuid4()

    token, _ = create_refresh_token(user_id)
    assert token is not None

    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert "role" not in payload


def test_invalid_jwt_handling() -> None:
    """
    Verifies that invalid or tampered tokens return None when decoded.
    """
    assert decode_token("invalid.jwt.token") is None

    # Sign with a different secret
    payload = {"sub": "123", "type": "access", "exp": 9999999999}
    fake_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
    assert decode_token(fake_token) is None


# Quick utility helper
def datetime_now_utc() -> float:
    from datetime import datetime

    return datetime.now(UTC).timestamp()
