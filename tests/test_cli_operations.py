"""Tests for CLI operations module."""

from __future__ import annotations

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ai_ffmpeg_cli.cli_operations import _execute_commands
from ai_ffmpeg_cli.cli_operations import _make_llm_client
from ai_ffmpeg_cli.cli_operations import process_interactive_session
from ai_ffmpeg_cli.cli_operations import process_natural_language_prompt
from ai_ffmpeg_cli.cli_operations import setup_logging
from ai_ffmpeg_cli.errors import BuildError
from ai_ffmpeg_cli.errors import ConfigError
from ai_ffmpeg_cli.errors import ExecError
from ai_ffmpeg_cli.errors import ParseError
from ai_ffmpeg_cli.nl_schema import Action
from ai_ffmpeg_cli.nl_schema import FfmpegIntent


class TestSetupLogging:
    """Test logging setup functionality."""

    def test_setup_logging_verbose(self):
        """Test verbose logging setup."""
        # Test that the function doesn't raise exceptions
        try:
            setup_logging(True)
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"setup_logging(True) raised {e} unexpectedly")

    def test_setup_logging_normal(self):
        """Test normal logging setup."""
        # Test that the function doesn't raise exceptions
        try:
            setup_logging(False)
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"setup_logging(False) raised {e} unexpectedly")


class TestMakeLLMClient:
    """Test LLM client creation."""

    def test_make_llm_client_success(self, mock_config):
        """Test successful LLM client creation."""
        client = _make_llm_client(mock_config)
        assert client is not None
        assert hasattr(client, "provider")

    def test_make_llm_client_no_api_key(self, mock_config_no_api_key):
        """Test LLM client creation with missing API key."""
        with pytest.raises(ConfigError, match="OPENAI_API_KEY is required"):
            _make_llm_client(mock_config_no_api_key)


class TestExecuteCommands:
    """Test command execution functionality."""

    def test_execute_commands_success(self, mock_config):
        """Test successful command execution."""
        commands = [["ffmpeg", "-i", "test.mp4", "output.mp4"]]

        with (
            patch("ai_ffmpeg_cli.executor.preview") as mock_preview,
            patch("ai_ffmpeg_cli.cli_operations.confirm_prompt") as mock_confirm,
            patch("ai_ffmpeg_cli.executor.run") as mock_run,
        ):
            mock_confirm.return_value = True
            mock_run.return_value = 0

            result = _execute_commands(commands, mock_config, assume_yes=False)

            assert result == 0
            mock_preview.assert_called_once_with(commands)
            mock_confirm.assert_called_once()
            mock_run.assert_called_once()

    def test_execute_commands_assume_yes(self, mock_config):
        """Test command execution with assume_yes=True."""
        commands = [["ffmpeg", "-i", "test.mp4", "output.mp4"]]

        with (
            patch("ai_ffmpeg_cli.executor.preview") as mock_preview,
            patch("ai_ffmpeg_cli.cli_operations.confirm_prompt") as mock_confirm,
            patch("ai_ffmpeg_cli.executor.run") as mock_run,
        ):
            mock_run.return_value = 0

            result = _execute_commands(commands, mock_config, assume_yes=True)

            assert result == 0
            mock_preview.assert_called_once_with(commands)
            mock_confirm.assert_not_called()  # Should not be called when assume_yes=True
            mock_run.assert_called_once()


class TestProcessNaturalLanguagePrompt:
    """Test natural language prompt processing."""

    def test_process_natural_language_prompt_success(self, mock_config):
        """Test successful natural language prompt processing."""
        prompt = "convert video.mp4 to 720p"

        with (
            patch("ai_ffmpeg_cli.cli_operations.scan") as mock_scan,
            patch("ai_ffmpeg_cli.cli_operations._make_llm_client") as mock_make_client,
            patch("ai_ffmpeg_cli.cli_operations._execute_commands") as mock_execute,
        ):
            # Mock the scan result
            mock_scan.return_value = {"videos": ["video.mp4"]}

            # Mock the LLM client
            mock_client = Mock()
            mock_intent = FfmpegIntent(action=Action.convert, inputs=["video.mp4"])
            mock_client.parse.return_value = mock_intent
            mock_make_client.return_value = mock_client

            # Mock command execution
            mock_execute.return_value = 0

            result = process_natural_language_prompt(prompt, mock_config, assume_yes=False)

            assert result == 0
            mock_scan.assert_called_once()
            mock_make_client.assert_called_once_with(mock_config)
            mock_client.parse.assert_called_once_with(prompt, {"videos": ["video.mp4"]}, timeout=60)
            mock_execute.assert_called_once()

    def test_process_natural_language_prompt_parse_error(self, mock_config):
        """Test natural language prompt processing with parse error."""
        prompt = "invalid prompt"

        with (
            patch("ai_ffmpeg_cli.cli_operations.scan") as mock_scan,
            patch("ai_ffmpeg_cli.cli_operations._make_llm_client") as mock_make_client,
        ):
            mock_scan.return_value = {"videos": ["video.mp4"]}

            mock_client = Mock()
            mock_client.parse.side_effect = ParseError("Failed to parse prompt")
            mock_make_client.return_value = mock_client

            with pytest.raises(ParseError, match="Failed to parse prompt"):
                process_natural_language_prompt(prompt, mock_config, assume_yes=False)

    def test_process_natural_language_prompt_build_error(self, mock_config):
        """Test natural language prompt processing with build error."""
        prompt = "convert video.mp4 to 720p"

        with (
            patch("ai_ffmpeg_cli.cli_operations.scan") as mock_scan,
            patch("ai_ffmpeg_cli.cli_operations._make_llm_client") as mock_make_client,
            patch("ai_ffmpeg_cli.cli_operations.route_intent") as mock_route,
        ):
            mock_scan.return_value = {"videos": ["video.mp4"]}

            mock_client = Mock()
            mock_intent = FfmpegIntent(action=Action.convert, inputs=["video.mp4"])
            mock_client.parse.return_value = mock_intent
            mock_make_client.return_value = mock_client

            mock_route.side_effect = BuildError("Failed to build commands")

            with pytest.raises(BuildError, match="Failed to build commands"):
                process_natural_language_prompt(prompt, mock_config, assume_yes=False)

    def test_process_natural_language_prompt_exec_error(self, mock_config):
        """Test natural language prompt processing with exec error."""
        prompt = "convert video.mp4 to 720p"

        with (
            patch("ai_ffmpeg_cli.cli_operations.scan") as mock_scan,
            patch("ai_ffmpeg_cli.cli_operations._make_llm_client") as mock_make_client,
            patch("ai_ffmpeg_cli.cli_operations._execute_commands") as mock_execute,
        ):
            mock_scan.return_value = {"videos": ["video.mp4"]}

            mock_client = Mock()
            mock_intent = FfmpegIntent(action=Action.convert, inputs=["video.mp4"])
            mock_client.parse.return_value = mock_intent
            mock_make_client.return_value = mock_client

            mock_execute.side_effect = ExecError("Failed to execute commands")

            with pytest.raises(ExecError, match="Failed to execute commands"):
                process_natural_language_prompt(prompt, mock_config, assume_yes=False)


class TestProcessInteractiveSession:
    """Test interactive session processing."""

    @patch("builtins.input")
    def test_process_interactive_session_exit_command(self, mock_input, mock_config):
        """Test interactive session with exit command."""
        mock_input.return_value = "exit"

        result = process_interactive_session(mock_config, assume_yes=False)

        assert result == 0
        mock_input.assert_called_once_with("aiclip> ")

    @patch("builtins.input")
    def test_process_interactive_session_quit_command(self, mock_input, mock_config):
        """Test interactive session with quit command."""
        mock_input.return_value = "quit"

        result = process_interactive_session(mock_config, assume_yes=False)

        assert result == 0
        mock_input.assert_called_once_with("aiclip> ")

    @patch("builtins.input")
    def test_process_interactive_session_q_command(self, mock_input, mock_config):
        """Test interactive session with q command."""
        mock_input.return_value = "q"

        result = process_interactive_session(mock_config, assume_yes=False)

        assert result == 0
        mock_input.assert_called_once_with("aiclip> ")

    @patch("builtins.input")
    def test_process_interactive_session_empty_input(self, mock_input, mock_config):
        """Test interactive session with empty input."""
        mock_input.side_effect = ["", "exit"]

        result = process_interactive_session(mock_config, assume_yes=False)

        assert result == 0
        assert mock_input.call_count == 2

    @patch("builtins.input")
    def test_process_interactive_session_whitespace_input(self, mock_input, mock_config):
        """Test interactive session with whitespace input."""
        mock_input.side_effect = ["   ", "exit"]

        result = process_interactive_session(mock_config, assume_yes=False)

        assert result == 0
        assert mock_input.call_count == 2

    @patch("builtins.input")
    def test_process_interactive_session_successful_command(self, mock_input, mock_config):
        """Test interactive session with successful command."""
        mock_input.side_effect = ["convert video.mp4 to 720p", "exit"]

        with patch("ai_ffmpeg_cli.cli_operations.process_natural_language_prompt") as mock_process:
            mock_process.return_value = 0

            result = process_interactive_session(mock_config, assume_yes=False)

            assert result == 0
            mock_process.assert_called_once_with("convert video.mp4 to 720p", mock_config, False)

    @patch("builtins.input")
    def test_process_interactive_session_command_with_error(self, mock_input, mock_config):
        """Test interactive session with command that produces error."""
        mock_input.side_effect = ["convert video.mp4 to 720p", "exit"]

        with patch("ai_ffmpeg_cli.cli_operations.process_natural_language_prompt") as mock_process:
            mock_process.side_effect = ParseError("Failed to parse")

            result = process_interactive_session(mock_config, assume_yes=False)

            assert result == 0  # Session should continue despite error
            mock_process.assert_called_once()

    @patch("builtins.input")
    def test_process_interactive_session_keyboard_interrupt(self, mock_input, mock_config):
        """Test interactive session with keyboard interrupt."""
        mock_input.side_effect = KeyboardInterrupt()

        result = process_interactive_session(mock_config, assume_yes=False)

        assert result == 0
        mock_input.assert_called_once()

    @patch("builtins.input")
    def test_process_interactive_session_eof_error(self, mock_input, mock_config):
        """Test interactive session with EOF error."""
        mock_input.side_effect = EOFError()

        result = process_interactive_session(mock_config, assume_yes=False)

        assert result == 0
        mock_input.assert_called_once()


# Fixtures for testing
@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock()
    config.model = "gpt-4o"
    config.timeout_seconds = 60
    config.confirm_default = True
    config.dry_run = False
    config.get_api_key_for_client.return_value = "sk-test1234567890abcdef"
    return config


@pytest.fixture
def mock_config_no_api_key():
    """Create a mock configuration without API key for testing."""
    config = Mock()
    config.model = "gpt-4o"
    config.timeout_seconds = 60
    config.confirm_default = True
    config.dry_run = False
    config.get_api_key_for_client.side_effect = ConfigError("OPENAI_API_KEY is required")
    return config
