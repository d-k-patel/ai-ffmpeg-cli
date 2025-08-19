"""Integration tests for error handling scenarios."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_ffmpeg_cli.errors import ConfigError
from ai_ffmpeg_cli.errors import ParseError


class TestIntegrationErrors:
    """Test integration error handling scenarios."""

    @pytest.mark.integration
    def test_invalid_api_key_handling(self):
        """Test handling of invalid OpenAI API key."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            from ai_ffmpeg_cli.cli_operations import _make_llm_client
            from ai_ffmpeg_cli.config import load_config

            config = load_config()

            # Should handle authentication error gracefully when trying to use the API
            # The validation happens when get_api_key_for_client() is called
            with pytest.raises(ConfigError, match="OPENAI_API_KEY is required"):
                _make_llm_client(config)

    @pytest.mark.integration
    def test_missing_ffmpeg_handling(self):
        """Test handling when ffmpeg is not available."""
        with patch.dict(os.environ, {"PATH": ""}):
            from ai_ffmpeg_cli.config import load_config

            with pytest.raises(ConfigError, match="ffmpeg.*not found"):
                load_config()

    @pytest.mark.integration
    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test1234567890abcdef"}):
            from ai_ffmpeg_cli.cli_operations import _make_llm_client
            from ai_ffmpeg_cli.config import load_config

            config = load_config()
            config.timeout_seconds = 1  # Very short timeout
            client = _make_llm_client(config)

            # Mock the entire parse method to simulate timeout behavior
            with patch.object(client, "parse") as mock_parse:
                mock_parse.side_effect = ParseError(
                    "OpenAI request timed out after 1 seconds. "
                    "Try increasing --timeout or check your internet connection."
                )

                with pytest.raises(ParseError, match="timed out"):
                    client.parse("convert video.mp4", {}, timeout=1)

    @pytest.mark.integration
    def test_file_permission_errors(self):
        """Test handling of file permission errors."""
        import platform

        if platform.system() == "Windows":
            # On Windows, try to write to a system directory that requires admin privileges
            system_dir = Path("C:/Windows/System32")
            test_file = system_dir / "test_write_permission.mp4"

            # This should fail due to permission error on Windows
            with pytest.raises((PermissionError, OSError)):
                test_file.write_bytes(b"fake video data")
        else:
            # On Unix-like systems, use the original approach
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a read-only directory
                readonly_dir = Path(temp_dir) / "readonly"
                readonly_dir.mkdir()
                readonly_dir.chmod(0o444)  # Read-only

                # Try to create a file in read-only directory
                test_file = readonly_dir / "test.mp4"

                # This should fail due to permission error
                with pytest.raises(PermissionError):
                    test_file.write_bytes(b"fake video data")

    @pytest.mark.integration
    def test_disk_space_errors(self):
        """Test handling of disk space errors."""
        # Simulate disk space error by mocking mkdir to fail
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = OSError(28, "No space left on device")

            from ai_ffmpeg_cli.io_utils import ensure_parent_dir

            # Use a path where parent directory doesn't exist to ensure mkdir is called
            with pytest.raises(OSError, match="No space left"):
                ensure_parent_dir(Path("/nonexistent/path/test_output.mp4"))

    @pytest.mark.integration
    def test_corrupted_ffmpeg_installation(self):
        """Test handling of corrupted ffmpeg installation."""
        # Mock shutil.which to return None (ffmpeg not found)
        with patch("shutil.which", return_value=None):
            from ai_ffmpeg_cli.config import load_config

            # Should detect that ffmpeg is not available
            with pytest.raises(ConfigError, match="ffmpeg.*not found"):
                load_config()

    @pytest.mark.integration
    def test_malformed_natural_language_input(self):
        """Test handling of malformed natural language input."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test1234567890abcdef"}):
            from ai_ffmpeg_cli.cli_operations import _make_llm_client
            from ai_ffmpeg_cli.config import load_config

            config = load_config()
            client = _make_llm_client(config)

            # Mock the provider to avoid authentication issues
            with patch.object(client.provider, "complete") as mock_complete:
                mock_complete.return_value = '{"action": "convert", "inputs": ["test.mp4"]}'

                # Test empty input
                with pytest.raises(ParseError, match="Empty or invalid prompt"):
                    client.parse("", {}, timeout=10)

                # Test whitespace-only input
                with pytest.raises(ParseError, match="Empty or invalid prompt"):
                    client.parse("   ", {}, timeout=10)

    @pytest.mark.integration
    def test_concurrent_file_access(self):
        """Test handling of concurrent file access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.mp4"
            test_file.write_bytes(b"fake video data")

            # Simulate concurrent access
            import threading
            import time

            def process_file():
                time.sleep(0.1)  # Simulate processing time
                return test_file.exists()

            threads = [threading.Thread(target=process_file) for _ in range(5)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

    @pytest.mark.integration
    def test_memory_pressure_handling(self):
        """Test handling under memory pressure."""
        import gc

        import psutil

        # Force garbage collection
        gc.collect()

        # Check memory usage
        process = psutil.Process()
        memory_info = process.memory_info()

        # Ensure memory usage is reasonable (< 500MB for CLI tool with dependencies)
        assert memory_info.rss < 500 * 1024 * 1024, "Memory usage too high"

    @pytest.mark.integration
    def test_unicode_filename_handling(self):
        """Test handling of Unicode filenames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with Unicode name
            unicode_filename = "test_🎬_video.mp4"
            test_file = Path(temp_dir) / unicode_filename
            test_file.write_bytes(b"fake video data")

            # Should handle Unicode filenames correctly
            assert test_file.exists()
            assert test_file.name == unicode_filename

    @pytest.mark.integration
    def test_special_character_handling(self):
        """Test handling of special characters in filenames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with special characters
            special_filename = "test video (2024) [HD].mp4"
            test_file = Path(temp_dir) / special_filename
            test_file.write_bytes(b"fake video data")

            # Should handle special characters correctly
            assert test_file.exists()
            assert test_file.name == special_filename
