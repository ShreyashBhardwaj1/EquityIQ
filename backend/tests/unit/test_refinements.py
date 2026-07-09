"""
Unit tests for Milestone 7 Engineering Refinements.
"""

import uuid
from datetime import datetime

from app.application.services.confidence_scorer import ConfidenceScorer
from app.domain.entities.conversation import Citation, LLMRequest
from app.infrastructure.llm.prompts.prompt_loader import (
    BASE_INSTRUCTIONS,
    CITATION_INSTRUCTIONS,
    FINANCIAL_SAFETY_RULES,
    SYSTEM_PROMPT,
)


def test_external_prompts_loaded():
    """Verify that templates are loaded correctly from markdown files instead of being hardcoded."""
    assert len(SYSTEM_PROMPT) > 20
    assert len(FINANCIAL_SAFETY_RULES) > 20
    assert len(CITATION_INSTRUCTIONS) > 20
    assert len(BASE_INSTRUCTIONS) > 50
    assert "EquityIQ" in SYSTEM_PROMPT
    assert "SAFETY RULES" in FINANCIAL_SAFETY_RULES


def test_grounding_score_calculation():
    """Test deterministic grounding score computation based on cited sentences."""
    scorer = ConfidenceScorer()

    # 1. Fully grounded response (1 sentence, cited)
    text_1 = "Revenue grew by 15% [Chunk 1]."
    assert scorer.calculate_grounding_score(text_1) == 1.0

    # 2. Partially grounded response (2 sentences, 1 cited)
    text_2 = "Net income was $50B [Chunk 2]. We expect further growth next quarter."
    assert scorer.calculate_grounding_score(text_2) == 0.5

    # 3. Ungrounded response (2 sentences, 0 cited)
    text_3 = "The company is performing well. The management team is optimistic."
    assert scorer.calculate_grounding_score(text_3) == 0.0

    # 4. Empty text
    assert scorer.calculate_grounding_score("") == 0.0


def test_llm_request_telemetry_schema():
    """Assert that LLMRequest model includes all required refinement metrics."""
    req_id = uuid.uuid4()
    ws_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    telemetry = LLMRequest(
        id=req_id,
        workspace_id=ws_id,
        conversation_id=conv_id,
        model_name="gemini-2.5-pro",
        prompt_version="1.0.0",
        embedding_version="bge-small-en-v1.5",
        parser_version="1.0.0",
        vector_index_version="v1",
        input_tokens=1000,
        output_tokens=500,
        retrieval_latency_ms=120.5,
        generation_latency_ms=1450.2,
        total_latency_ms=1570.7,
        confidence_score=0.88,
        grounding_score=0.95,
        created_at=datetime.utcnow(),
    )

    assert telemetry.id == req_id
    assert telemetry.workspace_id == ws_id
    assert telemetry.conversation_id == conv_id
    assert telemetry.model_name == "gemini-2.5-pro"
    assert telemetry.confidence_score == 0.88
    assert telemetry.grounding_score == 0.95


def test_citation_explainability_fields():
    """Assert that Citation entity schema correctly enforces the explainability fields."""
    cit_id = uuid.uuid4()
    msg_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    citation = Citation(
        id=cit_id,
        message_id=msg_id,
        chunk_id=chunk_id,
        document_id=doc_id,
        document_name="annual_report.pdf",
        page_number=10,
        section_heading="Item 7",
        snippet_preview="Net cash was positive...",
        score=0.85,
        rank=2,
        semantic_score=0.9,
        keyword_score=0.7,
        hybrid_score=0.85,
        retrieval_method="hybrid",
    )

    assert citation.id == cit_id
    assert citation.rank == 2
    assert citation.semantic_score == 0.9
    assert citation.keyword_score == 0.7
    assert citation.hybrid_score == 0.85
    assert citation.retrieval_method == "hybrid"
