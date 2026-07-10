"""
Integration tests for RAG Chat and Ask API endpoints.
"""

import os
from io import BytesIO
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.core.dependencies import get_llm_provider
from app.domain.interfaces.providers import LLMProvider, LLMResponse
from app.infrastructure.db.manager import db_manager
from app.main import app
from app.workers.celery_app import celery_app


class MockLLMProvider(LLMProvider):
    """
    Mock LLMProvider to avoid network calls during integration tests.
    """

    def __init__(self) -> None:
        self.response_text = "Net Income was $93.7 billion [Chunk 1]."

    async def complete(self, prompt: str, schema: Any = None) -> LLMResponse:
        return LLMResponse(
            text=self.response_text,
            structured_data=None,
            prompt_tokens=25,
            completion_tokens=30,
            latency_ms=50.0,
        )

    async def complete_with_tools(self, prompt: str, tools: list) -> LLMResponse:
        return await self.complete(prompt)


@pytest.fixture(autouse=True)
def configure_celery_eager():
    """Forces Celery to run tasks synchronously inline for integration tests."""
    original_eager = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = original_eager


@pytest_asyncio.fixture
def mock_llm():
    """Inject Mock LLM dependency override."""
    mock = MockLLMProvider()
    app.dependency_overrides[get_llm_provider] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_llm_provider, None)


@pytest_asyncio.fixture
async def test_db():
    """Clean database before and after runs."""
    from sqlalchemy import text

    db_manager.initialize()

    async with db_manager.session_factory() as session:
        await session.execute(text("PRAGMA foreign_keys = OFF;"))


        await session.execute(text("DELETE FROM citations;"))
        await session.execute(text("DELETE FROM conversation_messages;"))
        await session.execute(text("DELETE FROM conversations;"))
        await session.execute(text("DELETE FROM document_chunks;"))
        await session.execute(text("DELETE FROM parsing_manifests;"))
        await session.execute(text("DELETE FROM documents;"))
        await session.execute(text("DELETE FROM companies;"))
        await session.execute(text("DELETE FROM refresh_tokens;"))
        await session.execute(text("DELETE FROM workspace_memberships;"))
        await session.execute(text("DELETE FROM workspaces;"))
        await session.execute(text("DELETE FROM users;"))
        await session.execute(text("PRAGMA foreign_keys = ON;"))
        await session.commit()

    yield


def test_stateless_ask_and_multi_turn_chat(
    test_db: None, mock_llm: MockLLMProvider
) -> None:
    client = TestClient(app)

    # 1. Register User 1 and fetch headers
    u1_res = client.post(
        "/auth/register",
        json={
            "email": "chat_user1@equityiq.com",
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

    # Create Company Apple
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

    # Upload document AAPL 10K
    dummy_text = (
        "Item 1. Business Description\n\n"
        "Apple Inc. is a consumer technology company. "
        "During the period, Net Income was $93.7 billion. "
        "Research and development costs were significant."
    )
    file_bytes = b"%PDF-1.4\n" + dummy_text.encode("utf-8") + b"\n%%EOF"

    upload_res = client.post(
        "/documents",
        data={
            "company_id": comp_a_id,
            "doc_type": "10K",
            "fiscal_period": "FY-2024",
        },
        files={"file": ("AAPL_10K.pdf", BytesIO(file_bytes), "application/pdf")},
        headers=headers1,
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]

    # Save to storage path and parse
    os.makedirs(os.path.dirname(doc_data["storage_path"]), exist_ok=True)
    with open(doc_data["storage_path"], "wb") as f:
        f.write(file_bytes)

    try:
        parse_res = client.post(f"/documents/{doc_id}/parse", headers=headers1)
        assert parse_res.status_code == 202

        # 2. Test stateless ask (POST /chat/ask)
        ask_res = client.post(
            "/chat/ask",
            json={
                "query_text": "What was Net Income?",
                "company_id": comp_a_id,
            },
            headers=headers1,
        )
        assert ask_res.status_code == 200
        ask_data = ask_res.json()
        assert "93.7 billion" in ask_data["answer"]
        assert len(ask_data["citations"]) == 1
        assert ask_data["citations"][0]["document_name"].endswith("AAPL_10K.pdf")
        assert ask_data["confidence_score"] > 0.0

        # 3. Test multi-turn chat (POST /chat/chat)
        chat_res_1 = client.post(
            "/chat/chat",
            json={
                "query_text": "What was Net Income?",
                "company_id": comp_a_id,
            },
            headers=headers1,
        )
        assert chat_res_1.status_code == 200
        chat_data_1 = chat_res_1.json()
        conv_id = chat_data_1["conversation_id"]
        assert conv_id is not None
        assert len(chat_data_1["citations"]) == 1

        # Continue conversation
        chat_res_2 = client.post(
            "/chat/chat",
            json={
                "query_text": "Is this above forecast?",
                "conversation_id": conv_id,
                "company_id": comp_a_id,
            },
            headers=headers1,
        )
        assert chat_res_2.status_code == 200
        assert chat_res_2.json()["conversation_id"] == conv_id

        # 4. Get active history
        history_res = client.get(f"/chat/conversation/{conv_id}", headers=headers1)
        assert history_res.status_code == 200
        history_data = history_res.json()
        # Should have 2 messages (user turn 1, assistant turn 1, user turn 2, assistant turn 2) -> 4 messages total
        assert len(history_data["messages"]) == 4

        # 5. Register User 2 (Tenant 2) and try to access User 1's conversation
        u2_res = client.post(
            "/auth/register",
            json={
                "email": "chat_user2@equityiq.com",
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

        # User 2 tries to GET User 1's conversation
        leak_res = client.get(f"/chat/conversation/{conv_id}", headers=headers2)
        assert leak_res.status_code == 404  # Not found due to tenancy block

        # User 2 tries to POST to User 1's conversation
        leak_post = client.post(
            "/chat/chat",
            json={
                "query_text": "Hack query",
                "conversation_id": conv_id,
            },
            headers=headers2,
        )
        assert leak_post.status_code == 404

        # 6. Delete conversation
        del_res = client.delete(f"/chat/conversation/{conv_id}", headers=headers1)
        assert del_res.status_code == 200

        # Attempt to retrieve deleted session
        after_del = client.get(f"/chat/conversation/{conv_id}", headers=headers1)
        assert after_del.status_code == 404

    finally:
        if os.path.exists(doc_data["storage_path"]):
            try:
                os.remove(doc_data["storage_path"])
            except OSError:
                pass
