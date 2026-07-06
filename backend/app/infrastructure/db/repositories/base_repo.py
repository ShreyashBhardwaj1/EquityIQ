"""
BaseRepository class providing generic CRUD operations.
"""

from typing import TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository[ModelType: Base]:
    """
    Abstract base repository that concrete repository adapters inherit from.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initializes the repository with an active AsyncSession.

        Args:
            session: SQLAlchemy AsyncSession.
        """
        self.session = session

    async def _get(self, model_class: type[ModelType], id_: UUID) -> ModelType | None:
        """
        Helper method to retrieve an ORM model instance by its primary key ID.

        Args:
            model_class: The ORM class to query.
            id_: The UUID primary key value.

        Returns:
            The ORM instance if found, otherwise None.
        """
        return await self.session.get(model_class, id_)

    def _add(self, instance: ModelType) -> None:
        """
        Helper method to add an ORM model instance to the session.

        Args:
            instance: The ORM instance to stage.
        """
        self.session.add(instance)

    async def _delete(self, instance: ModelType) -> None:
        """
        Helper method to delete an ORM model instance from the database.

        Args:
            instance: The ORM instance to delete.
        """
        await self.session.delete(instance)
