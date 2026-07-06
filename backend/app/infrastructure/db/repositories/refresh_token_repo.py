"""
SQLAlchemy repository adapter for RefreshToken.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update

from app.infrastructure.db.models.refresh_token import RefreshTokenORM
from app.infrastructure.db.repositories.base_repo import BaseRepository


class SQLAlchemyRefreshTokenRepository(BaseRepository[RefreshTokenORM]):
    """
    SQLAlchemy-backed repository managing active refresh tokens in the database.
    """

    async def create_token(
        self, user_id: UUID, token: str, expires_at: datetime
    ) -> RefreshTokenORM:
        """
        Creates and persists a new refresh token.
        """
        orm = RefreshTokenORM(
            token=token, user_id=user_id, expires_at=expires_at, is_revoked=False
        )
        self._add(orm)
        await self.session.flush()
        return orm

    async def get_active_token(self, token: str) -> RefreshTokenORM | None:
        """
        Retrieves a token only if it exists and has not been marked as revoked.
        """
        query = select(RefreshTokenORM).where(
            RefreshTokenORM.token == token,
            RefreshTokenORM.is_revoked.is_(False),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def revoke_token(self, token: str) -> None:
        """
        Revokes a single refresh token by marking it as revoked.
        """
        query = (
            update(RefreshTokenORM)
            .where(RefreshTokenORM.token == token)
            .values(is_revoked=True)
        )
        await self.session.execute(query)
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """
        Revokes all refresh tokens belonging to a user.
        """
        query = (
            update(RefreshTokenORM)
            .where(
                RefreshTokenORM.user_id == user_id,
                RefreshTokenORM.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        await self.session.execute(query)
        await self.session.flush()
