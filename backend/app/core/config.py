"""
Pydantic Settings configuration module for EquityIQ.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings containing configuration variables loaded from env.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    ENV: str = Field(default="development", description="Runtime environment")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/equityiq",
        description="PostgreSQL async connection URL",
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    APP_NAME: str = Field(default="EquityIQ API", description="FastAPI app name")
    VERSION: str = Field(default="0.1.0", description="Application semantic version")
    RELEASE_TAG: str = Field(
        default="v0.2.1-repository-cleanup", description="Active Git release tag"
    )
    JWT_SECRET_KEY: str = Field(
        default="supersecretkey_please_change_in_production_9812739182739812739",
        description="Secret key for signing JWTs",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, description="Expiry duration of access tokens"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Expiry duration of refresh tokens"
    )


# Global settings instance
settings = Settings()
