"""Rich-based logging configuration for ai-ffmpeg-cli.

This module provides a comprehensive logging setup using Rich for beautiful console output
and flexible file logging for production environments.
"""

from .config import JsonFormatter
from .config import get_logger
from .config import setup_logging
from .context import LogContext
from .context import bind_context
from .context import clear_context
from .context import get_context
from .context import request_id
from .context import tenant_id
from .context import user_id

__all__ = [
    "setup_logging",
    "get_logger",
    "JsonFormatter",
    "bind_context",
    "clear_context",
    "get_context",
    "LogContext",
    "request_id",
    "user_id",
    "tenant_id",
]

__version__ = "0.2.3"
