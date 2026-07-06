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


# Global settings instance
settings = Settings()
