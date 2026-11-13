"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "HireAgent"
    version: str = "0.1.0"

    database_path: Path = BASE_DIR / "data" / "hire_agent.db"
    jobs_dir: Path = BASE_DIR / "data" / "jobs"

    # Any OpenAI-compatible endpoint works: OpenAI, DeepSeek, Qwen, Moonshot...
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout: float = 40.0

    recommend_threshold: float = 8.0
    hold_threshold: float = 6.0

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
