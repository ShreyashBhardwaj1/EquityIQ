"""
SQLAlchemy repository adapter for User.
"""

from uuid import UUID

from sqlalchemy import select

from app.domain.entities.user import User, UserRole
from app.domain.interfaces.repositories import UserRepository
from app.infrastructure.db.models.user import UserORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyUserRepository(BaseRepository[UserORM], UserRepository):
    """
    SQLAlchemy-backed implementation of the UserRepository interface.
    """

    def _to_domain(self, orm: UserORM) -> User:
        """Translates ORM model to Domain Entity."""
        return User(
            id=orm.id,
            email=orm.email,
            hashed_password=orm.hashed_password,
            oauth_provider=orm.oauth_provider,
            role=UserRole(orm.role),
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _to_orm(self, domain: User) -> UserORM:
        """Translates Domain Entity to ORM model."""
        return UserORM(
            id=domain.id,
            email=domain.email,
            hashed_password=domain.hashed_password,
            oauth_provider=domain.oauth_provider,
            role=domain.role.value,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Retrieves a user by their UUID primary key.
        """
        orm = await self._get(UserORM, user_id)
        return self._to_domain(orm) if orm else None

    async def get_by_email(self, email: str) -> User | None:
        """
        Retrieves a user by their unique email address.
        """
        query = select(UserORM).where(UserORM.email == email.lower().strip())
        result = await self.session.execute(query)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def save(self, user: User) -> User:
        """
        Persists a User domain entity and flushes the session.
        """
        existing_orm = await self.session.get(UserORM, user.id)
        orm = self._to_orm(user)

        if existing_orm:
            existing_orm.email = orm.email
            existing_orm.hashed_password = orm.hashed_password
            existing_orm.oauth_provider = orm.oauth_provider
            existing_orm.role = orm.role
            existing_orm.updated_at = orm.updated_at
            await self.session.flush()
            return self._to_domain(existing_orm)
        else:
            self._add(orm)
            await self.session.flush()
            return self._to_domain(orm)
