"""
Authentication API Routers.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_auth_service, get_current_user
from app.domain.entities.user import User
from app.infrastructure.db.session import get_db_session
from app.infrastructure.security.service import AuthService

router = APIRouter(prefix="/auth")


class UserRegisterRequest(BaseModel):
    """
    Registration request payload.
    """

    email: str = Field(..., description="User unique email address")
    password: str = Field(
        ..., min_length=8, max_length=100, description="Raw login password"
    )
    role: str = Field(
        default="viewer",
        description="Assigned RBAC role (admin/analyst/viewer)",
    )


class UserLoginRequest(BaseModel):
    """
    Login request payload.
    """

    email: str = Field(..., description="User unique email address")
    password: str = Field(..., description="Raw login password")


class TokenRefreshRequest(BaseModel):
    """
    Token refresh request payload.
    """

    refresh_token: str = Field(..., description="Existing refresh token for rotation")


class LogoutRequest(BaseModel):
    """
    Logout request payload.
    """

    refresh_token: str = Field(..., description="Refresh token to revoke")


class UserResponse(BaseModel):
    """
    Sanitized user details response model (hiding password hash).
    """

    id: UUID
    email: str
    role: str
    created_at: datetime


class AuthResponse(BaseModel):
    """
    Standard authentication details response containing access/refresh tokens.
    """

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshResponse(BaseModel):
    """
    Refresh details response mapping access and refresh token rotation.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """
    Registers a new User, configures default workspace, and issues credentials.
    """
    if request.role not in ["admin", "analyst", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role assigned. Allowed roles are: admin, analyst, viewer.",
        )

    try:
        user, _, access, refresh = await auth_service.register_user(
            email=request.email, password=request.password, role=request.role
        )
        # Commit the single transaction
        await session.commit()

        return AuthResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                role=user.role.value,
                created_at=user.created_at,
            ),
            access_token=access,
            refresh_token=refresh,
        )
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except Exception as exc:
        await session.rollback()
        raise exc


@router.post("/login", response_model=AuthResponse)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    """
    Authenticates user credentials and issues new access/refresh tokens.
    """
    try:
        user, access, refresh = await auth_service.authenticate_user(
            email=request.email, password=request.password
        )
        await session.commit()

        return AuthResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                role=user.role.value,
                created_at=user.created_at,
            ),
            access_token=access,
            refresh_token=refresh,
        )
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    except Exception as exc:
        await session.rollback()
        raise exc


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
) -> RefreshResponse:
    """
    Validates the refresh token and rotates it with new access/refresh tokens.
    """
    try:
        access, refresh = await auth_service.refresh_session(
            refresh_token=request.refresh_token
        )
        await session.commit()

        return RefreshResponse(access_token=access, refresh_token=refresh)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    except Exception as exc:
        await session.rollback()
        raise exc


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """
    Revokes the provided refresh token.
    """
    try:
        await auth_service.logout_user(refresh_token=request.refresh_token)
        await session.commit()
        return {"detail": "Successfully logged out."}
    except Exception as exc:
        await session.rollback()
        raise exc


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Retrieves information about the currently authenticated user.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        created_at=current_user.created_at,
    )
