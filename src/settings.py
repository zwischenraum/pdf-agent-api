from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # API Configuration
    api_base: str = Field(default="http://localhost:11434", description="Base URL for the API")
    api_key: str | None = Field(default=None, description="API key for authentication")
    model_id: str = Field(default="google/gemma-3-27b-it", description="Model ID for the API")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Host to bind the server to")
    port: int = Field(default=8000, description="Port to bind the server to")

    # Environment
    environment: str = Field(
        default="development", description="Environment (development, staging, production)"
    )
    debug: bool = Field(default=True, description="Enable debug mode")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")


# Create a global instance
settings = Settings()
