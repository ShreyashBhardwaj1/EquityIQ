"""
FastAPI router implementation for Chat and Ask RAG routes.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.conversation_service import ConversationService
from app.application.services.rag_service import RAGService
from app.core.dependencies import (
    get_conversation_service,
    get_current_user,
    get_current_workspace_id,
    get_rag_service,
)
from app.domain.entities.user import User
from app.domain.exceptions import (
    ConversationNotFoundError,
    PromptInjectionFlaggedError,
    ResponseValidationError,
)
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/chat", tags=["RAG Chat & Q&A"])


class ChatRequest(BaseModel):
    """
    Payload schema for continuing or starting multi-turn conversation.
    """

    query_text: str = Field(..., description="The query/question string to send to RAG")
    company_id: UUID | None = Field(
        default=None, description="Optional scoping company filter"
    )
    conversation_id: UUID | None = Field(
        default=None, description="Optional conversation session ID to resume"
    )


class AskRequest(BaseModel):
    """
    Payload schema for stateless one-off Q&A.
    """

    query_text: str = Field(..., description="The query/question string to send to RAG")
    company_id: UUID | None = Field(
        default=None, description="Optional scoping company filter"
    )


class CitationResponse(BaseModel):
    """
    Grounding citation response payload schema.
    """

    id: UUID
    chunk_id: UUID | None
    document_id: UUID
    document_name: str
    page_number: int
    section_heading: str | None
    snippet_preview: str
    score: float
    rank: int
    semantic_score: float | None
    keyword_score: float | None
    hybrid_score: float
    retrieval_method: str


class MessageResponse(BaseModel):
    """
    Turn message context response payload schema.
    """

    id: UUID
    role: str
    content: str
    created_at: datetime
    citations: list[CitationResponse] = []


class ChatResponse(BaseModel):
    """
    Multi-turn active turn response payload schema.
    """

    answer: str
    confidence_score: float
    grounding_score: float
    citations: list[CitationResponse]
    conversation_id: UUID
    metadata: dict[str, Any]


class AskResponse(BaseModel):
    """
    Stateless query response payload schema.
    """

    answer: str
    confidence_score: float
    grounding_score: float
    citations: list[CitationResponse]
    metadata: dict[str, Any]


class ConversationDetailResponse(BaseModel):
    """
    Rich conversation session detail response.
    """

    id: UUID
    workspace_id: UUID
    user_id: UUID
    title: str
    summary: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db_session),
    rag_service: RAGService = Depends(get_rag_service),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ChatResponse:
    """
    Starts or continues a multi-turn chat session inside a workspace.
    Saves conversation turns and citations.
    """
    try:
        conv_id = request.conversation_id
        if not conv_id:
            # Generate session title from initial query text
            title = (
                request.query_text[:40] + "..."
                if len(request.query_text) > 40
                else request.query_text
            )
            conv = await conversation_service.create_conversation(
                workspace_id=workspace_id, user_id=current_user.id, title=title
            )
            conv_id = conv.id

        result = await rag_service.execute_rag(
            db_session=db,
            user_query=request.query_text,
            workspace_id=workspace_id,
            user_id=current_user.id,
            company_id=request.company_id,
            conversation_id=conv_id,
        )

        await db.commit()

        # Map domain citations to API schema
        api_citations = [
            CitationResponse(
                id=c.id,
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                document_name=c.document_name,
                page_number=c.page_number,
                section_heading=c.section_heading,
                snippet_preview=c.snippet_preview,
                score=c.score,
                rank=c.rank,
                semantic_score=c.semantic_score,
                keyword_score=c.keyword_score,
                hybrid_score=c.hybrid_score,
                retrieval_method=c.retrieval_method,
            )
            for c in result["citations"]
        ]

        return ChatResponse(
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            grounding_score=result["grounding_score"],
            citations=api_citations,
            conversation_id=conv_id,
            metadata=result["metadata"],
        )

    except ConversationNotFoundError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from None
    except PromptInjectionFlaggedError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from None
    except ResponseValidationError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat execution failed: {e}",
        ) from None


@router.post("/ask", response_model=AskResponse, status_code=status.HTTP_200_OK)
async def ask(
    request: AskRequest,
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db_session),
    rag_service: RAGService = Depends(get_rag_service),
) -> AskResponse:
    """
    Performs stateless RAG grounding. Does not save messages or citations.
    """
    try:
        result = await rag_service.execute_rag(
            db_session=db,
            user_query=request.query_text,
            workspace_id=workspace_id,
            user_id=current_user.id,
            company_id=request.company_id,
            conversation_id=None,
        )

        api_citations = [
            CitationResponse(
                id=c.id,
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                document_name=c.document_name,
                page_number=c.page_number,
                section_heading=c.section_heading,
                snippet_preview=c.snippet_preview,
                score=c.score,
                rank=c.rank,
                semantic_score=c.semantic_score,
                keyword_score=c.keyword_score,
                hybrid_score=c.hybrid_score,
                retrieval_method=c.retrieval_method,
            )
            for c in result["citations"]
        ]

        return AskResponse(
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            grounding_score=result["grounding_score"],
            citations=api_citations,
            metadata=result["metadata"],
        )

    except PromptInjectionFlaggedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from None
    except ResponseValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stateless query execution failed: {e}",
        ) from None


@router.get(
    "/conversation/{conversation_id}",
    response_model=ConversationDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_conversation(
    conversation_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ConversationDetailResponse:
    """
    Retrieve active messages and citations of a specific conversation session.
    """
    try:
        conv = await conversation_service.get_conversation(
            conversation_id, workspace_id
        )
        messages = await conversation_service.get_active_messages(
            conversation_id, workspace_id
        )

        # Map to response schema
        api_messages = []
        for msg in messages:
            api_cits = [
                CitationResponse(
                    id=c.id,
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    document_name=c.document_name,
                    page_number=c.page_number,
                    section_heading=c.section_heading,
                    snippet_preview=c.snippet_preview,
                    score=c.score,
                    rank=c.rank,
                    semantic_score=c.semantic_score,
                    keyword_score=c.keyword_score,
                    hybrid_score=c.hybrid_score,
                    retrieval_method=c.retrieval_method,
                )
                for c in msg.citations
            ]

            api_messages.append(
                MessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    created_at=msg.created_at,
                    citations=api_cits,
                )
            )

        return ConversationDetailResponse(
            id=conv.id,
            workspace_id=conv.workspace_id,
            user_id=conv.user_id,
            title=conv.title,
            summary=conv.summary,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=api_messages,
        )

    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation details: {e}",
        ) from None


@router.delete(
    "/conversation/{conversation_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_conversation(
    conversation_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db_session),
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> dict[str, str]:
    """
    Deletes conversation history session and all linked messages/citations.
    """
    try:
        await conversation_service.delete_conversation(conversation_id, workspace_id)
        await db.commit()
        return {"status": "success", "message": "Conversation session deleted."}
    except ConversationNotFoundError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from None
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {e}",
        ) from None
