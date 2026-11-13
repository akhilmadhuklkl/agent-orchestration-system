from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./orchestrator.db"
    redis_url: str = "redis://localhost:6379/0"
    app_env: str = "development"
    queue_mode: str = "sync"
    api_key: str = ""
    model_mode: str = "deterministic"
    openai_api_key: str = ""
    model_name: str = "gpt-4.1-mini"
    workspace_id: str = "default"
    user_id: str = "local-user"
    user_role: str = "admin"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
