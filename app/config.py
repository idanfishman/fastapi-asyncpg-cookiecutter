"""
Provides global settings for the application.

The config is loading the values for each parameter from the environment
(Environment Variables Values) using pydantic's `BaseSettings`.
"""

from typing import Any

from pydantic import BaseSettings, PostgresDsn, validator


class Settings(BaseSettings):
    # CORS Middleware
    CORS_ORIGINS: list[str]
    CORS_CREDENTIALS: bool
    CORS_METHODS: list[str]
    CORS_HEADERS: list[str]

    # PostgreSQL Database Connection
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URL: PostgresDsn | None

    @validator("SQLALCHEMY_DATABASE_URL", pre=True)
    def assemble_db_connection_string(
        cls, v: PostgresDsn | None, values: dict[str, Any]
    ) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB')}",
        )

    # Pagination
    PAGE_SIZE: int = 1000

    class Config:
        case_sensitive = True


settings = Settings()
