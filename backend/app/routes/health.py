"""
Health check route.

Provides a liveness/readiness endpoint consumed by:
  - Docker health checks
  - Cloud platform load balancers
  - Monitoring systems (e.g. Prometheus, Datadog)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.registry import DISEASE_FILE_MAP, model_registry
from app.schemas.responses import HealthResponse
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])

# Module-level start time for uptime calculation
_START_TIME = time.monotonic()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API Health Check",
    description=(
        "Returns the current health status of the API, including "
        "uptime, loaded models, and application version."
    ),
)
def health_check() -> HealthResponse:
    """
    Liveness and readiness probe.

    Returns:
      - ``healthy``: All model files are found on disk.
      - ``degraded``: One or more model files are missing.
    """
    uptime = time.monotonic() - _START_TIME
    loaded = model_registry.loaded_keys()

    # Check availability of all registered disease model files
    all_available = all(
        model_registry.is_available(key) for key in DISEASE_FILE_MAP
    )
    status = "healthy" if all_available else "degraded"

    if status == "degraded":
        logger.warning("Health check: degraded — some model files are missing.")

    from app.config.settings import get_settings
    settings = get_settings()

    return HealthResponse(
        status=status,
        version=settings.app_version,
        uptime_seconds=round(uptime, 2),
        loaded_models=loaded,
        timestamp=datetime.now(timezone.utc),
    )
