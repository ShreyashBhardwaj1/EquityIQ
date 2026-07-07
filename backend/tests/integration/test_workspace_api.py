"""
Integration tests for Workspace API endpoints.
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


def test_workspace_endpoints_flow(test_db: None) -> None:
    """
    Validates workspace CRUD, role auth permissions, and deletion safety rules.
    """
    client = TestClient(app)

    # 1. Register User (creates personal workspace automatically)
    reg_res = client.post(
        "/auth/register",
        json={
            "email": "owner@equityiq.com",
            "password": "Password123!",
            "role": "admin",
        },
    )
    assert reg_res.status_code == 201
    auth_data = reg_res.json()
    headers = {"Authorization": f"Bearer {auth_data['access_token']}"}

    # 2. List Workspaces (asserting personal workspace exists)
    list_res = client.get("/workspaces", headers=headers)
    assert list_res.status_code == 200
    workspaces = list_res.json()
    assert len(workspaces) == 1
    personal_ws = workspaces[0]
    assert personal_ws["name"] == "Owner's Workspace"
    personal_ws_id = personal_ws["id"]

    # 3. Create a second Workspace
    create_res = client.post(
        "/workspaces", json={"name": "Research Group"}, headers=headers
    )
    assert create_res.status_code == 201
    new_ws = create_res.json()
    assert new_ws["name"] == "Research Group"
    new_ws_id = new_ws["id"]

    # 4. List Workspaces again (now showing both workspaces)
    list_res = client.get("/workspaces", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 2

    # 5. Switch Active Workspace context verification
    switch_res = client.post(f"/workspaces/{new_ws_id}/switch", headers=headers)
    assert switch_res.status_code == 200
    assert (
        switch_res.json()["detail"] == "Workspace active context switched successfully."
    )
    assert switch_res.json()["workspace_id"] == new_ws_id

    # 6. Patch Workspace (partial updates)
    patch_res = client.patch(
        f"/workspaces/{new_ws_id}",
        json={"name": "Research Group Modified"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Research Group Modified"

    # 7. Delete Workspace Safety Checks
    # Delete the new workspace
    delete_res = client.delete(f"/workspaces/{new_ws_id}", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["detail"] == "Workspace archived successfully."

    # Try to retrieve it (should be soft-deleted, hence inactive)
    get_res = client.get(f"/workspaces/{new_ws_id}", headers=headers)
    assert get_res.status_code == 404  # Workspace is soft-deleted, not active

    # Try to delete the personal workspace (rejected because it is the last remaining active workspace)
    delete_fail_res = client.delete(f"/workspaces/{personal_ws_id}", headers=headers)
    assert delete_fail_res.status_code == 400
    assert (
        "never delete their last remaining workspace"
        in delete_fail_res.json()["detail"]
    )
