"""
Integration tests for Document Intelligence parsing workers and endpoints.
"""

import os
from io import BytesIO
from uuid import uuid4

from collections.abc import AsyncGenerator
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.db.models.base import Base
from app.infrastructure.db.session import get_db_session
from app.main import app
from app.workers.celery_app import celery_app


@pytest.fixture(autouse=True)
def configure_celery_eager():
    """Forces Celery to run tasks synchronously inline for integration tests."""
    original_eager = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = original_eager


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[None, None]:
    """
    Cleans up the database tables to ensure isolation before running tests.
    """
    from app.infrastructure.db.manager import db_manager
    from sqlalchemy import text

    db_manager.initialize()

    async with db_manager.session_factory() as session:
        await session.execute(text("PRAGMA foreign_keys = OFF;"))
        await session.execute(text("DELETE FROM document_chunks;"))
        await session.execute(text("DELETE FROM parsing_manifests;"))
        await session.execute(text("DELETE FROM document_versions;"))
        await session.execute(text("DELETE FROM financial_statement_versions;"))
        await session.execute(text("DELETE FROM financial_statements;"))
        await session.execute(text("DELETE FROM documents;"))
        await session.execute(text("DELETE FROM companies;"))
        await session.execute(text("DELETE FROM refresh_tokens;"))
        await session.execute(text("DELETE FROM workspace_memberships;"))
        await session.execute(text("DELETE FROM workspaces;"))
        await session.execute(text("DELETE FROM users;"))
        await session.execute(text("PRAGMA foreign_keys = ON;"))
        await session.commit()

    yield


def test_document_parsing_integration_flow(test_db: None) -> None:
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

    # 3. User 1 Upload Document
    # We will write a dummy PDF file content with actual text layout details
    dummy_text = (
        "Item 1. Business Description\n\n"
        "EquityIQ is a leading financial data analytics platform. "
        "It parses documents and extracts insights deterministically.\n\n"
        "Item 2. Properties\n\n"
        "The company has corporate office locations globally."
    )
    file_bytes = b"%PDF-1.4\n" + dummy_text.encode("utf-8") + b"\n%%EOF"

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
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["parsing_status"] == "pending"

    # Make sure physical folder is clean / exists for test
    os.makedirs(os.path.dirname(doc_data["storage_path"]), exist_ok=True)
    with open(doc_data["storage_path"], "wb") as f:
        f.write(file_bytes)

    try:
        # 4. Trigger parsing POST /documents/{id}/parse
        parse_res = client.post(f"/documents/{doc_id}/parse", headers=headers1)
        assert parse_res.status_code == 202
        assert parse_res.json()["status"] == "queued"

        # 5. Retrieve Document details to verify parsing completed successfully
        doc_details = client.get(f"/documents/{doc_id}", headers=headers1)
        assert doc_details.status_code == 200
        assert doc_details.json()["parsing_status"] == "completed"
        assert doc_details.json()["parsing_confidence"] > 0.0

        # 6. GET /documents/{id}/chunks
        chunks_res = client.get(f"/documents/{doc_id}/chunks", headers=headers1)
        assert chunks_res.status_code == 200
        chunk_list = chunks_res.json()
        assert len(chunk_list) > 0
        assert chunk_list[0]["section_heading"] == "Item 2. Properties"

        # 7. Reprocess document POST /documents/{id}/reprocess
        reprocess_res = client.post(f"/documents/{doc_id}/reprocess", headers=headers1)
        assert reprocess_res.status_code == 202
        assert reprocess_res.json()["status"] == "queued"

        # Verify parsing manifest details via chunks endpoint
        chunks_after = client.get(f"/documents/{doc_id}/chunks", headers=headers1).json()
        assert len(chunks_after) > 0
        # The parser_run_idx should increment to 2
        assert chunks_after[0]["metadata"]["parse_version"] == 2

        # 8. Workspace Isolation Check
        # User 2 tries to trigger parsing on User 1's document -> 404
        user2_parse_res = client.post(f"/documents/{doc_id}/parse", headers=headers2)
        assert user2_parse_res.status_code == 404

        # User 2 tries to fetch chunks of User 1's document -> 404
        user2_chunks_res = client.get(f"/documents/{doc_id}/chunks", headers=headers2)
        assert user2_chunks_res.status_code == 404

    finally:
        # Clean up test file from disk
        if os.path.exists(doc_data["storage_path"]):
            try:
                os.remove(doc_data["storage_path"])
            except OSError:
                pass
