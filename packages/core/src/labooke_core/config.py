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
    embed_model: str = Field(default="intfloat/multilingual-e5-small")
    embed_cache_model: bool = Field(default=True)
    embed_worker_idle_seconds: float = Field(default=60.0, ge=1.0)
    chunk_pages: int = Field(default=1, ge=1)

    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_reload: bool = Field(default=True)
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

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
