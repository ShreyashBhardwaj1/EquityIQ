"""
Integration tests for Document Metadata and Financial Statement CRUD, normalization, validations, and version history.
"""

from collections.abc import AsyncGenerator
from io import BytesIO

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


def test_financial_data_foundation_flow(test_db: None) -> None:
    """
    Comprehensive workflow integration testing:
    - Register User 1 & User 2
    - User 1 upload document metadata context
    - User 1 create balanced and imbalanced financial statements
    - User 1 update statement (generating history version audit logs)
    - User 1 compare as-reported vs normalized fields
    - User 1 update document file (generating document versions)
    - User 2 workspace isolation checks (blocking access to User 1's resources)
    """
    client = TestClient(app)

    # 1. Register User 1 & retrieve default workspace headers
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

    ws1_list = client.get("/workspaces", headers=headers1)
    ws1_id = ws1_list.json()[0]["id"]
    headers1["X-Workspace-ID"] = ws1_id

    # Register User 2 & retrieve default workspace headers
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

    ws2_list = client.get("/workspaces", headers=headers2)
    ws2_id = ws2_list.json()[0]["id"]
    headers2["X-Workspace-ID"] = ws2_id

    # 2. Create Company A under User 1
    comp_res = client.post(
        "/companies",
        json={
            "ticker": "AAPL",
            "exchange": "NASDAQ",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Software",
            "country": "US",
            "fiscal_year_end": "09-30",
            "currency": "USD",
        },
        headers=headers1,
    )
    assert comp_res.status_code == 201
    comp_a = comp_res.json()
    comp_a_id = comp_a["id"]

    # Create Company B under User 2
    comp_res2 = client.post(
        "/companies",
        json={
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "name": "Microsoft Corp.",
            "sector": "Technology",
            "industry": "Software",
            "country": "US",
            "fiscal_year_end": "06-30",
            "currency": "USD",
        },
        headers=headers2,
    )
    assert comp_res2.status_code == 201
    comp_b_id = comp_res2.json()["id"]
    assert comp_b_id is not None

    # 3. User 1 Upload Document Metadata Context
    file_bytes = b"%PDF-1.4\n%test pdf data\n%%EOF"
    upload_res = client.post(
        "/documents",
        data={
            "company_id": comp_a_id,
            "doc_type": "10K",
            "fiscal_period": "FY-2024",
        },
        files={"file": ("AAPL_10K_2024.pdf", BytesIO(file_bytes), "application/pdf")},
        headers=headers1,
    )
    assert upload_res.status_code == 201
    doc_a = upload_res.json()
    doc_a_id = doc_a["id"]

    # 4. Create Financial Statement (Income Statement) under User 1
    stmt_res = client.post(
        "/financial-statements",
        json={
            "company_id": comp_a_id,
            "document_id": doc_a_id,
            "statement_type": "income",
            "fiscal_period": "FY-2024",
            "line_items": {
                "Revenues": 1000.0,
                "Net Income": 200.0,
                "Operating Income": 300.0,
            },
        },
        headers=headers1,
    )
    assert stmt_res.status_code == 201
    income_stmt = stmt_res.json()
    assert (
        income_stmt["normalized_line_items"]["revenue"] == 1000.0
    )  # Mapping standardisation alias check
    assert income_stmt["normalized_line_items"]["net_income"] == 200.0
    stmt_a_id = income_stmt["id"]

    # 5. Verify Accounting Identity Validation Failures (Balance Sheet)
    bs_fail_res = client.post(
        "/financial-statements",
        json={
            "company_id": comp_a_id,
            "document_id": doc_a_id,
            "statement_type": "balance",
            "fiscal_period": "FY-2024",
            "line_items": {
                "Total Assets": 100.0,
                "Total Liabilities": 50.0,
                "Total Equity": 40.0,  # Unbalanced: 50 + 40 = 90 != 100
            },
        },
        headers=headers1,
    )
    assert bs_fail_res.status_code == 400
    assert "Balance sheet identity violation" in bs_fail_res.json()["detail"]

    # 6. Verify Accounting Identity Validation Success (Balance Sheet)
    bs_success_res = client.post(
        "/financial-statements",
        json={
            "company_id": comp_a_id,
            "document_id": doc_a_id,
            "statement_type": "balance",
            "fiscal_period": "FY-2024",
            "line_items": {
                "Total Assets": 100.0,
                "Total Liabilities": 60.0,
                "Total Equity": 40.0,  # Balanced: 60 + 40 = 100
            },
        },
        headers=headers1,
    )
    assert bs_success_res.status_code == 201

    # 7. Update Statement (generating version history versions)
    patch_res = client.patch(
        f"/financial-statements/{stmt_a_id}",
        json={
            "line_items": {
                "Revenue": 1100.0,
                "Net Income": 220.0,
            },
            "change_reason": "Corrected revenues after final auditor reconciliation.",
        },
        headers=headers1,
    )
    assert patch_res.status_code == 200
    updated_stmt = patch_res.json()
    assert updated_stmt["normalized_line_items"]["revenue"] == 1100.0
    assert updated_stmt["normalized_line_items"]["net_income"] == 220.0

    # Retrieve Statement version log
    history_res = client.get(
        f"/financial-statements/history?statement_id={stmt_a_id}",
        headers=headers1,
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 1
    assert history[0]["version"] == 1
    assert history[0]["line_items"]["revenue"] == 1000.0  # Old version has old values

    # 8. Side-by-side comparison report
    compare_res = client.get(
        f"/financial-statements/{stmt_a_id}/compare",
        headers=headers1,
    )
    assert compare_res.status_code == 200
    comparison = compare_res.json()
    assert comparison["comparison"]["revenue"]["as_reported"] == 1100.0
    assert comparison["comparison"]["revenue"]["normalized"] == 1100.0

    # 9. Update Document File (generating DocumentVersion logs)
    new_file_bytes = b"%PDF-1.4\n%updated pdf data\n%%EOF"
    doc_patch_res = client.patch(
        f"/documents/{doc_a_id}",
        data={"change_reason": "Re-uploaded clear PDF filing scan."},
        files={
            "file": (
                "AAPL_10K_2024_revised.pdf",
                BytesIO(new_file_bytes),
                "application/pdf",
            )
        },
        headers=headers1,
    )
    assert doc_patch_res.status_code == 200

    # Fetch document version list
    doc_ver_res = client.get(
        f"/documents/{doc_a_id}/versions",
        headers=headers1,
    )
    assert doc_ver_res.status_code == 200
    doc_versions = doc_ver_res.json()
    assert len(doc_versions) == 1
    assert doc_versions[0]["version"] == 1
    assert doc_versions[0]["change_reason"] == "Re-uploaded clear PDF filing scan."

    # 10. Workspace Isolation Tests:
    # User 2 attempts to retrieve User 1's Document metadata -> should return 404
    u2_get_doc_res = client.get(
        f"/documents/{doc_a_id}",
        headers=headers2,
    )
    assert u2_get_doc_res.status_code == 404

    # User 2 attempts to retrieve User 1's statement -> should return 404
    u2_get_stmt_res = client.get(
        f"/financial-statements/{stmt_a_id}",
        headers=headers2,
    )
    assert u2_get_stmt_res.status_code == 404

    # User 2 attempts to update User 1's statement -> should return 404
    u2_patch_stmt_res = client.patch(
        f"/financial-statements/{stmt_a_id}",
        json={
            "line_items": {"revenue": 5000.0},
            "change_reason": "Malicious attempt to overwrite.",
        },
        headers=headers2,
    )
    assert u2_patch_stmt_res.status_code == 404
