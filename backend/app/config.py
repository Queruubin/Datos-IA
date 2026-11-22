from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration read from environment variables or a `.env` file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    data_dir: Path = Path("data")
    duckdb_path: Path = Path("data/san_cristobal.duckdb")
    ckan_api_url: str = "https://datosabiertos.bogota.gov.co/api/3/action"
    http_timeout_seconds: float = 300
    # Agent (Gemini). Without a key, POST /api/chat answers 503 and the rest of the API works.
    gemini_api_key: SecretStr | None = None
    # Model names verified against the models available to a new AI Studio key (2026-11-22).
    # Flash-Lite first: it answers in ~1 s, while gemini-3.8-flash was saturated (503/504) in tests.
    gemini_model: str = "gemini-3.5-flash-lite"
    # Tried in order when the current model is overloaded, rate-limited or times out.
    gemini_fallback_models: list[str] = ["gemini-3.1-flash-lite", "gemini-3.8-flash"]
    gemini_timeout_seconds: float = 30
    gemini_temperature: float = 0.2
    # Separate DuckDB file so the API never needs write access to the analytics database.
    gap_log_path: Path = Path("data/gap_log.duckdb")
    chat_rate_limit_per_minute: int = 20
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def raw_cache_dir(self) -> Path:
        return self.data_dir / "raw"


@lru_cache
def get_settings() -> Settings:
    return Settings()
