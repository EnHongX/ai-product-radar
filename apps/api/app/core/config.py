from functools import cached_property
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["openai", "anthropic", "google", "ollama", "none"]


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Product Radar"
    APP_ENV: str = "development"

    DATABASE_URL: str = "postgresql+psycopg://radar:radar_dev_password@localhost:5432/ai_product_radar"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    WEB_ORIGIN: str = Field(default="http://localhost:3000")

    LLM_PROVIDER: LLMProvider = Field(default="none", description="LLM provider for extraction. Set to 'none' to disable.")
    LLM_API_KEY: str | None = Field(default=None, description="API key for LLM provider")
    LLM_MODEL: str = Field(default="gpt-4o", description="Model name to use for extraction")
    LLM_BASE_URL: str | None = Field(default=None, description="Base URL for LLM API (for ollama or custom endpoints)")
    LLM_EXTRACTION_PROMPT_VERSION: str = Field(default="v1", description="Prompt version for extraction")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @cached_property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.WEB_ORIGIN.split(",") if origin.strip()]

    @cached_property
    def llm_enabled(self) -> bool:
        return self.LLM_PROVIDER != "none" and self.LLM_API_KEY is not None


settings = Settings()
