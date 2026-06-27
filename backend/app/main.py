"""
MediAI Disease Prediction Platform — FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance.
It should be run with uvicorn:

    uvicorn app.main:app --host 127.0.0.1 --port 5055 --reload

Or using the convenience runner at the bottom of this file:

    python -m app.main
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.routes import health, predict
from app.utils.logging_config import (
    RequestIdMiddleware,
    configure_logging,
    get_logger,
)

# ─────────────────────────────────────────────────────────────────────────────
# Bootstrap logging BEFORE anything else
# ─────────────────────────────────────────────────────────────────────────────

settings = get_settings()
configure_logging(level=settings.log_level, fmt=settings.log_format)
logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan events
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Startup:  Log configuration, pre-warm models (optional).
    Shutdown: Log graceful termination.
    """
    logger.info(
        "Starting %s v%s on %s:%d",
        settings.app_name,
        settings.app_version,
        settings.host,
        settings.port,
    )
    logger.info("Model directory: %s", settings.model_dir)
    logger.info("API documentation: http://%s:%d%s", settings.host, settings.port, settings.docs_url)

    yield  # Application is running

    logger.info("Shutting down %s — goodbye.", settings.app_name)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Application
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Predictions",
            "description": (
                "Disease risk prediction endpoints. Each endpoint accepts validated "
                "medical parameters and returns a comprehensive 10-section MedicalReport "
                "written in a specialist physician's consultation style."
            ),
        },
        {
            "name": "Health",
            "description": "API health and readiness probes.",
        },
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────────────────────

# 1. Request ID tagging (must be registered before CORS)
app.add_middleware(RequestIdMiddleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)


# ─────────────────────────────────────────────────────────────────────────────
# Request timing middleware (lightweight inline version)
# ─────────────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    logger.debug(
        "%s %s → %d  (%.2f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ─────────────────────────────────────────────────────────────────────────────
# Global exception handler
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────

# Health check — root level
app.include_router(health.router)

# Prediction endpoints — versioned prefix
app.include_router(predict.router, prefix=settings.api_v1_prefix)


# ─────────────────────────────────────────────────────────────────────────────
# Root endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/",
    tags=["Health"],
    summary="API Root",
    description="Returns basic API information and documentation links.",
)
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "documentation": f"http://{settings.host}:{settings.port}{settings.docs_url}",
        "health": f"http://{settings.host}:{settings.port}/health",
        "endpoints": {
            "breast_cancer": f"{settings.api_v1_prefix}/predict/breast-cancer",
            "diabetes": f"{settings.api_v1_prefix}/predict/diabetes",
            "heart_disease": f"{settings.api_v1_prefix}/predict/heart-disease",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Direct execution
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
