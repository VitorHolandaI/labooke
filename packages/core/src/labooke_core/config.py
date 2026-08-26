"""Runtime configuration loaded from environment variables.

All hosts, ports, paths, and model identifiers come from `LABOOKE_*`
env vars (or a `.env` file at the project root).
"""

from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Project-wide settings.

    Example:
        >>> s = Settings()
        >>> s.chunk_pages
        1
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="LABOOKE_", extra="ignore")

    data_dir: Path = Field(default=Path("./data"))
    import_dir: Path = Field(default=Path("./data/inbox"))
    embed_base_url: str = Field(default="")
    embed_model: str = Field(default="bge-m3")
    embed_timeout_seconds: float = Field(default=120.0, gt=0)
    chunk_pages: int = Field(default=1, ge=1)

    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_reload: bool = Field(default=True)
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    llm_base_url: str = Field(default="")
    llm_model: str = Field(default="")
    llm_api_key: str = Field(default="")
    llm_summary_pages: int = Field(default=10, ge=1)
    llm_rag_k: int = Field(default=10, ge=1)
    llm_auto_summarize: bool = Field(default=False)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, raw: object) -> object:
        """Accept comma-separated env strings; empty value yields an empty list."""
        if isinstance(raw, str):
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        return raw

    @property
    def books_dir(self) -> Path:
        """Return the directory where uploaded book files are stored."""
        return self.data_dir / "books"

    @property
    def covers_dir(self) -> Path:
        """Return the directory where generated cover thumbnails live."""
        return self.data_dir / "covers"

    @property
    def db_path(self) -> Path:
        """Return the path of the SQLite database file."""
        return self.data_dir / "labooke.db"

    @property
    def llm_enabled(self) -> bool:
        """Return True when the LLM endpoint and model are configured."""
        return bool(self.llm_base_url) and bool(self.llm_model)

    @property
    def embed_enabled(self) -> bool:
        """Return True when the Ollama embedding endpoint is configured."""
        return bool(self.embed_base_url) and bool(self.embed_model)
