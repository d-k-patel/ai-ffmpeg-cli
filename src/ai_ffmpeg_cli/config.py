from __future__ import annotations

import os
import shutil

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError

from .errors import ConfigError


class AppConfig(BaseModel):
    """Runtime configuration loaded from environment variables.

    Attributes
    ----------
    openai_api_key: Optional[str]
        API key for OpenAI provider. Optional at import time, but validated
        when the provider is used.
    model: str
        Model name to use for parsing intents.
    dry_run: bool
        If True, only preview commands and do not execute.
    confirm_default: bool
        Default value for confirmation prompts (True means default Yes).
    timeout_seconds: int
        Timeout in seconds for LLM parsing requests.
    """

    openai_api_key: str | None = Field(default=None)
    model: str = Field(default_factory=lambda: os.getenv("AICLIP_MODEL", "gpt-4o"))
    dry_run: bool = Field(
        default_factory=lambda: os.getenv("AICLIP_DRY_RUN", "false").lower() in ("1", "true", "yes")
    )
    confirm_default: bool = Field(default=True)
    timeout_seconds: int = Field(default=60)

    def validate_ffmpeg_available(self) -> None:
        if shutil.which("ffmpeg") is None:
            raise ConfigError(
                "ffmpeg not found in PATH. Please install ffmpeg (e.g., brew install ffmpeg) and retry."
            )


def load_config() -> AppConfig:
    """Load configuration from environment variables and validate environment.

    Returns
    -------
    AppConfig
        Parsed configuration instance.
    """

    load_dotenv(override=False)
    try:
        config = AppConfig(openai_api_key=os.getenv("OPENAI_API_KEY"))
    except ValidationError as exc:
        raise ConfigError(
            f"Configuration validation failed: {exc}. "
            f"Please check your environment variables and .env file format. "
            f"Required: OPENAI_API_KEY. Optional: AICLIP_MODEL, AICLIP_DRY_RUN."
        ) from exc

    # ffmpeg required for runtime usage; validate here when CLI starts
    config.validate_ffmpeg_available()
    return config
