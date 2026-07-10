"""
Integration tests for Financial Intelligence API endpoints.
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


def test_financial_intelligence_api_flow(test_db: None) -> None:
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
    comp_a_id = comp_res.json()["id"]

    # 3. User 1 Upload Document Metadata
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
    doc_a_id = upload_res.json()["id"]

    # 4. Create Financial Statements for calculations to succeed
    # Income Statement
    client.post(
        "/financial-statements",
        json={
            "company_id": comp_a_id,
            "document_id": doc_a_id,
            "statement_type": "income",
            "fiscal_period": "FY-2024",
            "line_items": {
                "Revenues": 100000.0,
                "Net Income": 20000.0,
                "Operating Income": 30000.0,
            },
        },
        headers=headers1,
    )
    # Balance Sheet
    client.post(
        "/financial-statements",
        json={
            "company_id": comp_a_id,
            "document_id": doc_a_id,
            "statement_type": "balance",
            "fiscal_period": "FY-2024",
            "line_items": {
                "Total Assets": 500000.0,
                "Total Liabilities": 200000.0,
                "Total Equity": 300000.0,
                "Cash and Cash Equivalents": 50000.0,
                "Accounts Receivable": 40000.0,
                "Inventory": 30000.0,
                "Current Assets": 150000.0,
                "Current Liabilities": 100000.0,
            },
        },
        headers=headers1,
    )
    # Cash Flow Statement
    client.post(
        "/financial-statements",
        json={
            "company_id": comp_a_id,
            "document_id": doc_a_id,
            "statement_type": "cash_flow",
            "fiscal_period": "FY-2024",
            "line_items": {
                "Net Cash Provided by Operating Activities": 25000.0,
                "Capital Expenditures": 5000.0,
            },
        },
        headers=headers1,
    )

    # 5. Run Calculation Pipeline
    calc_res = client.post(
        f"/companies/{comp_a_id}/calculate?fiscal_period=FY-2024",
        headers=headers1,
    )
    assert calc_res.status_code == 200
    calc_data = calc_res.json()
    assert "overall_score" in calc_data
    assert "recommendation" in calc_data
    assert "portfolio_signal" in calc_data
    assert "ratio_engine_version" in calc_data
    assert "health_engine_version" in calc_data
    assert "risk_engine_version" in calc_data
    assert "recommendation_policy_version" in calc_data
    assert "financial_intelligence_version" in calc_data

    # 6. Fetch Explainability
    explain_res = client.get(
        f"/companies/{comp_a_id}/explainability?fiscal_period=FY-2024",
        headers=headers1,
    )
    assert explain_res.status_code == 200
    explain_data = explain_res.json()
    assert explain_data["company_id"] == comp_a_id
    assert explain_data["fiscal_period"] == "FY-2024"
    assert "health_score_details" in explain_data
    assert "risks_detected" in explain_data
    assert "engine_versions" in explain_data
    assert "positive_signals" in explain_data
    assert "negative_signals" in explain_data
    assert "deterministic_reasoning_steps" in explain_data
    assert "rules_triggered" in explain_data
    assert "policies_applied" in explain_data
    assert "ratios_influencing_recommendation" in explain_data
    assert "risk_factors_influencing_recommendation" in explain_data
    assert "trend_factors_influencing_recommendation" in explain_data
    assert "confidence_breakdown" in explain_data

    # 7. Fetch Dashboard
    dash_res = client.get(
        f"/companies/{comp_a_id}/dashboard?fiscal_period=FY-2024",
        headers=headers1,
    )
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["company_id"] == comp_a_id
    assert dash_data["fiscal_period"] == "FY-2024"
    assert "overall_score" in dash_data
    assert "category_scores" in dash_data
    assert "top_5_ratios" in dash_data
    assert "top_3_risks" in dash_data
    assert "strongest_positive_trend" in dash_data
    assert "weakest_trend" in dash_data
    assert "final_recommendation" in dash_data
    assert "recommendation_confidence" in dash_data
    assert "confidence_breakdown" in dash_data
    assert "engine_versions" in dash_data

    # 8. Workspace Isolation Tests
    # User 2 attempts to run calculation for Company A -> should return 404
    u2_calc_res = client.post(
        f"/companies/{comp_a_id}/calculate?fiscal_period=FY-2024",
        headers=headers2,
    )
    assert u2_calc_res.status_code == 404

    # User 2 attempts to fetch explainability for Company A -> should return 404
    u2_explain_res = client.get(
        f"/companies/{comp_a_id}/explainability?fiscal_period=FY-2024",
        headers=headers2,
    )
    assert u2_explain_res.status_code == 404

    # User 2 attempts to fetch dashboard for Company A -> should return 404
    u2_dash_res = client.get(
        f"/companies/{comp_a_id}/dashboard?fiscal_period=FY-2024",
        headers=headers2,
    )
    assert u2_dash_res.status_code == 404
