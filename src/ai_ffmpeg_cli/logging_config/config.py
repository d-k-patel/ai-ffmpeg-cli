"""Rich-based logging configuration for ai-ffmpeg-cli."""

import json
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
from rich.traceback import install as install_rich_traceback

from .context import get_context

# Create a custom theme for better visual consistency
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "critical": "red bold",
        "debug": "dim",
        "success": "green",
        "progress": "blue",
    }
)

# Initialize console with custom theme
console = Console(theme=custom_theme)


def setup_logging(
    level: str | int | None = None,
    json_output: bool = False,
    log_file: str | Path | None = None,
    show_locals: bool = True,
    console_instance: Console | None = None,
) -> None:
    """Setup Rich-based logging configuration.

    Args:
        level: Logging level (default: INFO, or LOG_LEVEL env var)
        json_output: Use JSON format for file logs (default: False)
        log_file: Path to log file (default: None)
        show_locals: Show local variables in tracebacks (default: True)
        console_instance: Rich console instance (default: creates new one)

    This function is idempotent - calling it multiple times won't duplicate handlers.
    """
    # Get log level from env var or use default
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # Install Rich traceback handler
    install_rich_traceback(show_locals=show_locals)

    # Use provided console or create new one
    rich_console = console_instance or console

    # Get root logger
    root_logger = logging.getLogger()

    # Clear existing handlers to ensure idempotency
    root_logger.handlers.clear()

    # Create Rich console handler with enhanced formatting
    rich_handler = RichHandler(
        console=rich_console,
        show_time=True,
        show_path=False,  # Don't show file paths and line numbers
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=show_locals,
        show_level=True,
        level=level,
        log_time_format="[%X]",
    )
    rich_handler.setLevel(level)

    # Set root logger level
    root_logger.setLevel(level)

    # Create formatter for Rich handler
    rich_formatter = logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]",
    )
    rich_handler.setFormatter(rich_formatter)

    # Add Rich handler to root logger
    root_logger.addHandler(rich_handler)

    # Setup file logging if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if json_output:
            # JSON file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(JsonFormatter())
        else:
            # Plain text file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )

        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)

    # Capture warnings in logs
    logging.captureWarnings(True)

    # Silence noisy libraries
    _silence_noisy_libraries()

    # Log setup completion with enhanced formatting
    logger = logging.getLogger(__name__)
    logger.info(
        "ai-ffmpeg-cli logging initialized",
        extra={
            "level": logging.getLevelName(level),
            "log_file": str(log_file) if log_file else "console only",
            "rich_tracebacks": True,
            "show_locals": show_locals,
        },
    )


def _silence_noisy_libraries() -> None:
    """Silence noisy third-party libraries to WARNING level."""
    noisy_libraries = [
        "urllib3",
        "botocore",
        "boto3",
        "requests",
        "httpx",
        "aiohttp",
        "asyncio",
        "charset_normalizer",
        "certifi",
    ]

    for lib in noisy_libraries:
        logging.getLogger(lib).setLevel(logging.WARNING)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Get context data
        context_data = get_context()

        # Prepare log entry
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context data if available
        if context_data:
            log_entry["context"] = context_data

        # Add exception info if present
        if record.exc_info and record.exc_info != (None, None, None):
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in log_entry and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_startup_info() -> None:
    """Log startup information with Rich formatting."""
    logger = get_logger(__name__)

    # Log system information
    logger.info(
        "Starting ai-ffmpeg-cli",
        extra={
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "working_directory": str(Path.cwd()),
        },
    )

    # Log configuration status
    api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
    logger.info(
        "Configuration status",
        extra={
            "api_key_configured": api_key_configured,
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "model": os.getenv("AICLIP_MODEL", "gpt-5"),
        },
    )


def log_operation_start(operation: str, **kwargs: Any) -> None:
    """Log the start of an operation with Rich formatting.

    Args:
        operation: Name of the operation
        **kwargs: Additional context information
    """
    logger = get_logger(__name__)
    logger.info(f"Starting operation: {operation}", extra=kwargs)


def log_operation_success(operation: str, **kwargs: Any) -> None:
    """Log successful completion of an operation with Rich formatting.

    Args:
        operation: Name of the operation
        **kwargs: Additional context information
    """
    logger = get_logger(__name__)
    logger.info(f"Operation completed: {operation}", extra=kwargs)


def log_operation_error(operation: str, error: Exception, **kwargs: Any) -> None:
    """Log an operation error with Rich formatting.

    Args:
        operation: Name of the operation
        error: The error that occurred
        **kwargs: Additional context information
    """
    logger = get_logger(__name__)
    logger.error(
        f"Operation failed: {operation}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs,
        },
        exc_info=True,
    )
