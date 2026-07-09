"""
SQLAlchemy repository adapter for Conversation and ConversationMessage.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.entities.conversation import (
    Citation,
    Conversation,
    ConversationMessage,
    LLMRequest,
)
from app.domain.interfaces.repositories import ConversationRepository
from app.infrastructure.db.models.conversation import (
    ConversationMessageORM,
    ConversationORM,
    LLMRequestORM,
)
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyConversationRepository(
    BaseRepository[ConversationORM], ConversationRepository
):
    """
    SQLAlchemy-backed implementation of the ConversationRepository interface.
    """

    def _to_domain(self, orm: ConversationORM) -> Conversation:
        """Translates ORM model to Domain Entity."""
        return Conversation(
            id=orm.id,
            workspace_id=orm.workspace_id,
            user_id=orm.user_id,
            title=orm.title,
            summary=orm.summary,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: Conversation) -> ConversationORM:
        """Translates Domain Entity to ORM model."""
        return ConversationORM(
            id=domain.id,
            workspace_id=domain.workspace_id,
            user_id=domain.user_id,
            title=domain.title,
            summary=domain.summary,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def _message_to_domain(self, orm: ConversationMessageORM) -> ConversationMessage:
        """Translates message ORM to domain message."""
        citations = []
        if orm.citations:
            for cit in orm.citations:
                citations.append(
                    Citation(
                        id=cit.id,
                        message_id=cit.message_id,
                        chunk_id=cit.chunk_id,
                        document_id=cit.document_id,
                        document_name=cit.document_name,
                        page_number=cit.page_number,
                        section_heading=cit.section_heading,
                        snippet_preview=cit.snippet_preview,
                        score=cit.score,
                        rank=cit.rank,
                        semantic_score=cit.semantic_score,
                        keyword_score=cit.keyword_score,
                        hybrid_score=cit.hybrid_score,
                        retrieval_method=cit.retrieval_method,
                    )
                )
        return ConversationMessage(
            id=orm.id,
            conversation_id=orm.conversation_id,
            role=orm.role,
            content=orm.content,
            created_at=orm.created_at,
            citations=citations,
        )

    def _message_to_orm(self, domain: ConversationMessage) -> ConversationMessageORM:
        """Translates domain message to ORM."""
        return ConversationMessageORM(
            id=domain.id,
            conversation_id=domain.conversation_id,
            role=domain.role,
            content=domain.content,
            created_at=domain.created_at,
        )

    async def get(
        self, conversation_id: UUID, workspace_id: UUID | None = None
    ) -> Conversation | None:
        """
        Retrieve a conversation session by its ID, scoped optionally to workspace.
        """
        query = select(ConversationORM).where(
            ConversationORM.id == conversation_id,
            ConversationORM.deleted_at.is_(None),
        )
        if workspace_id:
            query = query.where(ConversationORM.workspace_id == workspace_id)
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def save(self, conversation: Conversation) -> Conversation:
        """
        Persist a Conversation domain entity.
        """
        existing_orm = await self.session.get(ConversationORM, conversation.id)
        orm = self._to_orm(conversation)

        if existing_orm:
            existing_orm.title = orm.title
            existing_orm.summary = orm.summary
            existing_orm.updated_at = orm.updated_at
            await self.session.flush()
            return self._to_domain(existing_orm)
        else:
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)

    async def list_by_workspace(
        self, workspace_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        """
        List conversations under a workspace ordered by updated_at descending.
        """
        query = (
            select(ConversationORM)
            .where(
                ConversationORM.workspace_id == workspace_id,
                ConversationORM.deleted_at.is_(None),
            )
            .order_by(ConversationORM.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]

    async def delete(
        self, conversation_id: UUID, workspace_id: UUID | None = None
    ) -> None:
        """
        Delete/soft-delete a conversation.
        """
        query = select(ConversationORM).where(ConversationORM.id == conversation_id)
        if workspace_id:
            query = query.where(ConversationORM.workspace_id == workspace_id)
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        if orm:
            await self._delete(orm)
            await self.session.flush()

    async def get_messages(self, conversation_id: UUID) -> list[ConversationMessage]:
        """
        Retrieve all messages for a session, loading citations in chronological order.
        """
        query = (
            select(ConversationMessageORM)
            .where(
                ConversationMessageORM.conversation_id == conversation_id,
                ConversationMessageORM.deleted_at.is_(None),
            )
            .options(selectinload(ConversationMessageORM.citations))
            .order_by(ConversationMessageORM.created_at.asc())
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._message_to_domain(orm) for orm in orms]

    async def save_message(self, message: ConversationMessage) -> ConversationMessage:
        """
        Persists a ConversationMessage domain entity.
        """
        existing_orm = await self.session.get(ConversationMessageORM, message.id)
        orm = self._message_to_orm(message)

        if existing_orm:
            existing_orm.content = orm.content
            await self.session.flush()
            # Fetch to load citations relationship properly
            query = (
                select(ConversationMessageORM)
                .where(ConversationMessageORM.id == message.id)
                .options(selectinload(ConversationMessageORM.citations))
            )
            res = await self.session.execute(query)
            saved_orm = res.scalar_one()
            return self._message_to_domain(saved_orm)
        else:
            self.session.add(orm)
            await self.session.flush()
            return message

    async def soft_delete_messages(self, message_ids: list[UUID]) -> None:
        """
        Soft-delete a list of messages by their identifiers.
        """
        from datetime import datetime

        for mid in message_ids:
            msg_orm = await self.session.get(ConversationMessageORM, mid)
            if msg_orm:
                msg_orm.deleted_at = datetime.utcnow()
        await self.session.flush()

    def _telemetry_to_domain(self, orm: LLMRequestORM) -> LLMRequest:
        """Translates telemetry ORM to domain request."""
        return LLMRequest(
            id=orm.id,
            workspace_id=orm.workspace_id,
            conversation_id=orm.conversation_id,
            model_name=orm.model_name,
            prompt_version=orm.prompt_version,
            embedding_version=orm.embedding_version,
            parser_version=orm.parser_version,
            vector_index_version=orm.vector_index_version,
            input_tokens=orm.input_tokens,
            output_tokens=orm.output_tokens,
            retrieval_latency_ms=orm.retrieval_latency_ms,
            generation_latency_ms=orm.generation_latency_ms,
            total_latency_ms=orm.total_latency_ms,
            confidence_score=orm.confidence_score,
            grounding_score=orm.grounding_score,
            created_at=orm.created_at,
        )

    def _telemetry_to_orm(self, domain: LLMRequest) -> LLMRequestORM:
        """Translates domain request telemetry to ORM."""
        return LLMRequestORM(
            id=domain.id,
            workspace_id=domain.workspace_id,
            conversation_id=domain.conversation_id,
            model_name=domain.model_name,
            prompt_version=domain.prompt_version,
            embedding_version=domain.embedding_version,
            parser_version=domain.parser_version,
            vector_index_version=domain.vector_index_version,
            input_tokens=domain.input_tokens,
            output_tokens=domain.output_tokens,
            retrieval_latency_ms=domain.retrieval_latency_ms,
            generation_latency_ms=domain.generation_latency_ms,
            total_latency_ms=domain.total_latency_ms,
            confidence_score=domain.confidence_score,
            grounding_score=domain.grounding_score,
            created_at=domain.created_at,
        )

    async def save_telemetry(self, telemetry: LLMRequest) -> LLMRequest:
        """
        Persists a telemetry record tracking LLM request execution parameters.
        """
        orm = self._telemetry_to_orm(telemetry)
        self.session.add(orm)
        await self.session.flush()
        return telemetry
