"""
Application configuration management using Pydantic Settings.
"""

from functools import lru_cache
from typing import List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    APP_NAME: str = "Memoist"
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")

    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    # Database settings
    MONGODB_DATABASE: str = Field(default="memoist", env="MONGODB_DATABASE")
    MONGODB_USER: str = Field(..., env="MONGODB_USER")
    MONGODB_PASSWORD: str = Field(..., env="MONGODB_PASSWORD")
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    SQL_ECHO: bool = Field(default=False, env="SQL_ECHO")

    # MinIO settings
    MINIO_ENDPOINT: str = Field(..., env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(..., env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(..., env="MINIO_SECRET_KEY")
    MINIO_SECURE: bool = Field(default=False, env="MINIO_SECURE")
    MINIO_BUCKET_AUDIO: str = Field(default="audio", env="MINIO_BUCKET_AUDIO")
    MINIO_BUCKET_IMAGES: str = Field(default="images", env="MINIO_BUCKET_IMAGES")

    # Gemini AI settings
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")
    GEMINI_MAX_TOKENS: int = Field(default=8192, env="GEMINI_MAX_TOKENS")

    # Processing settings
    MAX_CONCURRENT_PROCESSES: int = Field(default=4, env="MAX_CONCURRENT_PROCESSES")
    PROCESS_TIMEOUT: int = Field(default=300, env="PROCESS_TIMEOUT")  # 5 minutes
    RETRY_ATTEMPTS: int = Field(default=3, env="RETRY_ATTEMPTS")
    RETRY_DELAY: int = Field(default=1, env="RETRY_DELAY")

    # Cache settings
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    CACHE_MAX_SIZE: int = Field(default=1000, env="CACHE_MAX_SIZE")
    CACHE_PREFIX: str = Field(default="memoist", env="CACHE_PREFIX")

    # Security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")

    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    @validator("DEBUG", pre=True)
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    @validator("MINIO_SECURE", pre=True)
    def parse_minio_secure(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    @validator("SQL_ECHO", pre=True)
    def parse_sql_echo(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
