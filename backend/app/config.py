from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"

    database_url: str = ""
    asr_api_key: str = ""
    asr_api_base: str = "https://api.siliconflow.cn/v1/audio/transcriptions"
    asr_model: str = "TeleAI/TeleSpeechASR"

    postgres_user: str = "solocrm"
    postgres_password: str = "solocrm"
    postgres_db: str = "solocrm"
    postgres_host: str = "db"
    postgres_port: int = 5432

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-me"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    openclaw_enabled: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
