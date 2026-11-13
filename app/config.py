from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./orchestrator.db"
    redis_url: str = "redis://localhost:6379/0"
    app_env: str = "development"
    queue_mode: str = "sync"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
