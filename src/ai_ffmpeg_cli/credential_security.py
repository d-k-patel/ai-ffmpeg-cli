"""Security utilities for handling sensitive data and credentials.

This module provides utilities for secure handling of API keys and other
sensitive information, including masking, validation, and secure logging.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from pydantic_core.core_schema import AfterValidatorFunctionSchema  # noqa: TC003

logger = logging.getLogger(__name__)


def mask_api_key(api_key: str | None) -> str:
    """Mask API key for safe display in logs and errors.

    Creates a masked version of an API key that shows only the first
    and last few characters, preventing accidental exposure in logs.

    Args:
        api_key: The API key to mask

    Returns:
        str: Masked version safe for logging and error messages
    """
    if not api_key or not isinstance(api_key, str):
        return "***NO_KEY***"

    if len(api_key) <= 8:
        return "***SHORT_KEY***"

    # Show first 3 and last 3 characters, mask the rest
    return f"{api_key[:3]}***{api_key[-3:]}"


def validate_api_key_format(api_key: str | None) -> bool:
    """Validate API key has expected format without logging the key.

    Checks that the API key follows the expected OpenAI format
    without exposing the actual key value.

    Args:
        api_key: The API key to validate

    Returns:
        bool: True if format is valid
    """
    if not api_key or not isinstance(api_key, str):
        return False

    # OpenAI API keys start with 'sk-' and can include various formats:
    # - sk-... (standard keys)
    # - sk-proj-... (project keys)
    # - sk-org-... (organization keys)
    if api_key.startswith("sk-"):
        # Remove prefix and check remaining characters
        key_body = api_key[3:]
        # Allow alphanumeric characters, hyphens, and underscores
        if len(key_body) >= 32 and re.match(r"^[a-zA-Z0-9_-]+$", key_body):
            return True

    return False


def sanitize_error_message(message: str) -> str:
    """Remove sensitive information from error messages.

    Scans error messages for patterns that might contain sensitive
    data and replaces them with safe placeholders.

    Args:
        message: Original error message

    Returns:
        str: Sanitized error message with sensitive data masked
    """
    if not message:
        return ""

    # Patterns to mask for security
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
    """Logger wrapper that automatically sanitizes sensitive data.

    Provides a drop-in replacement for the standard logger that
    automatically masks sensitive information in all log messages.
    """

    def __init__(self, logger_name: str):
        """Initialize secure logger with the given name.

        Args:
            logger_name: Name for the underlying logger
        """
        self.logger = logging.getLogger(logger_name)

    def _sanitize_args(self, args: tuple[Any, ...]) -> tuple[Any, ...]:
        """Sanitize logging arguments to remove sensitive data.

        Args:
            args: Logging arguments to sanitize

        Returns:
            Tuple of sanitized arguments
        """
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

    Factory function to create a secure logger instance that will
    automatically mask sensitive information in all log messages.

    Args:
        name: Logger name

    Returns:
        SecureLogger: Logger instance with automatic sanitization
    """
    return SecureLogger(name)


class SecretStr:
    """String wrapper that prevents accidental exposure of sensitive data.

    Provides a safe wrapper around sensitive strings that prevents
    accidental logging or display of the actual value.
    """

    def __init__(self, value: str | None):
        """Initialize with a sensitive string value.

        Args:
            value: The sensitive string to wrap
        """
        self._value = value

    def get_secret_value(self) -> str | None:
        """Get the actual secret value. Use with caution.

        Returns:
            The actual secret value (use only when absolutely necessary)
        """
        return self._value

    def __str__(self) -> str:
        """String representation that masks the secret."""
        return "***SECRET***"

    def __repr__(self) -> str:
        """Representation that masks the secret."""
        return "SecretStr('***SECRET***')"

    def __bool__(self) -> bool:
        """Boolean evaluation based on whether value exists."""
        return bool(self._value)

    def __eq__(self, other: object) -> bool:
        """Equality comparison with other SecretStr instances."""
        if isinstance(other, SecretStr):
            return self._value == other._value
        return False

    def mask(self) -> str:
        """Get masked version of the secret.

        Returns:
            Masked version showing partial content
        """
        return mask_api_key(self._value)

    def is_valid_format(self) -> bool:
        """Check if secret has valid format.

        Returns:
            True if the secret follows expected format
        """
        return validate_api_key_format(self._value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> AfterValidatorFunctionSchema:
        """Pydantic v2 compatibility for schema generation."""
        from pydantic_core import core_schema

        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(),
        )
