"""Application configuration using Pydantic settings."""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    ASYNC_DATABASE_URL: str = Field(..., description="Async PostgreSQL connection string (asyncpg)")

    # JWT Configuration
    JWT_ALGORITHM: str = Field(default="RS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiry")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry")
    PRIVATE_KEY_PATH: str = Field(
        default="keys/private_key.pem", description="Path to RSA private key"
    )
    PUBLIC_KEY_PATH: str = Field(
        default="keys/public_key.pem", description="Path to RSA public key"
    )
    # RSA key contents (takes precedence over file paths — use for serverless/Vercel)
    PRIVATE_KEY_CONTENT: Optional[str] = Field(default=None, description="RSA private key PEM content")
    PUBLIC_KEY_CONTENT: Optional[str] = Field(default=None, description="RSA public key PEM content")

    # Email Configuration
    SMTP_HOST: str = Field(default="localhost", description="SMTP server host")
    SMTP_PORT: int = Field(default=1025, description="SMTP server port")
    SMTP_USER: str = Field(default="", description="SMTP username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password")
    SMTP_FROM_EMAIL: str = Field(
        default="noreply@learnpybyai.local", description="From email address"
    )
    SMTP_FROM_NAME: str = Field(default="LearnPyByAI", description="From name")

    # Frontend URL
    FRONTEND_URL: str = Field(
        default="http://localhost:3000", description="Frontend URL for email links"
    )

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_MAX_ATTEMPTS: int = Field(default=5, description="Max failed login attempts")
    RATE_LIMIT_LOCKOUT_MINUTES: int = Field(default=15, description="Lockout duration in minutes")

    # HaveIBeenPwned API
    HIBP_API_URL: str = Field(
        default="https://api.pwnedpasswords.com/range/",
        description="HaveIBeenPwned API URL",
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # LLM Provider
    LLM_MODEL: str = Field(default="openrouter/qwen-3.6", description="LiteLLM model identifier")
    LLM_API_KEY: str = Field(default="", description="API key for the configured LLM provider")
    LLM_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        description="Base URL for the LLM provider",
    )
    LLM_MAX_INPUT_TOKENS: int = Field(
        default=1200, description="Maximum input tokens before rejection"
    )
    LLM_MAX_OUTPUT_TOKENS: int = Field(
        default=600, description="Maximum output tokens per response"
    )
    LLM_TIMEOUT_SECONDS: int = Field(default=30, description="Timeout for LLM requests in seconds")
    LLM_TEMPERATURE: float = Field(default=0.7, description="Default temperature for completions")
    LLM_CACHE_TTL_DAYS: int = Field(default=30, description="Cache entry TTL in days")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Comma-separated list of allowed CORS origins",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> List[str]:
        """Parse comma-separated string or list into a list of origins."""
        if isinstance(v, list):
            return [o.strip() for o in v if o.strip()]
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return list(v)

    def get_private_key(self) -> str:
        """Load RSA private key from env content or file."""
        if self.PRIVATE_KEY_CONTENT:
            return self.PRIVATE_KEY_CONTENT.replace("\\n", "\n")
        key_path = Path(self.PRIVATE_KEY_PATH)
        if not key_path.exists():
            raise FileNotFoundError(f"Private key not found at {key_path}")
        return key_path.read_text()

    def get_public_key(self) -> str:
        """Load RSA public key from env content or file."""
        if self.PUBLIC_KEY_CONTENT:
            return self.PUBLIC_KEY_CONTENT.replace("\\n", "\n")
        key_path = Path(self.PUBLIC_KEY_PATH)
        if not key_path.exists():
            raise FileNotFoundError(f"Public key not found at {key_path}")
        return key_path.read_text()


# Global settings instance
settings = Settings()
