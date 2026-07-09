"""
Provider Interfaces (Protocols) and DTOs for AI/RAG integrations.
"""

from collections.abc import Callable
from typing import Any, Protocol, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)


class LLMResponse(BaseModel):
    """Normalized response envelope returned by LLM Providers."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(description="Raw text generation from the model")
    structured_data: Any = Field(
        default=None,
        description="De-serialized Pydantic model output if schema requested",
    )
    prompt_tokens: int = Field(default=0, description="Tokens in input prompt")
    completion_tokens: int = Field(default=0, description="Tokens in output completion")
    latency_ms: float = Field(default=0.0, description="Request execution duration")


class Tool(BaseModel):
    """Represents a capability function bound to the LLM agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: str = Field(description="Tool identification key")
    description: str = Field(description="Description exposed to LLM instruction")
    func: Callable[..., Any] = Field(description="Actual local callback reference")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for parameters validation"
    )


class EmbeddedChunk(BaseModel):
    """Vector database chunk representation containing source text and metadata."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="Matches vector unique identifier")
    document_id: UUID = Field(description="Parent source document file")
    chunk_index: int = Field(description="Sequential position of chunk")
    page_number: int = Field(ge=1, description="Page index where chunk text resides")
    section_label: str = Field(description="Chapter/Section context (e.g. Item 1A)")
    text_preview: str = Field(description="Underlying raw text segment")
    vector: list[float] = Field(description="Computed numerical embedding vector")
    embedding_model_version: str = Field(description="Model identifier version string")


class MetadataFilter(BaseModel):
    """Query filter parameters for hybrid/dense search constraints."""

    model_config = ConfigDict(frozen=True)

    company_id: UUID | None = None
    document_id: UUID | None = None
    doc_type: str | None = None
    fiscal_period: str | None = None


class ScoredChunk(BaseModel):
    """Match result returned by Vector Store query."""

    model_config = ConfigDict(frozen=True)

    chunk: EmbeddedChunk = Field(description="Core chunk entity details")
    score: float = Field(description="Search similarity metric score")


class LLMProvider(Protocol):
    """Abstract interface for LLM interaction."""

    async def complete(self, prompt: str, schema: type[T] | None = None) -> LLMResponse:
        """Execute text completion, optionally enforcing Pydantic schema validation."""
        ...

    async def complete_with_tools(self, prompt: str, tools: list[Tool]) -> LLMResponse:
        """Execute text generation with tool-calling integrations."""
        ...


class EmbeddingProvider(Protocol):
    """Abstract interface for text embedding calculation."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Calculate numerical floating point arrays for input strings."""
        ...


class VectorStore(Protocol):
    """Abstract interface for Vector Store operations."""

    async def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        """Insert or refresh chunk vectors inside storage."""
        ...

    async def query(
        self, vector: list[float], filters: MetadataFilter, top_k: int
    ) -> list[ScoredChunk]:
        """Query vector database for similar chunks matching constraints."""
        ...

    async def delete_by_document(self, document_id: UUID) -> None:
        """Remove all embedded chunks belonging to a document."""
        ...


class TokenizerProvider(Protocol):
    """Abstract interface for token count calculations."""

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a string."""
        ...
