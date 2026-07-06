"""
JWT creation, decoding, and validation services.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app.core.config import settings


def create_access_token(user_id: UUID, role: str) -> tuple[str, datetime]:
    """
    Generates a secure access token.

    Args:
        user_id: The UUID of the user.
        role: The role classification of the user.

    Returns:
        A tuple containing the signed token string and the expiration datetime.
    """
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = datetime.now(UTC) + expires_delta

    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": int(expires_at.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
        "jti": str(uuid4()),
    }
    token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return token, expires_at


def create_refresh_token(user_id: UUID) -> tuple[str, datetime]:
    """
    Generates a secure refresh token.

    Args:
        user_id: The UUID of the user.

    Returns:
        A tuple containing the signed token string and the expiration datetime.
    """
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expires_at = datetime.now(UTC) + expires_delta

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": int(expires_at.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
        "jti": str(uuid4()),
    }
    token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return token, expires_at


def decode_token(token: str) -> dict | None:
    """
    Decodes a JWT and verifies signatures, expiration, and key claims.

    Args:
        token: The signed token string.

    Returns:
        The decoded payload dictionary if valid, otherwise None.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
        return payload
    except jwt.PyJWTError:
        return None
