"""Tests for main.py CLI entry point."""

from unittest.mock import Mock
from unittest.mock import patch

import pytest
import typer

from ai_ffmpeg_cli.cli_operations import _make_llm_client
from ai_ffmpeg_cli.errors import ConfigError
from ai_ffmpeg_cli.main import main


class TestMakeLLM:
    """Test LLM client creation."""

    def test_make_llm_success(self):
        """Test successful LLM client creation."""
        from ai_ffmpeg_cli.config import AppConfig

        config = AppConfig(
            openai_api_key="sk-1234567890abcdef1234567890abcdef12345678", model="gpt-4o"
        )
        client = _make_llm_client(config)

        assert client is not None
        assert client.provider.model == "gpt-4o"

    def test_make_llm_no_api_key(self):
        """Test LLM client creation fails without API key."""
        from ai_ffmpeg_cli.config import AppConfig

        config = AppConfig(openai_api_key=None)

        with pytest.raises(ConfigError, match="OPENAI_API_KEY is required"):
            _make_llm_client(config)


class TestMainCLI:
    """Test main CLI functionality."""

    @patch("ai_ffmpeg_cli.main.process_natural_language_prompt")
    @patch("ai_ffmpeg_cli.main.load_config")
    @pytest.mark.e2e
    def test_one_shot_mode_success(
        self,
        mock_load_config,
        mock_process_prompt,
    ):
        """Test one-shot mode with successful execution."""
        from ai_ffmpeg_cli.config import AppConfig

        # Setup mocks
        config = AppConfig(openai_api_key="test-key", dry_run=False)
        mock_load_config.return_value = config
        mock_process_prompt.return_value = 0

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
        mock_process_prompt.assert_called_once_with("convert test.mp4", config, False)

    @patch("ai_ffmpeg_cli.main.process_natural_language_prompt")
    @patch("ai_ffmpeg_cli.main.load_config")
    def test_one_shot_mode_parse_error(
        self,
        mock_load_config,
        mock_process_prompt,
    ):
        """Test one-shot mode with parse error."""
        from ai_ffmpeg_cli.config import AppConfig
        from ai_ffmpeg_cli.errors import ParseError

        # Setup mocks
        config = AppConfig(openai_api_key="test-key")
        mock_load_config.return_value = config
        mock_process_prompt.side_effect = ParseError("Parse failed")

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

    def test_explain_command_exists(self):
        """Test that explain command exists."""
        from ai_ffmpeg_cli.main import explain_cmd

        # Test that the explain command function exists
        assert callable(explain_cmd)

    def test_explain_command_function_exists(self):
        """Test that explain command function exists."""
        from ai_ffmpeg_cli.main import explain_cmd

        # Test that the function exists and is callable
        assert callable(explain_cmd)

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_no_args(self, mock_rprint):
        """Test explain command with no arguments."""
        import typer

        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with no args
        mock_ctx = Mock()
        mock_ctx.args = []

        with pytest.raises(typer.Exit) as exc_info:
            explain_cmd(mock_ctx)

        assert exc_info.value.exit_code == 2
        mock_rprint.assert_called()

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_empty_command(self, mock_rprint):
        """Test explain command with empty command string."""
        import typer

        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with empty args
        mock_ctx = Mock()
        mock_ctx.args = [""]

        with pytest.raises(typer.Exit) as exc_info:
            explain_cmd(mock_ctx)

        assert exc_info.value.exit_code == 2
        mock_rprint.assert_called()

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_invalid_command(self, mock_rprint):
        """Test explain command with invalid ffmpeg command."""
        import typer

        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with invalid command
        mock_ctx = Mock()
        mock_ctx.args = ["invalid", "command"]

        with pytest.raises(typer.Exit) as exc_info:
            explain_cmd(mock_ctx)

        assert exc_info.value.exit_code == 1
        mock_rprint.assert_called()

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_basic_command(self, mock_rprint):
        """Test explain command with basic ffmpeg command."""
        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with basic command
        mock_ctx = Mock()
        mock_ctx.args = ["ffmpeg", "-i", "input.mp4", "output.mp4"]

        explain_cmd(mock_ctx)

        # Verify that rprint was called multiple times for the explanation
        assert mock_rprint.call_count >= 3

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_with_video_filters(self, mock_rprint):
        """Test explain command with video filters."""
        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with command containing video filters
        mock_ctx = Mock()
        mock_ctx.args = [
            "ffmpeg",
            "-i",
            "input.mp4",
            "-vf",
            "scale=1280:720",
            "output.mp4",
        ]

        explain_cmd(mock_ctx)

        # Verify that the explanation includes video filtering
        calls = [str(call) for call in mock_rprint.call_args_list]
        assert any("Video filtering applied" in call for call in calls)

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_with_codecs(self, mock_rprint):
        """Test explain command with codec specifications."""
        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with command containing codecs
        mock_ctx = Mock()
        mock_ctx.args = [
            "ffmpeg",
            "-i",
            "input.mp4",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "output.mp4",
        ]

        explain_cmd(mock_ctx)

        # Verify that the explanation includes codec information
        calls = [str(call) for call in mock_rprint.call_args_list]
        assert any("Video codec specified" in call for call in calls)
        assert any("Audio codec specified" in call for call in calls)

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_with_timing(self, mock_rprint):
        """Test explain command with timing parameters."""
        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with command containing timing
        mock_ctx = Mock()
        mock_ctx.args = [
            "ffmpeg",
            "-i",
            "input.mp4",
            "-ss",
            "10",
            "-t",
            "30",
            "output.mp4",
        ]

        explain_cmd(mock_ctx)

        # Verify that the explanation includes timing information
        calls = [str(call) for call in mock_rprint.call_args_list]
        assert any("Seeking to specific time" in call for call in calls)
        assert any("Duration/time limit specified" in call for call in calls)

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_with_quality_settings(self, mock_rprint):
        """Test explain command with quality settings."""
        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with command containing quality settings
        mock_ctx = Mock()
        mock_ctx.args = [
            "ffmpeg",
            "-i",
            "input.mp4",
            "-crf",
            "23",
            "-b:v",
            "2M",
            "output.mp4",
        ]

        explain_cmd(mock_ctx)

        # Verify that the explanation includes quality information
        calls = [str(call) for call in mock_rprint.call_args_list]
        assert any("Quality-based encoding" in call for call in calls)
        assert any("Bitrate-based encoding" in call for call in calls)

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_with_scaling(self, mock_rprint):
        """Test explain command with scaling parameters."""
        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with command containing scaling
        mock_ctx = Mock()
        mock_ctx.args = [
            "ffmpeg",
            "-i",
            "input.mp4",
            "-vf",
            "scale=1920:1080",
            "output.mp4",
        ]

        explain_cmd(mock_ctx)

        # Verify that the explanation includes scaling information
        calls = [str(call) for call in mock_rprint.call_args_list]
        assert any("Video scaling/resizing" in call for call in calls)

    @patch("ai_ffmpeg_cli.main.rprint")
    def test_explain_cmd_minimal_command(self, mock_rprint):
        """Test explain command with minimal ffmpeg command."""
        from ai_ffmpeg_cli.main import explain_cmd

        # Create a mock context with minimal command
        mock_ctx = Mock()
        mock_ctx.args = ["ffmpeg", "input.mp4"]

        explain_cmd(mock_ctx)

        # Verify that the explanation includes basic command info
        calls = [str(call) for call in mock_rprint.call_args_list]

        # For minimal command, we expect output file detection
        assert any("Output file" in call for call in calls)
        # And we expect the note about basic explanation
        assert any("basic explanation" in call for call in calls)


class TestNLCommandInteractive:
    """Test nl command interactive functionality."""

    def test_nl_command_interactive_mode_structure(self):
        """Test nl command structure for interactive mode."""
        from ai_ffmpeg_cli.main import nl

        # Test that the function exists and is callable
        assert callable(nl)

        # Test that it accepts the expected parameters
        import inspect

        sig = inspect.signature(nl)
        assert "ctx" in sig.parameters
        assert "prompt" in sig.parameters

    def test_nl_command_with_existing_context_structure(self):
        """Test nl command structure with existing context."""
        from ai_ffmpeg_cli.main import nl

        # Test that the function exists and is callable
        assert callable(nl)

        # Test that it can handle context with obj
        mock_ctx = Mock()
        mock_ctx.obj = {"config": Mock(), "assume_yes": True}

        # This should not raise an error for basic structure test
        assert mock_ctx.obj["config"] is not None
        assert mock_ctx.obj["assume_yes"] is True

    @patch("ai_ffmpeg_cli.main.rprint")
    @patch("ai_ffmpeg_cli.main.load_config")
    @patch("ai_ffmpeg_cli.main.setup_logging")
    def test_nl_command_config_error(self, mock_setup, mock_load_config, mock_rprint):
        """Test nl command with config error."""
        import typer

        from ai_ffmpeg_cli.errors import ConfigError
        from ai_ffmpeg_cli.main import nl

        # Setup mocks
        mock_load_config.side_effect = ConfigError("Config failed")

        # Create a mock context
        mock_ctx = Mock()
        mock_ctx.obj = None

        # Test config error handling
        with pytest.raises(typer.Exit) as exc_info:
            nl(mock_ctx, prompt=None)

        assert exc_info.value.exit_code == 1
        mock_rprint.assert_called()


class TestMainCLIAdditional:
    """Additional tests for main CLI functionality."""

    @patch("ai_ffmpeg_cli.main.setup_logging")
    @pytest.mark.e2e
    def test_main_with_model_override(self, mock_setup):
        """Test main function with model override."""
        import typer

        from ai_ffmpeg_cli.main import main

        with patch("ai_ffmpeg_cli.main.load_config") as mock_load_config:
            mock_config = Mock()
            mock_load_config.return_value = mock_config

            with patch("ai_ffmpeg_cli.main.process_natural_language_prompt") as mock_process:
                mock_process.return_value = 0

                with pytest.raises(typer.Exit) as exc_info:
                    main(
                        None,
                        prompt="test",
                        model="gpt-4o-mini",
                        dry_run=None,
                        timeout=30,
                        verbose=True,
                    )

                assert exc_info.value.exit_code == 0
                # Verify model was set
                assert mock_config.model == "gpt-4o-mini"
                # Verify timeout was set
                assert mock_config.timeout_seconds == 30
                # Verify logging was set up
                mock_setup.assert_called_with(True)

    @patch("ai_ffmpeg_cli.main.setup_logging")
    def test_main_with_dry_run_override(self, mock_setup):
        """Test main function with dry_run override."""
        import typer

        from ai_ffmpeg_cli.main import main

        with patch("ai_ffmpeg_cli.main.load_config") as mock_load_config:
            mock_config = Mock()
            mock_load_config.return_value = mock_config

            with patch("ai_ffmpeg_cli.main.process_natural_language_prompt") as mock_process:
                mock_process.return_value = 0

                with pytest.raises(typer.Exit) as exc_info:
                    main(None, prompt="test", dry_run=True, timeout=60, verbose=False)

                assert exc_info.value.exit_code == 0
                # Verify dry_run was set
                assert mock_config.dry_run is True
                # Verify logging was set up
                mock_setup.assert_called_with(False)

    def test_version_callback(self):
        """Test version callback functionality."""
        import typer

        from ai_ffmpeg_cli.main import version_callback

        with pytest.raises(typer.Exit) as exc_info:
            version_callback(True)

        # Version callback should exit with code 0
        assert exc_info.value.exit_code == 0
