"""
Integration tests for Authentication API endpoints.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.session import get_db_session
from app.main import app


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[None, None]:
    """
    Sets up an in-memory SQLite database, overrides dependency, and cleans up.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    yield

    app.dependency_overrides.clear()
    await engine.dispose()


def test_auth_endpoints_flow(test_db: None) -> None:
    """
    Validates register, authenticated /me, refresh token rotation, and logout operations.
    """
    client = TestClient(app)

    # 1. Register User (admin)
    reg_res = client.post(
        "/auth/register",
        json={
            "email": "user@equityiq.com",
            "password": "Password123!",
            "role": "admin",
        },
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["user"]["email"] == "user@equityiq.com"
    assert reg_data["user"]["role"] == "admin"

    access = reg_data["access_token"]
    refresh = reg_data["refresh_token"]

    # 2. Get Me (Success)
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "user@equityiq.com"

    # 3. Access with Invalid Token (Failure)
    bad_me_res = client.get("/auth/me", headers={"Authorization": "Bearer badtoken"})
    assert bad_me_res.status_code == 401

    # 4. Refresh Token Rotation (Success)
    ref_res = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert "access_token" in ref_data
    assert "refresh_token" in ref_data

    assert isinstance(ref_data["access_token"], str)
    new_refresh = ref_data["refresh_token"]
    assert new_refresh != refresh  # Ensure rotation took place

    # 5. Reuse Revoked Refresh Token (Failure)
    stale_ref_res = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert stale_ref_res.status_code == 401

    # 6. Logout (Success)
    logout_res = client.post("/auth/logout", json={"refresh_token": new_refresh})
    assert logout_res.status_code == 200

    # 7. Refresh with Logged-Out Token (Failure)
    post_logout_res = client.post("/auth/refresh", json={"refresh_token": new_refresh})
    assert post_logout_res.status_code == 401
