from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Product Radar"
    APP_ENV: str = "development"

    DATABASE_URL: str = "postgresql+psycopg://radar:radar_dev_password@localhost:5432/ai_product_radar"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    WEB_ORIGIN: str = Field(default="http://localhost:3000")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @cached_property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.WEB_ORIGIN.split(",") if origin.strip()]


settings = Settings()
