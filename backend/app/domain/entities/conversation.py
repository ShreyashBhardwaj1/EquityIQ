"""
Conversation, ConversationMessage, and Citation entities for RAG interactions.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    """
    Domain entity linking a specific generated answer segment to source chunk metadata.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    message_id: UUID = Field(
        description="Associated assistant conversation message identifier"
    )
    chunk_id: UUID | None = Field(
        default=None, description="Corresponding document chunk identifier"
    )
    document_id: UUID = Field(description="Parent source document identifier")
    document_name: str = Field(description="Name/Filename of the source document")
    page_number: int = Field(ge=1, description="Page index containing the cited chunk")
    section_heading: str | None = Field(
        default=None, description="Document section heading context"
    )
    snippet_preview: str = Field(
        description="Text segment preview matching the citation"
    )
    score: float = Field(description="Similarity score of the referenced chunk")
    rank: int = Field(default=1, description="Relevance rank of cited segment")
    semantic_score: float | None = Field(
        default=None, description="Semantic similarity vector score"
    )
    keyword_score: float | None = Field(
        default=None, description="BM25 keyword search score"
    )
    hybrid_score: float = Field(
        default=0.0, description="Combined hybrid ranking score"
    )
    retrieval_method: str = Field(
        default="hybrid", description="Method: semantic, keyword, hybrid"
    )


class ConversationMessage(BaseModel):
    """
    Single turn in a chat conversation session.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    conversation_id: UUID = Field(description="Parent conversation session identifier")
    role: str = Field(description="Turn role: user or assistant")
    content: str = Field(description="Raw text content of the message")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
    citations: list[Citation] = Field(
        default_factory=list, description="Citations grounding this response turn"
    )


class Conversation(BaseModel):
    """
    Active multi-turn conversation session scoped to workspace and user context.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    workspace_id: UUID = Field(description="Scoping target workspace identifier")
    user_id: UUID = Field(description="Owner user identifier")
    title: str = Field(description="Summarized or generated title for the session")
    summary: str | None = Field(
        default=None, description="Optional accumulated conversation summarization"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Session creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last turn update timestamp"
    )


class LLMRequest(BaseModel):
    """
    Domain entity capturing execution telemetry and metrics for an LLM RAG completion.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    workspace_id: UUID
    conversation_id: UUID | None = None
    model_name: str
    prompt_version: str
    embedding_version: str
    parser_version: str
    vector_index_version: str
    input_tokens: int
    output_tokens: int
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    confidence_score: float
    grounding_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
