"""Configuration management for ai-ffmpeg-cli.

This module handles application configuration loading, validation, and
environment setup. It provides a centralized configuration system with
environment variable support and comprehensive validation.

Key features:
- Environment variable loading with .env file support
- Pydantic-based configuration validation
- API key security and masking
- Directory validation and normalization
- Dependency availability checking
- Comprehensive error reporting

Configuration sources:
- Environment variables (primary)
- .env file (fallback)
- Default values (sensible defaults)
"""

from __future__ import annotations

import os
import shutil

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError
from pydantic import field_validator

from .errors import ConfigError
from .security import create_secure_logger
from .security import mask_api_key

logger = create_secure_logger(__name__)


class AppConfig(BaseModel):
    """Runtime configuration loaded from environment variables.

    Central configuration class that manages all application settings
    with comprehensive validation and security features.

    Attributes:
        openai_api_key: API key for OpenAI provider (securely handled)
        model: Model name to use for parsing intents
        dry_run: If True, only preview commands and do not execute
        confirm_default: Default value for confirmation prompts
        timeout_seconds: Timeout in seconds for LLM parsing requests
        max_file_size: Maximum allowed file size in bytes (default: 500MB)
        allowed_directories: List of directories where file operations are allowed
        rate_limit_requests: Maximum API requests per minute
    """

    openai_api_key: str | None = Field(default=None)
    model: str = Field(default_factory=lambda: os.getenv("AICLIP_MODEL", "gpt-4o"))
    dry_run: bool = Field(
        default_factory=lambda: os.getenv("AICLIP_DRY_RUN", "false").lower() in ("1", "true", "yes")
    )
    confirm_default: bool = Field(default=True)
    timeout_seconds: int = Field(default=60, ge=1, le=300)  # 1-300 seconds
    max_file_size: int = Field(default=500 * 1024 * 1024)  # 500MB
    allowed_directories: list[str] = Field(default_factory=lambda: [os.getcwd()])
    rate_limit_requests: int = Field(default=60, ge=1, le=1000)  # requests per minute

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model name format and compatibility.

        Ensures the model name is valid and warns about non-standard models.
        Allows common OpenAI models while providing warnings for others.

        Args:
            v: Model name to validate

        Returns:
            str: Validated model name

        Raises:
            ValueError: If model name is invalid or missing
        """
        if not v or not isinstance(v, str):
            raise ValueError("Model name is required")

        # Allow common OpenAI models with known compatibility
        allowed_models = {
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        }

        if v not in allowed_models:
            logger.warning(f"Using non-standard model: {v}")

        return v

    @field_validator("allowed_directories", mode="before")
    @classmethod
    def validate_directories(cls, v: list[str] | str) -> list[str]:
        """Validate and normalize allowed directories.

        Converts string inputs to lists, validates directory existence,
        and provides fallback to current directory if needed.

        Args:
            v: Directory path(s) to validate (string or list)

        Returns:
            list[str]: List of validated absolute directory paths
        """
        if isinstance(v, str):
            v = [v]

        validated_dirs = []
        for dir_path in v:
            try:
                abs_path = os.path.abspath(dir_path)
                if os.path.exists(abs_path) and os.path.isdir(abs_path):
                    validated_dirs.append(abs_path)
                else:
                    logger.warning(f"Directory does not exist or is not accessible: {dir_path}")
            except (OSError, ValueError) as e:
                logger.warning(f"Invalid directory path {dir_path}: {e}")

        if not validated_dirs:
            # Fallback to current directory if no valid directories provided
            validated_dirs = [os.getcwd()]

        return validated_dirs

    def validate_ffmpeg_available(self) -> None:
        """Validate that ffmpeg is available in PATH.

        Checks if ffmpeg executable is accessible in the system PATH.
        Required for all media processing operations.

        Raises:
            ConfigError: If ffmpeg is not found in PATH
        """
        if shutil.which("ffmpeg") is None:
            raise ConfigError(
                "ffmpeg not found in PATH. Please install ffmpeg (e.g., brew install ffmpeg) and retry."
            )

    def validate_api_key_for_use(self) -> None:
        """Validate API key is present and properly formatted for use.

        Ensures the OpenAI API key is available before attempting to use
        the LLM services. Provides clear guidance if missing.

        Raises:
            ConfigError: If API key is missing or invalid
        """
        if not self.openai_api_key:
            raise ConfigError(
                "OPENAI_API_KEY is required for LLM parsing. "
                "Please set it in your environment or create a .env file with: "
                "OPENAI_API_KEY=sk-your-key-here"
            )

    def get_api_key_for_client(self) -> str:
        """Get the API key value for client use with validation.

        Validates the API key is present before returning it for use
        in LLM client initialization.

        Returns:
            str: Validated API key

        Raises:
            ConfigError: If API key is missing or invalid
        """
        self.validate_api_key_for_use()
        return self.openai_api_key  # type: ignore


def load_config() -> AppConfig:
    """Load configuration from environment variables and validate environment.

    Main configuration loading function that handles environment setup,
    validation, and dependency checking. Loads from .env file and
    environment variables with comprehensive error handling.

    Returns:
        AppConfig: Parsed and validated configuration instance

    Raises:
        ConfigError: If configuration is invalid or required dependencies are missing
    """
    # Load environment variables from .env file (if present)
    load_dotenv(override=False)

    try:
        # Get API key from environment (primary source)
        api_key = os.getenv("OPENAI_API_KEY")

        # Get allowed directories (comma-separated list from environment)
        allowed_dirs_str = os.getenv("AICLIP_ALLOWED_DIRS", "")
        allowed_dirs = (
            [d.strip() for d in allowed_dirs_str.split(",") if d.strip()]
            if allowed_dirs_str
            else []
        )

        # Create configuration with environment values
        config = AppConfig(
            openai_api_key=api_key,
            allowed_directories=allowed_dirs or [os.getcwd()],
            timeout_seconds=int(os.getenv("AICLIP_TIMEOUT", "60")),
            max_file_size=int(os.getenv("AICLIP_MAX_FILE_SIZE", str(500 * 1024 * 1024))),
            rate_limit_requests=int(os.getenv("AICLIP_RATE_LIMIT", "60")),
        )

        logger.debug(f"Configuration loaded successfully with API key: {mask_api_key(api_key)}")

    except (ValidationError, ValueError) as exc:
        # Sanitize error messages to prevent API key exposure
        sanitized_error = str(exc).replace(api_key or "", "***API_KEY***") if api_key else str(exc)
        raise ConfigError(
            f"Configuration validation failed: {sanitized_error}. "
            f"Please check your environment variables and .env file format. "
            f"Required: OPENAI_API_KEY. Optional: AICLIP_MODEL, AICLIP_DRY_RUN, "
            f"AICLIP_ALLOWED_DIRS, AICLIP_TIMEOUT, AICLIP_MAX_FILE_SIZE, AICLIP_RATE_LIMIT."
        ) from exc

    # Validate required dependencies are available
    config.validate_ffmpeg_available()

    # Log configuration summary (without sensitive data)
    logger.info(
        f"aiclip configuration: model={config.model}, dry_run={config.dry_run}, "
        f"timeout={config.timeout_seconds}s, allowed_dirs={len(config.allowed_directories)} directories"
    )

    return config
