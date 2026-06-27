"""
Structured logging configuration.

Provides JSON-formatted logging for production and
human-readable text logging for development. Every
HTTP request is tagged with a unique request ID.
"""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Context variable so request ID flows through async tasks
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class _JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        import traceback

        payload: dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(""),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class _TextFormatter(logging.Formatter):
    """Colourised text formatter for development."""

    _COLOURS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        colour = self._COLOURS.get(record.levelname, "")
        rid = request_id_ctx.get("")
        rid_part = f" [{rid[:8]}]" if rid else ""
        prefix = f"{colour}{record.levelname:<8}{self._RESET}"
        return (
            f"{self.formatTime(record, '%H:%M:%S')}{rid_part} "
            f"{prefix} {record.name} — {record.getMessage()}"
        )


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    """
    Configure the root logger.

    Args:
        level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
        fmt:   "json" for structured output, "text" for human-readable.
    """
    formatter: logging.Formatter
    if fmt.lower() == "json":
        formatter = _JSONFormatter()
    else:
        formatter = _TextFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    # Quieten noisy libraries
    for noisy in ("uvicorn.access", "httpx", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Attach a UUID request ID to every incoming request.

    The ID is stored in a ContextVar so it flows through
    async code and appears in all log records.
    It is also returned as an X-Request-ID response header.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_ctx.reset(token)
