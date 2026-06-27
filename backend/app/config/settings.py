"""
Application settings loaded from environment variables.

Uses pydantic-settings for type-safe configuration with
automatic .env file loading. All values can be overridden
via environment variables or a .env file.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root is two levels above this file: backend/app/config/ → backend/
_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Centralised application configuration."""

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ─────────────────────────────────────────────────────────────
    app_name: str = "MediAI Disease Prediction API"
    app_version: str = "2.0.0"
    app_description: str = (
        "Production-ready REST API for AI-powered disease risk assessment. "
        "Provides comprehensive, physician-style medical reports for breast cancer, "
        "diabetes, and heart disease predictions."
    )
    host: str = "127.0.0.1"
    port: int = 5055
    debug: bool = False

    # ── CORS ───────────────────────────────────────────────────────────────
    allowed_origins: list[str] = ["*"]
    allowed_methods: list[str] = ["GET", "POST", "OPTIONS"]
    allowed_headers: list[str] = ["*"]

    # ── Models ─────────────────────────────────────────────────────────────
    model_dir: Path = _BACKEND_ROOT / "models"

    # ── Logging ────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "json"  # "json" | "text"

    # ── API ────────────────────────────────────────────────────────────────
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper

    @field_validator("model_dir", mode="before")
    @classmethod
    def validate_model_dir(cls, v: str | Path) -> Path:
        path = Path(v)
        if not path.is_absolute():
            path = _BACKEND_ROOT / path
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings (singleton)."""
    return Settings()
