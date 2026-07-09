"""
SQLAlchemy repository adapter for Citation.
"""

from uuid import UUID

from sqlalchemy import select

from app.domain.entities.conversation import Citation
from app.domain.interfaces.repositories import CitationRepository
from app.infrastructure.db.models.conversation import CitationORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyCitationRepository(BaseRepository[CitationORM], CitationRepository):
    """
    SQLAlchemy-backed implementation of the CitationRepository interface.
    """

    def _to_domain(self, orm: CitationORM) -> Citation:
        """Translates ORM model to Domain Entity."""
        return Citation(
            id=orm.id,
            message_id=orm.message_id,
            chunk_id=orm.chunk_id,
            document_id=orm.document_id,
            document_name=orm.document_name,
            page_number=orm.page_number,
            section_heading=orm.section_heading,
            snippet_preview=orm.snippet_preview,
            score=orm.score,
            rank=orm.rank,
            semantic_score=orm.semantic_score,
            keyword_score=orm.keyword_score,
            hybrid_score=orm.hybrid_score,
            retrieval_method=orm.retrieval_method,
        )

    def _to_orm(self, domain: Citation) -> CitationORM:
        """Translates Domain Entity to ORM model."""
        return CitationORM(
            id=domain.id,
            message_id=domain.message_id,
            chunk_id=domain.chunk_id,
            document_id=domain.document_id,
            document_name=domain.document_name,
            page_number=domain.page_number,
            section_heading=domain.section_heading,
            snippet_preview=domain.snippet_preview,
            score=domain.score,
            rank=domain.rank,
            semantic_score=domain.semantic_score,
            keyword_score=domain.keyword_score,
            hybrid_score=domain.hybrid_score,
            retrieval_method=domain.retrieval_method,
        )

    async def save_batch(self, citations: list[Citation]) -> None:
        """
        Persist a list of Citation domain entities.
        """
        if not citations:
            return

        for citation in citations:
            orm = self._to_orm(citation)
            self._add(orm)

        await self.session.flush()

    async def list_by_message(self, message_id: UUID) -> list[Citation]:
        """
        Retrieves all citations associated with an assistant message turn.
        """
        query = select(CitationORM).where(
            CitationORM.message_id == message_id,
            CitationORM.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
