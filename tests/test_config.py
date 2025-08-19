"""Tests for config.py configuration module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from ai_ffmpeg_cli.config import AppConfig
from ai_ffmpeg_cli.config import load_config
from ai_ffmpeg_cli.errors import ConfigError


class TestAppConfig:
    """Test AppConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AppConfig()

        assert config.openai_api_key is None
        assert config.model == "gpt-4o"  # Default from env
        assert config.dry_run is False  # Updated default
        assert config.confirm_default is True
        assert config.timeout_seconds == 60

    def test_config_with_values(self):
        """Test configuration with explicit values."""
        config = AppConfig(
            openai_api_key="test-key",
            model="gpt-4o-mini",
            dry_run=True,
            confirm_default=False,
            timeout_seconds=120,
        )

        assert config.openai_api_key == "test-key"
        assert config.model == "gpt-4o-mini"
        assert config.dry_run is True
        assert config.confirm_default is False
        assert config.timeout_seconds == 120

    @patch("ai_ffmpeg_cli.config.shutil.which")
    def test_validate_ffmpeg_available(self, mock_which):
        """Test ffmpeg availability validation."""
        mock_which.return_value = "/usr/bin/ffmpeg"

        config = AppConfig()
        # Should not raise exception
        config.validate_ffmpeg_available()

    @patch("ai_ffmpeg_cli.config.shutil.which")
    def test_validate_ffmpeg_not_available(self, mock_which):
        """Test ffmpeg not available error."""
        mock_which.return_value = None

        config = AppConfig()

        with pytest.raises(ConfigError, match="ffmpeg not found in PATH"):
            config.validate_ffmpeg_available()

    @patch.dict(os.environ, {"AICLIP_MODEL": "gpt-3.5-turbo"})
    def test_model_from_env(self):
        """Test model loading from environment."""
        config = AppConfig()
        assert config.model == "gpt-3.5-turbo"

    @patch.dict(os.environ, {"AICLIP_DRY_RUN": "true"})
    def test_dry_run_true_from_env(self):
        """Test dry_run=True from environment."""
        config = AppConfig()
        assert config.dry_run is True

    @patch.dict(os.environ, {"AICLIP_DRY_RUN": "false"})
    def test_dry_run_false_from_env(self):
        """Test dry_run=False from environment."""
        config = AppConfig()
        assert config.dry_run is False

    @patch.dict(os.environ, {"AICLIP_DRY_RUN": "1"})
    def test_dry_run_numeric_true_from_env(self):
        """Test dry_run=True from numeric environment value."""
        config = AppConfig()
        assert config.dry_run is True

    @patch.dict(os.environ, {"AICLIP_DRY_RUN": "yes"})
    def test_dry_run_yes_from_env(self):
        """Test dry_run=True from 'yes' environment value."""
        config = AppConfig()
        assert config.dry_run is True


class TestLoadConfig:
    """Test load_config function."""

    @patch("ai_ffmpeg_cli.config.load_dotenv")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("ai_ffmpeg_cli.config.shutil.which")
    def test_load_config_success(self, mock_which, mock_load_dotenv):
        """Test successful config loading."""
        mock_which.return_value = "/usr/bin/ffmpeg"

        config = load_config()

        assert config.openai_api_key == "test-key"
        mock_load_dotenv.assert_called_once_with(override=False)
        mock_which.assert_called_once_with("ffmpeg")

    @patch("ai_ffmpeg_cli.config.load_dotenv")
    @patch("ai_ffmpeg_cli.config.shutil.which")
    def test_load_config_no_ffmpeg(self, mock_which, mock_load_dotenv):
        """Test config loading when ffmpeg is not available."""
        mock_which.return_value = None

        with pytest.raises(ConfigError, match="ffmpeg not found in PATH"):
            load_config()

    @patch("ai_ffmpeg_cli.config.load_dotenv")
    @patch("ai_ffmpeg_cli.config.AppConfig")
    @patch("ai_ffmpeg_cli.config.shutil.which")
    def test_load_config_validation_error(self, mock_which, mock_app_config, mock_load_dotenv):
        """Test config loading with validation error."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        # Create proper ValidationError with line_errors as list

        mock_app_config.side_effect = ValidationError.from_exception_data("Invalid config", [])

        with pytest.raises(ConfigError):
            load_config()

    @patch("ai_ffmpeg_cli.config.load_dotenv")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "AICLIP_MODEL": "custom-model"})
    @patch("ai_ffmpeg_cli.config.shutil.which")
    def test_load_config_with_env_vars(self, mock_which, mock_load_dotenv):
        """Test config loading with environment variables."""
        mock_which.return_value = "/usr/bin/ffmpeg"

        config = load_config()

        assert config.openai_api_key == "test-key"
        assert config.model == "custom-model"

    @patch("ai_ffmpeg_cli.config.load_dotenv")
    @patch.dict(os.environ, {}, clear=True)  # Clear environment
    @patch("ai_ffmpeg_cli.config.shutil.which")
    def test_load_config_minimal(self, mock_which, mock_load_dotenv):
        """Test config loading with minimal environment."""
        mock_which.return_value = "/usr/bin/ffmpeg"

        config = load_config()

        assert config.openai_api_key is None  # Not set in env
        assert config.model == "gpt-4o"  # Default value
        assert config.dry_run is False  # Default value
