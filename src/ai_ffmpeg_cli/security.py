"""Security utilities for handling sensitive data and credentials."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from pydantic_core.core_schema import AfterValidatorFunctionSchema

logger = logging.getLogger(__name__)


def mask_api_key(api_key: str | None) -> str:
    """Mask API key for safe display in logs and errors.

    Args:
        api_key: The API key to mask

    Returns:
        str: Masked version safe for logging
    """
    if not api_key or not isinstance(api_key, str):
        return "***NO_KEY***"

    if len(api_key) <= 8:
        return "***SHORT_KEY***"

    # Show first 3 and last 3 characters, mask the rest
    return f"{api_key[:3]}***{api_key[-3:]}"


def validate_api_key_format(api_key: str | None) -> bool:
    """Validate API key has expected format without logging the key.

    Args:
        api_key: The API key to validate

    Returns:
        bool: True if format is valid
    """
    if not api_key or not isinstance(api_key, str):
        return False

    # OpenAI API keys start with 'sk-' and have specific length/format
    if api_key.startswith("sk-"):
        # Remove prefix and check remaining characters
        key_body = api_key[3:]
        if len(key_body) >= 32 and re.match(r"^[a-zA-Z0-9]+$", key_body):
            return True

    return False


def sanitize_error_message(message: str) -> str:
    """Remove sensitive information from error messages.

    Args:
        message: Original error message

    Returns:
        str: Sanitized error message
    """
    if not message:
        return ""

    # Patterns to mask
    patterns = [
        # API keys
        (r"sk-[a-zA-Z0-9]{10,}", "***API_KEY***"),
        (r"OPENAI_API_KEY[=\s:]+[^\s]+", "OPENAI_API_KEY=***MASKED***"),
        # File paths that might contain sensitive info
        (r"/Users/[^/\s]+", "/Users/***USER***"),
        (r"C:\\\\Users\\\\[^\\\\s]+", r"C:\\Users\\***USER***"),
        # Potential passwords or tokens
        (r"password[=\s:]+[^\s]+", "password=***MASKED***"),
        (r"token[=\s:]+[^\s]+", "token=***MASKED***"),
        (r"secret[=\s:]+[^\s]+", "secret=***MASKED***"),
    ]

    sanitized = message
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized


class SecureLogger:
    """Logger wrapper that automatically sanitizes sensitive data."""

    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)

    def _sanitize_args(self, args: tuple[Any, ...]) -> tuple[Any, ...]:
        """Sanitize logging arguments to remove sensitive data."""
        return tuple(
            sanitize_error_message(str(arg)) if isinstance(arg, str) else arg for arg in args
        )

    def debug(self, msg: str, *args: Any) -> None:
        """Log debug message with sanitized arguments."""
        self.logger.debug(sanitize_error_message(msg), *self._sanitize_args(args))

    def info(self, msg: str, *args: Any) -> None:
        """Log info message with sanitized arguments."""
        self.logger.info(sanitize_error_message(msg), *self._sanitize_args(args))

    def warning(self, msg: str, *args: Any) -> None:
        """Log warning message with sanitized arguments."""
        self.logger.warning(sanitize_error_message(msg), *self._sanitize_args(args))

    def error(self, msg: str, *args: Any) -> None:
        """Log error message with sanitized arguments."""
        self.logger.error(sanitize_error_message(msg), *self._sanitize_args(args))

    def critical(self, msg: str, *args: Any) -> None:
        """Log critical message with sanitized arguments."""
        self.logger.critical(sanitize_error_message(msg), *self._sanitize_args(args))


def create_secure_logger(name: str) -> SecureLogger:
    """Create a logger that automatically sanitizes sensitive data.

    Args:
        name: Logger name

    Returns:
        SecureLogger: Logger instance with automatic sanitization
    """
    return SecureLogger(name)


class SecretStr:
    """String wrapper that prevents accidental exposure of sensitive data."""

    def __init__(self, value: str | None):
        self._value = value

    def get_secret_value(self) -> str | None:
        """Get the actual secret value. Use with caution."""
        return self._value

    def __str__(self) -> str:
        return "***SECRET***"

    def __repr__(self) -> str:
        return "SecretStr('***SECRET***')"

    def __bool__(self) -> bool:
        return bool(self._value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SecretStr):
            return self._value == other._value
        return False

    def mask(self) -> str:
        """Get masked version of the secret."""
        return mask_api_key(self._value)

    def is_valid_format(self) -> bool:
        """Check if secret has valid format."""
        return validate_api_key_format(self._value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> AfterValidatorFunctionSchema:
        """Pydantic v2 compatibility."""
        from pydantic_core import core_schema

        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(),
        )
