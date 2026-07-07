"""
AuthService managing authentication, registration, logout, and session rotation.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.entities.user import User, UserRole
from app.domain.entities.workspace import Workspace, WorkspaceMembership
from app.domain.interfaces.repositories import UserRepository, WorkspaceRepository
from app.domain.interfaces.security import PasswordHasher
from app.infrastructure.db.repositories.refresh_token_repo import (
    SQLAlchemyRefreshTokenRepository,
)
from app.infrastructure.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


class AuthService:
    """
    Orchestrator for identity, access controls, and session validation.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        workspace_repo: WorkspaceRepository,
        refresh_token_repo: SQLAlchemyRefreshTokenRepository,
        hasher: PasswordHasher,
    ) -> None:
        self.user_repo = user_repo
        self.workspace_repo = workspace_repo
        self.refresh_token_repo = refresh_token_repo
        self.hasher = hasher

    async def register_user(
        self, email: str, password: str, role: str
    ) -> tuple[User, Workspace, str, str]:
        """
        Registers a new user and configures workspace defaults in a single transaction.

        Args:
            email: Account email.
            password: Raw plain-text password.
            role: Assignment role (admin/analyst/viewer).

        Returns:
            Tuple: (User, Workspace, access_token, refresh_token).
        """
        # 1. Enforce uniqueness checks
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("Email is already registered.")

        user_id = uuid4()
        hashed = self.hasher.hash_password(password)

        # 2. Build User entity
        user = User(
            id=user_id,
            email=email,
            hashed_password=hashed,
            oauth_provider=None,
            role=UserRole(role),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        saved_user = await self.user_repo.save(user)

        # 3. Create default Workspace
        workspace_id = uuid4()
        user_name_prefix = email.split("@")[0]
        workspace = Workspace(
            id=workspace_id,
            name=f"{user_name_prefix.capitalize()}'s Workspace",
            owner_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        saved_workspace = await self.workspace_repo.save(workspace)

        # 4. Associate user as owner (Owner membership)
        membership = WorkspaceMembership(
            id=uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            role="owner",  # Default owner membership
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await self.workspace_repo.save_membership(membership)

        # 5. Generate session tokens
        access_token, _ = create_access_token(user_id, user.role.value)
        refresh_token, expires_at = create_refresh_token(user_id)

        # 6. Persist session token state
        await self.refresh_token_repo.create_token(user_id, refresh_token, expires_at)

        return saved_user, saved_workspace, access_token, refresh_token

    async def authenticate_user(
        self, email: str, password: str
    ) -> tuple[User, str, str]:
        """
        Validates login credentials and returns session tokens.
        """
        user = await self.user_repo.get_by_email(email)
        if not user or not user.hashed_password:
            raise ValueError("Invalid email or password.")

        if not self.hasher.verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password.")

        access_token, _ = create_access_token(user.id, user.role.value)
        refresh_token, expires_at = create_refresh_token(user.id)

        # Persist refresh token
        await self.refresh_token_repo.create_token(user.id, refresh_token, expires_at)

        return user, access_token, refresh_token

    async def refresh_session(self, refresh_token: str) -> tuple[str, str]:
        """
        Verifies the refresh token and rotates it with new access/refresh tokens.
        """
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token.")

        user_id = UUID(payload["sub"])

        # Validate token against active records in database
        token_record = await self.refresh_token_repo.get_active_token(refresh_token)
        if not token_record:
            raise ValueError("Refresh token is invalid or has been revoked.")

        # Check expiration
        token_expires = token_record.expires_at
        if token_expires.tzinfo is None:
            token_expires = token_expires.replace(tzinfo=UTC)

        if datetime.now(UTC) > token_expires:
            # Revoke expired token
            await self.refresh_token_repo.revoke_token(refresh_token)
            raise ValueError("Refresh token has expired.")

        # Revoke used token (enforce one-time use rotation)
        await self.refresh_token_repo.revoke_token(refresh_token)

        # Verify user still exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        # Generate new rotated tokens
        new_access_token, _ = create_access_token(user_id, user.role.value)
        new_refresh_token, new_expires_at = create_refresh_token(user_id)

        # Persist new token
        await self.refresh_token_repo.create_token(
            user_id, new_refresh_token, new_expires_at
        )

        return new_access_token, new_refresh_token

    async def logout_user(self, refresh_token: str) -> None:
        """
        Revokes a refresh token session.
        """
        await self.refresh_token_repo.revoke_token(refresh_token)
