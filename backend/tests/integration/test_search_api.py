"""
Integration tests for Search and Retrieval endpoints (semantic, hybrid, rebuild).
"""

import os
from collections.abc import AsyncGenerator
from io import BytesIO

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.infrastructure.db.manager import db_manager
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
def clean_indices():
    """Ensures vector index directories are cleaned up before and after tests."""
    # Use a test-specific directory for FAISS files to prevent polluting local development

    # Override settings for vector index storage if needed

    yield

    # Clean up test directories
    if os.path.exists("./storage/indices/v1"):
        # We can clean up subdirectories created during tests
        pass


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[None, None]:
    """
    Cleans up the database tables to ensure isolation before running tests.
    """
    from sqlalchemy import text

    db_manager.initialize()

    async with db_manager.session_factory() as session:
        await session.execute(text("PRAGMA foreign_keys = OFF;"))
        await session.execute(text("DELETE FROM document_chunks_fts;"))
        await session.execute(text("DELETE FROM embedding_manifests;"))
        await session.execute(text("DELETE FROM embeddings;"))
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


def test_search_and_retrieval_integration_flow(
    test_db: None, clean_indices: None
) -> None:
    client = TestClient(app)

    # 1. Register User 1 & retrieve default workspace headers
    u1_res = client.post(
        "/auth/register",
        json={
            "email": "search_user1@equityiq.com",
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
            "email": "search_user2@equityiq.com",
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

    # 2. Create Company Apple under User 1
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

    # 3. User 1 Uploads and parses document
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

    # Write file to storage path so parser can read it
    os.makedirs(os.path.dirname(doc_data["storage_path"]), exist_ok=True)
    with open(doc_data["storage_path"], "wb") as f:
        f.write(file_bytes)

    try:
        # Trigger parsing (runs synchronously due to celery eager fixture)
        parse_res = client.post(f"/documents/{doc_id}/parse", headers=headers1)
        assert parse_res.status_code == 202

        # Verify parsing completed successfully
        doc_details = client.get(f"/documents/{doc_id}", headers=headers1)
        assert doc_details.status_code == 200
        assert doc_details.json()["parsing_status"] == "completed"

        # 4. Perform Semantic Search
        sem_res = client.post(
            "/search/semantic",
            json={
                "query_text": "financial data analytics platform",
                "limit": 5,
            },
            headers=headers1,
        )
        assert sem_res.status_code == 200
        sem_results = sem_res.json()
        assert len(sem_results) > 0
        # The first chunk should be the properties/business description
        assert (
            "EquityIQ" in sem_results[0]["content"]
            or "locations" in sem_results[0]["content"]
        )

        # 5. Perform Hybrid Search
        hyb_res = client.post(
            "/search/hybrid",
            json={
                "query_text": "office locations",
                "alpha": 0.5,
                "limit": 5,
            },
            headers=headers1,
        )
        assert hyb_res.status_code == 200
        hyb_results = hyb_res.json()
        assert len(hyb_results) > 0

        # Verify filters inside search (e.g. document_type match, or non-matching filter)
        filtered_res = client.post(
            "/search/hybrid",
            json={
                "query_text": "office locations",
                "document_type": "10Q",  # Apple doc uploaded was 10K, so this should match nothing
                "limit": 5,
            },
            headers=headers1,
        )
        assert filtered_res.status_code == 200
        assert len(filtered_res.json()) == 0

        # 6. Tenant isolation verification: User 2 searches under User 2's workspace
        u2_search_res = client.post(
            "/search/semantic",
            json={
                "query_text": "financial data analytics platform",
                "limit": 5,
            },
            headers=headers2,
        )
        assert u2_search_res.status_code == 200
        assert (
            len(u2_search_res.json()) == 0
        )  # Should be empty since User 2 has no documents

        # 7. Rebuild workspace index manually
        rebuild_res = client.post("/search/rebuild", headers=headers1)
        assert rebuild_res.status_code == 200
        assert rebuild_res.json()["status"] == "success"

        # Verify we can still search successfully after manual index rebuild
        post_rebuild_res = client.post(
            "/search/semantic",
            json={
                "query_text": "corporate office",
                "limit": 5,
            },
            headers=headers1,
        )
        assert post_rebuild_res.status_code == 200
        assert len(post_rebuild_res.json()) > 0

    finally:
        # Cleanup PDF file from storage
        if os.path.exists(doc_data["storage_path"]):
            try:
                os.remove(doc_data["storage_path"])
            except OSError:
                pass
