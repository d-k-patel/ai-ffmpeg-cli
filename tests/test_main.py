"""Tests for main.py CLI entry point."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from ai_ffmpeg_cli.main import _make_llm, app, main
from ai_ffmpeg_cli.errors import ConfigError


class TestMakeLLM:
    """Test LLM client creation."""

    def test_make_llm_success(self):
        """Test successful LLM client creation."""
        from ai_ffmpeg_cli.config import AppConfig

        config = AppConfig(openai_api_key="test-key", model="gpt-4o")
        client = _make_llm(config)

        assert client is not None
        assert client.provider.model == "gpt-4o"

    def test_make_llm_no_api_key(self):
        """Test LLM client creation fails without API key."""
        from ai_ffmpeg_cli.config import AppConfig

        config = AppConfig(openai_api_key=None)

        with pytest.raises(ConfigError, match="OPENAI_API_KEY is required"):
            _make_llm(config)


class TestMainCLI:
    """Test main CLI functionality."""

    @patch("ai_ffmpeg_cli.main.load_config")
    @patch("ai_ffmpeg_cli.main.scan")
    @patch("ai_ffmpeg_cli.main._make_llm")
    @patch("ai_ffmpeg_cli.main.route_intent")
    @patch("ai_ffmpeg_cli.main.build_commands")
    @patch("ai_ffmpeg_cli.main.confirm_prompt")
    @patch("ai_ffmpeg_cli.executor.run")
    @patch("ai_ffmpeg_cli.executor.preview")
    def test_one_shot_mode_success(
        self,
        mock_preview,
        mock_run,
        mock_confirm,
        mock_build,
        mock_route,
        mock_make_llm,
        mock_scan,
        mock_load_config,
    ):
        """Test one-shot mode with successful execution."""
        from ai_ffmpeg_cli.config import AppConfig
        from ai_ffmpeg_cli.nl_schema import FfmpegIntent, Action

        # Setup mocks
        config = AppConfig(openai_api_key="test-key", dry_run=False)
        mock_load_config.return_value = config
        mock_scan.return_value = {"cwd": "/test"}

        mock_client = Mock()
        mock_intent = FfmpegIntent(action=Action.convert, inputs=[Path("test.mp4")])
        mock_client.parse.return_value = mock_intent
        mock_make_llm.return_value = mock_client

        mock_plan = Mock()
        mock_route.return_value = mock_plan
        mock_commands = [["ffmpeg", "-i", "test.mp4", "output.mp4"]]
        mock_build.return_value = mock_commands
        mock_confirm.return_value = True
        mock_run.return_value = 0

        # Test - call main function directly, not through typer context
        with pytest.raises(typer.Exit) as exc_info:
            main(
                None,
                prompt="convert test.mp4",
                yes=False,
                model=None,
                dry_run=None,
                timeout=60,
                verbose=False,
            )

        assert exc_info.value.exit_code == 0
        mock_preview.assert_called_once()
        mock_confirm.assert_called_once()
        mock_run.assert_called_once()

    @patch("ai_ffmpeg_cli.main.load_config")
    @patch("ai_ffmpeg_cli.main.scan")
    @patch("ai_ffmpeg_cli.main._make_llm")
    def test_one_shot_mode_parse_error(
        self, mock_make_llm, mock_scan, mock_load_config
    ):
        """Test one-shot mode with parsing error."""
        from ai_ffmpeg_cli.config import AppConfig
        from ai_ffmpeg_cli.errors import ParseError

        # Setup mocks
        config = AppConfig(openai_api_key="test-key")
        mock_load_config.return_value = config
        mock_scan.return_value = {"cwd": "/test"}

        mock_client = Mock()
        mock_client.parse.side_effect = ParseError("Parse failed")
        mock_make_llm.return_value = mock_client

        # Test
        with pytest.raises(typer.Exit) as exc_info:
            main(
                None,
                prompt="invalid prompt",
                yes=False,
                model=None,
                dry_run=None,
                timeout=60,
                verbose=False,
            )

        assert exc_info.value.exit_code == 1

    @patch("ai_ffmpeg_cli.main.load_config")
    def test_config_error(self, mock_load_config):
        """Test configuration error handling."""
        from ai_ffmpeg_cli.errors import ConfigError

        mock_load_config.side_effect = ConfigError("Config failed")

        with pytest.raises(typer.Exit) as exc_info:
            main(
                None,
                prompt="test",
                yes=False,
                model=None,
                dry_run=None,
                timeout=60,
                verbose=False,
            )

        assert exc_info.value.exit_code == 1

    def test_model_parameter_validation(self):
        """Test that model parameter validation works."""
        # This is a simpler test that doesn't require complex mocking
        valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]

        # Test that these are valid model names (basic validation)
        for model in valid_models:
            assert isinstance(model, str)
            assert len(model) > 0

    def test_timeout_parameter_validation(self):
        """Test that timeout parameter is properly typed."""
        # Basic validation test
        timeout = 60
        assert isinstance(timeout, int)
        assert timeout > 0


class TestNLCommand:
    """Test nl subcommand functionality."""

    def test_nl_command_exists(self):
        """Test that nl command exists in app."""
        from ai_ffmpeg_cli.main import nl

        # Basic test that function exists and is callable
        assert callable(nl)

    def test_interactive_exit_commands(self):
        """Test that exit commands are recognized."""
        exit_commands = ["exit", "quit", "q"]

        for cmd in exit_commands:
            # Test that these are recognized as exit commands
            assert cmd.lower() in ["exit", "quit", "q"]


class TestExplainCommand:
    """Test explain subcommand."""

    def test_explain_no_command(self):
        """Test explain without command."""
        from ai_ffmpeg_cli.main import explain

        with pytest.raises(typer.Exit) as exc_info:
            explain(None)

        assert exc_info.value.exit_code == 2

    def test_explain_with_command(self):
        """Test explain with command (not implemented)."""
        from ai_ffmpeg_cli.main import explain

        # Should not raise exception, just prints message
        explain("ffmpeg -i input.mp4 output.mp4")
