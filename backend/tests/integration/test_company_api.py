"""
Integration tests for Company API endpoints.
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


def test_company_endpoints_flow(test_db: None) -> None:
    """
    Validates company CRUD, duplicate logic, paginated searches/filters, and workspace isolation.
    """
    client = TestClient(app)

    # 1. Register User 1
    u1_res = client.post(
        "/auth/register",
        json={
            "email": "user1@equityiq.com",
            "password": "Password123!",
            "role": "analyst",
        },
    )
    assert u1_res.status_code == 201
    u1_auth = u1_res.json()
    headers1 = {"Authorization": f"Bearer {u1_auth['access_token']}"}

    # Retrieve User 1's default personal workspace ID
    ws1_list = client.get("/workspaces", headers=headers1)
    ws1_id = ws1_list.json()[0]["id"]
    headers1["X-Workspace-ID"] = ws1_id

    # 2. Create Company A (US, NASDAQ, Technology, Software)
    comp_a_res = client.post(
        "/companies",
        json={
            "ticker": "AAPL",
            "exchange": "NASDAQ",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "US",
            "fiscal_year_end": "09-30",
            "currency": "USD",
        },
        headers=headers1,
    )
    assert comp_a_res.status_code == 201
    comp_a = comp_a_res.json()
    assert comp_a["ticker"] == "AAPL"
    comp_a_id = comp_a["id"]

    # 3. Verify Duplicate Prevention (Creating AAPL in NASDAQ in same workspace fails with 409)
    comp_dup_res = client.post(
        "/companies",
        json={
            "ticker": "AAPL",
            "exchange": "NASDAQ",
            "name": "Apple Duplicate",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "US",
            "fiscal_year_end": "09-30",
            "currency": "USD",
        },
        headers=headers1,
    )
    assert comp_dup_res.status_code == 409

    # 4. Create Company B (IN, NSE, Technology, IT Services) and Company C (US, NYSE, Financials, Banking)
    comp_b_res = client.post(
        "/companies",
        json={
            "ticker": "INFY",
            "exchange": "NSE",
            "name": "Infosys Ltd.",
            "sector": "Technology",
            "industry": "IT Services",
            "country": "IN",
            "fiscal_year_end": "03-31",
            "currency": "INR",
        },
        headers=headers1,
    )
    assert comp_b_res.status_code == 201
    assert comp_b_res.json()["ticker"] == "INFY"

    comp_c_res = client.post(
        "/companies",
        json={
            "ticker": "JPM",
            "exchange": "NYSE",
            "name": "JPMorgan Chase",
            "sector": "Financials",
            "industry": "Banking",
            "country": "US",
            "fiscal_year_end": "12-31",
            "currency": "USD",
        },
        headers=headers1,
    )
    assert comp_c_res.status_code == 201
    assert comp_c_res.json()["ticker"] == "JPM"

    # Default list
    list_res = client.get("/companies", headers=headers1)
    assert list_res.status_code == 200
    comp_list = list_res.json()
    assert len(comp_list) == 3

    # Sorting by ticker ASC -> [AAPL, INFY, JPM]
    sort_res = client.get("/companies?sort_by=ticker&sort_order=asc", headers=headers1)
    sort_list = sort_res.json()
    assert sort_list[0]["ticker"] == "AAPL"
    assert sort_list[1]["ticker"] == "INFY"
    assert sort_list[2]["ticker"] == "JPM"

    # Filtering by country=US -> [JPM, AAPL]
    filter_res = client.get("/companies?country=US", headers=headers1)
    filter_list = filter_res.json()
    assert len(filter_list) == 2
    tickers = {c["ticker"] for c in filter_list}
    assert tickers == {"AAPL", "JPM"}

    # Filtering by exchange=NSE -> [INFY]
    filter_nse = client.get("/companies?exchange=NSE", headers=headers1).json()
    assert len(filter_nse) == 1
    assert filter_nse[0]["ticker"] == "INFY"

    # Filtering by sector=Financials -> [JPM]
    filter_fin = client.get("/companies?sector=Financials", headers=headers1).json()
    assert len(filter_fin) == 1
    assert filter_fin[0]["ticker"] == "JPM"

    # 6. Verify Text Search (queries company name, ticker, exchange, and sector)
    # Search sector "Tech" -> AAPL, INFY
    search_res = client.get("/companies/search?query=Tech", headers=headers1)
    assert search_res.status_code == 200
    search_list = search_res.json()
    assert len(search_list) == 2
    search_tickers = {c["ticker"] for c in search_list}
    assert search_tickers == {"AAPL", "INFY"}

    # Search ticker "JP" -> JPM
    search_jp = client.get("/companies/search?query=JP", headers=headers1).json()
    assert len(search_jp) == 1
    assert search_jp[0]["ticker"] == "JPM"

    # 7. Verify Patch Update
    patch_res = client.patch(
        f"/companies/{comp_a_id}",
        json={"name": "Apple Inc. Updated"},
        headers=headers1,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Apple Inc. Updated"

    # 8. Verify Soft-Delete and Restoration Duplicate Validation
    # Soft delete AAPL
    del_res = client.delete(f"/companies/{comp_a_id}", headers=headers1)
    assert del_res.status_code == 200

    # Retrieve AAPL (should be 404 since it's soft-deleted)
    get_fail_res = client.get(f"/companies/{comp_a_id}", headers=headers1)
    assert get_fail_res.status_code == 404

    # Create AAPL again in NASDAQ (should restore and update the existing soft-deleted record)
    restore_res = client.post(
        "/companies",
        json={
            "ticker": "AAPL",
            "exchange": "NASDAQ",
            "name": "Apple Inc. Restored",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "US",
            "fiscal_year_end": "09-30",
            "currency": "USD",
        },
        headers=headers1,
    )
    assert restore_res.status_code == 201
    restored_comp = restore_res.json()
    assert restored_comp["id"] == comp_a_id  # Restores the SAME record ID!
    assert restored_comp["name"] == "Apple Inc. Restored"

    # 9. Verify Cross-Workspace Isolation (User 2 should not access User 1's companies)
    # Register User 2
    u2_res = client.post(
        "/auth/register",
        json={
            "email": "user2@equityiq.com",
            "password": "Password123!",
            "role": "analyst",
        },
    )
    assert u2_res.status_code == 201
    u2_auth = u2_res.json()
    headers2 = {"Authorization": f"Bearer {u2_auth['access_token']}"}

    # Retrieve User 2's personal workspace ID
    ws2_list = client.get("/workspaces", headers=headers2)
    ws2_id = ws2_list.json()[0]["id"]
    headers2["X-Workspace-ID"] = ws2_id

    # User 2 tries to access User 1's company by ID directly in Workspace 2 (404/NotFound because it is isolated)
    get_iso_res = client.get(f"/companies/{comp_a_id}", headers=headers2)
    assert get_iso_res.status_code == 404

    # User 2 tries to bypass isolation by explicitly setting headers to Workspace 1's ID (403/Forbidden due to lack of membership)
    headers2["X-Workspace-ID"] = ws1_id
    get_bypass_res = client.get(f"/companies/{comp_a_id}", headers=headers2)
    assert get_bypass_res.status_code == 403
    assert "does not have access to this workspace" in get_bypass_res.json()["detail"]
