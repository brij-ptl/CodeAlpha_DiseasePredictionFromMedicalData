"""
Thread-safe, lazy model registry.

Models and scalers are loaded from disk on first access and cached
in memory for the lifetime of the application process. A threading
lock ensures that concurrent first-time requests do not trigger
multiple simultaneous disk reads.

Disease keys follow the URL slug convention (e.g. "breast-cancer").
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import joblib

from app.config.settings import get_settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class ModelNotFoundError(RuntimeError):
    """Raised when the requested model file does not exist on disk."""


class ModelLoadError(RuntimeError):
    """Raised when a model file exists but cannot be deserialised."""


# ─────────────────────────────────────────────────────────────────────────────
# Disease → File slug mapping
# ─────────────────────────────────────────────────────────────────────────────

#: Maps URL-slug disease keys to the filename stem used when saving .pkl files.
#: Add a new entry here to register a new disease — no other code changes needed.
DISEASE_FILE_MAP: dict[str, str] = {
    "breast-cancer": "breast_cancer",
    "diabetes": "diabetes",
    "heart-disease": "heart_disease",
}


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

class ModelRegistry:
    """
    Singleton registry that lazily loads and caches ML models.

    Usage::

        registry = ModelRegistry()
        model, scaler = registry.get("breast-cancer")
    """

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}
        self._scalers: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._settings = get_settings()

    # ── Public API ──────────────────────────────────────────────────────────

    def get(self, disease_key: str) -> tuple[Any, Any]:
        """
        Return the (model, scaler) pair for the given disease key.

        Loads from disk if not already cached. Thread-safe.

        Args:
            disease_key: URL slug such as "breast-cancer".

        Returns:
            Tuple of (fitted sklearn estimator, fitted StandardScaler).

        Raises:
            ModelNotFoundError: If the .pkl files do not exist.
            ModelLoadError:     If joblib.load fails.
        """
        if disease_key not in self._models:
            self._load(disease_key)
        return self._models[disease_key], self._scalers[disease_key]

    def loaded_keys(self) -> list[str]:
        """Return list of disease keys currently loaded in memory."""
        return list(self._models.keys())

    def is_available(self, disease_key: str) -> bool:
        """Check whether model files exist on disk (without loading them)."""
        stem = DISEASE_FILE_MAP.get(disease_key)
        if not stem:
            return False
        model_dir = self._settings.model_dir
        return (
            (model_dir / f"{stem}_model.pkl").exists()
            and (model_dir / f"{stem}_scaler.pkl").exists()
        )

    # ── Private helpers ─────────────────────────────────────────────────────

    def _load(self, disease_key: str) -> None:
        """Load model + scaler from disk under a lock (double-checked)."""
        with self._lock:
            # Double-check inside the lock in case another thread already loaded
            if disease_key in self._models:
                return

            stem = DISEASE_FILE_MAP.get(disease_key)
            if stem is None:
                raise ModelNotFoundError(
                    f"Unknown disease key '{disease_key}'. "
                    f"Registered keys: {list(DISEASE_FILE_MAP.keys())}"
                )

            model_dir: Path = self._settings.model_dir
            model_path = model_dir / f"{stem}_model.pkl"
            scaler_path = model_dir / f"{stem}_scaler.pkl"

            if not model_path.exists() or not scaler_path.exists():
                raise ModelNotFoundError(
                    f"Model files for '{disease_key}' not found in {model_dir}. "
                    "Please run train_models.py first."
                )

            logger.info("Loading model for '%s' from %s", disease_key, model_dir)
            try:
                self._models[disease_key] = joblib.load(model_path)
                self._scalers[disease_key] = joblib.load(scaler_path)
                logger.info("Successfully loaded model for '%s'.", disease_key)
            except Exception as exc:
                raise ModelLoadError(
                    f"Failed to deserialise model for '{disease_key}': {exc}"
                ) from exc


# Module-level singleton — imported by services
model_registry = ModelRegistry()
