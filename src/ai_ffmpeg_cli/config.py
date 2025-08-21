"""Configuration management for ai-ffmpeg-cli.

This module handles loading, validation, and management of application
configuration from environment variables and .env files.
"""

from __future__ import annotations

import os
import shutil

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError
from pydantic import field_validator

from .credential_security import create_secure_logger
from .credential_security import mask_api_key
from .credential_security import validate_api_key_format
from .custom_exceptions import ConfigError

# Create secure logger that masks sensitive information
logger = create_secure_logger(__name__)


class AppConfig(BaseModel):
    """Runtime configuration loaded from environment variables.

    Provides a centralized configuration interface with validation
    and secure handling of sensitive data like API keys.

    Attributes
    ----------
    openai_api_key: str | None
        API key for OpenAI provider. Can be None if not set.
    model: str
        Model name to use for parsing intents (default: gpt-5).
    dry_run: bool
        If True, only preview commands and do not execute.
    confirm_default: bool
        Default value for confirmation prompts (True means default Yes).
    timeout_seconds: int
        Timeout in seconds for LLM parsing requests (1-300 seconds).
    max_file_size: int
        Maximum allowed file size in bytes (default: 500MB).
    allowed_directories: list[str]
        List of directories where file operations are allowed.
    rate_limit_requests: int
        Maximum API requests per minute (1-1000).
    output_directory: str
        Directory where generated output assets will be stored (default: "aiclip").
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
    output_directory: str = Field(default="aiclip")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model name format and warn about non-standard models.

        Ensures the model name is valid and warns when using models
        not in the standard allowed list.

        Args:
            v: Model name to validate

        Returns:
            Validated model name

        Raises:
            ValueError: When model name is empty or invalid
        """
        if not v or not isinstance(v, str):
            raise ValueError("Model name is required")

        # Allow common OpenAI models
        allowed_models = {
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
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

        Converts string input to list, validates directory existence,
        and provides fallback to current directory if no valid directories.

        Args:
            v: Directory path(s) as string or list of strings

        Returns:
            List of validated absolute directory paths
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
            # Fallback to current directory if no valid directories
            validated_dirs = [os.getcwd()]

        return validated_dirs

    @field_validator("output_directory")
    @classmethod
    def validate_output_directory(cls, v: str) -> str:
        """Validate and normalize output directory.

        Ensures the output directory is a valid path and creates it if it doesn't exist.

        Args:
            v: Output directory path as string

        Returns:
            Validated absolute output directory path
        """
        if not v or not isinstance(v, str):
            raise ValueError("Output directory is required")

        try:
            abs_path = os.path.abspath(v)
            # Create directory if it doesn't exist
            if not os.path.exists(abs_path):
                os.makedirs(abs_path, exist_ok=True)
                logger.info(f"Created output directory: {abs_path}")
            elif not os.path.isdir(abs_path):
                raise ValueError(f"Output directory path exists but is not a directory: {v}")

            return abs_path
        except (OSError, ValueError) as e:
            logger.warning(f"Invalid output directory path {v}: {e}")
            # Fallback to "aiclip" in current directory
            fallback_path = os.path.abspath("aiclip")
            try:
                os.makedirs(fallback_path, exist_ok=True)
                logger.info(f"Using fallback output directory: {fallback_path}")
                return fallback_path
            except OSError:
                # Last resort: use current directory
                logger.warning("Could not create output directory, using current directory")
                return os.getcwd()

    def validate_ffmpeg_available(self) -> None:
        """Validate that ffmpeg is available in PATH.

        Checks if ffmpeg executable is accessible in the system PATH.
        Required for all video processing operations.

        Raises:
            ConfigError: When ffmpeg is not found in PATH
        """
        if shutil.which("ffmpeg") is None:
            raise ConfigError(
                "ffmpeg not found in PATH. Please install ffmpeg (e.g., brew install ffmpeg) and retry."
            )

    def validate_api_key_for_use(self) -> None:
        """Validate API key is present and properly formatted for use.

        Checks that the API key exists and follows the correct format
        before allowing it to be used for API calls.

        Raises:
            ConfigError: When API key is missing or invalid
        """
        if not self.openai_api_key:
            raise ConfigError(
                "OPENAI_API_KEY is required for LLM parsing. "
                "Please set it in your environment or create a .env file with: "
                "OPENAI_API_KEY=sk-your-key-here"
            )

        if not validate_api_key_format(self.openai_api_key):
            masked_key = mask_api_key(self.openai_api_key)
            raise ConfigError(
                f"Invalid API key format: {masked_key}. "
                "OpenAI API keys should start with 'sk-' followed by alphanumeric characters."
            )

    def get_api_key_for_client(self) -> str:
        """Get the API key value for client use. Validates first.

        Validates the API key format and presence before returning
        it for use in API clients.

        Returns:
            Validated API key string

        Raises:
            ConfigError: When API key validation fails
        """
        self.validate_api_key_for_use()
        return self.openai_api_key  # type: ignore


def load_config() -> AppConfig:
    """Load configuration from environment variables and validate environment.

    Loads configuration from environment variables and .env files,
    validates all settings, and ensures required dependencies are available.

    Returns
    -------
    AppConfig
        Parsed and validated configuration instance.

    Raises
    ------
    ConfigError
        If configuration is invalid or required dependencies are missing.
    """
    # Load environment variables from .env file (don't override existing env vars)
    load_dotenv(override=False)

    try:
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")

        # Parse allowed directories from comma-separated environment variable
        allowed_dirs_str = os.getenv("AICLIP_ALLOWED_DIRS", "")
        allowed_dirs = (
            [d.strip() for d in allowed_dirs_str.split(",") if d.strip()]
            if allowed_dirs_str
            else []
        )

        # Create configuration instance with environment values
        config = AppConfig(
            openai_api_key=api_key,
            allowed_directories=allowed_dirs or [os.getcwd()],
            timeout_seconds=int(os.getenv("AICLIP_TIMEOUT", "60")),
            max_file_size=int(os.getenv("AICLIP_MAX_FILE_SIZE", str(500 * 1024 * 1024))),
            rate_limit_requests=int(os.getenv("AICLIP_RATE_LIMIT", "60")),
            output_directory=os.getenv("AICLIP_OUTPUT_DIR", "aiclip"),
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

    # Validate required dependencies
    config.validate_ffmpeg_available()

    # Log configuration summary (without sensitive data)
    logger.info(
        f"aiclip configuration: model={config.model}, dry_run={config.dry_run}, "
        f"timeout={config.timeout_seconds}s, allowed_dirs={len(config.allowed_directories)} directories"
    )

    return config
