"""Security utilities for handling sensitive data and credentials.

This module provides comprehensive security utilities for protecting sensitive
information like API keys, user credentials, and file paths. It includes
automatic sanitization, secure logging, and data masking capabilities.

Key features:
- API key masking and validation
- Error message sanitization
- Secure logging with automatic sanitization
- Secret string wrapper for sensitive data
- Pattern-based sensitive data detection

Security measures:
- Automatic masking of API keys in logs
- Sanitization of error messages
- Protection against credential exposure
- User path anonymization
- Comprehensive pattern matching
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from pydantic_core.core_schema import AfterValidatorFunctionSchema

logger = logging.getLogger(__name__)


def mask_api_key(api_key: str | None) -> str:
    """Mask API key for safe display in logs and error messages.

    Creates a safe representation of API keys that shows only the first
    and last few characters, masking the sensitive middle portion.

    Args:
        api_key: The API key to mask

    Returns:
        str: Masked version safe for logging and display

    Examples:
        >>> mask_api_key("sk-1234567890abcdef")
        "sk-***def"
        >>> mask_api_key("short")
        "***SHORT_KEY***"
    """
    if not api_key or not isinstance(api_key, str):
        return "***NO_KEY***"

    if len(api_key) <= 8:
        return "***SHORT_KEY***"

    # Show first 3 and last 3 characters, mask the rest
    return f"{api_key[:3]}***{api_key[-3:]}"


def validate_api_key_format(api_key: str | None) -> bool:
    """Validate API key has expected format without logging the key.

    Checks if the API key follows OpenAI's expected format without
    exposing the actual key in logs or error messages.

    Args:
        api_key: The API key to validate

    Returns:
        bool: True if format is valid (starts with 'sk-' and has proper length)
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

    Scans error messages for patterns that might contain sensitive data
    and replaces them with safe placeholders. Protects against accidental
    exposure of API keys, user paths, and other sensitive information.

    Args:
        message: Original error message to sanitize

    Returns:
        str: Sanitized error message with sensitive data masked

    Examples:
        >>> sanitize_error_message("API key sk-1234567890abcdef failed")
        "API key ***API_KEY*** failed"
        >>> sanitize_error_message("Error in /Users/john/file.txt")
        "Error in /Users/***USER***/file.txt"
    """
    if not message:
        return ""

    # Patterns to mask - comprehensive coverage of sensitive data
    patterns = [
        # API keys (OpenAI format)
        (r"sk-[a-zA-Z0-9]{10,}", "***API_KEY***"),
        (r"OPENAI_API_KEY[=\s:]+[^\s]+", "OPENAI_API_KEY=***MASKED***"),
        # File paths that might contain sensitive info (user directories)
        (r"/Users/[^/\s]+", "/Users/***USER***"),
        (r"C:\\\\Users\\\\[^\\\\s]+", r"C:\\Users\\***USER***"),
        # Potential passwords or tokens in various formats
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

    Provides a drop-in replacement for the standard logger that automatically
    sanitizes all log messages and arguments to prevent sensitive data exposure.
    """

    def __init__(self, logger_name: str):
        """Initialize secure logger with the given name.

        Args:
            logger_name: Name for the logger instance
        """
        self.logger = logging.getLogger(logger_name)

    def _sanitize_args(self, args: tuple[Any, ...]) -> tuple[Any, ...]:
        """Sanitize logging arguments to remove sensitive data.

        Processes all string arguments through sanitize_error_message
        to ensure no sensitive data is logged.

        Args:
            args: Logging arguments to sanitize

        Returns:
            tuple: Sanitized arguments safe for logging
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

    Factory function to create a SecureLogger instance that provides
    automatic sanitization of all log messages and arguments.

    Args:
        name: Logger name for identification

    Returns:
        SecureLogger: Logger instance with automatic sanitization
    """
    return SecureLogger(name)


class SecretStr:
    """String wrapper that prevents accidental exposure of sensitive data.

    Provides a safe container for sensitive strings that prevents
    accidental logging or display of the actual value. Includes
    validation and masking capabilities.
    """

    def __init__(self, value: str | None):
        """Initialize secret string with the sensitive value.

        Args:
            value: The sensitive string to protect
        """
        self._value = value

    def get_secret_value(self) -> str | None:
        """Get the actual secret value. Use with caution.

        Returns the actual secret value. This method should only be used
        when absolutely necessary and the value is needed for API calls.

        Returns:
            str | None: The actual secret value
        """
        return self._value

    def __str__(self) -> str:
        """String representation that masks the secret."""
        return "***SECRET***"

    def __repr__(self) -> str:
        """Representation that masks the secret."""
        return "SecretStr('***SECRET***')"

    def __bool__(self) -> bool:
        """Boolean evaluation based on whether secret has a value."""
        return bool(self._value)

    def __eq__(self, other: object) -> bool:
        """Equality comparison with other SecretStr instances."""
        if isinstance(other, SecretStr):
            return self._value == other._value
        return False

    def mask(self) -> str:
        """Get masked version of the secret.

        Returns a safely masked version of the secret value
        suitable for logging or display.

        Returns:
            str: Masked version of the secret
        """
        return mask_api_key(self._value)

    def is_valid_format(self) -> bool:
        """Check if secret has valid format.

        Validates the secret value against expected format
        without exposing the actual value.

        Returns:
            bool: True if secret has valid format
        """
        return validate_api_key_format(self._value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> AfterValidatorFunctionSchema:
        """Pydantic v2 compatibility for SecretStr validation.

        Provides Pydantic schema integration for automatic
        SecretStr wrapping in Pydantic models.
        """
        from pydantic_core import core_schema

        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(),
        )
