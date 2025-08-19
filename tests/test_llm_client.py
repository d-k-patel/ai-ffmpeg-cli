"""Comprehensive tests for LLM client functionality.

This module tests the LLM client's ability to:
- Interface with OpenAI API
- Handle various error conditions gracefully
- Parse natural language into FFmpeg intents
- Retry failed requests appropriately
- Generate mock responses for testing
"""

import json
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from ai_ffmpeg_cli.errors import ParseError
from ai_ffmpeg_cli.llm_client import LLMClient
from ai_ffmpeg_cli.llm_client import LLMProvider
from ai_ffmpeg_cli.llm_client import OpenAIProvider
from ai_ffmpeg_cli.nl_schema import Action
from ai_ffmpeg_cli.nl_schema import FfmpegIntent


class TestLLMProvider:
    """Test the abstract LLMProvider interface."""

    def test_interface_not_implemented(self):
        """Verify that the base provider raises NotImplementedError."""
        provider = LLMProvider()
        with pytest.raises(NotImplementedError):
            provider.complete("system", "user", 60)


class TestOpenAIProvider:
    """Test OpenAI-specific provider functionality."""

    @pytest.fixture
    def mock_openai_client(self):
        """Create a mock OpenAI client for testing."""
        with patch("openai.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def provider(self, mock_openai_client):
        """Create an OpenAI provider with mocked client."""
        return OpenAIProvider(api_key="test-key", model="gpt-4o")

    def test_initialization_success(self, mock_openai_client):
        """Test successful provider initialization."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o")

        assert provider.model == "gpt-4o"
        assert provider.client == mock_openai_client

    @patch("openai.OpenAI")
    def test_initialization_failure(self, mock_openai):
        """Test provider initialization with connection failure."""
        mock_openai.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            OpenAIProvider(api_key="test-key", model="gpt-4o")

    def test_successful_completion(self, provider, mock_openai_client):
        """Test successful API completion request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"action": "convert", "inputs": ["test.mp4"]}'
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Test completion
        result = provider.complete("system prompt", "user prompt", 60)

        assert result == '{"action": "convert", "inputs": ["test.mp4"]}'
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "user prompt"},
            ],
            temperature=0,
            response_format={"type": "json_object"},
            timeout=60,
        )

    def test_empty_response_handling(self, provider, mock_openai_client):
        """Test handling of empty API response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        mock_openai_client.chat.completions.create.return_value = mock_response

        result = provider.complete("system", "user", 60)
        assert result == "{}"

    def test_rate_limit_error_handling(self, provider, mock_openai_client):
        """Test handling of rate limit errors."""

        # Create custom exception that mimics RateLimitError behavior
        class MockRateLimitError(Exception):
            pass

        mock_openai_client.chat.completions.create.side_effect = MockRateLimitError(
            "Rate limit exceeded"
        )

        with pytest.raises(
            ParseError, match="Failed to get response from OpenAI: Rate limit exceeded"
        ):
            provider.complete("system", "user", 60)

    def test_timeout_error_handling(self, provider, mock_openai_client):
        """Test handling of timeout errors."""

        # Create custom exception that mimics APITimeoutError behavior
        class MockAPITimeoutError(Exception):
            pass

        mock_openai_client.chat.completions.create.side_effect = MockAPITimeoutError(
            "Request timed out"
        )

        with pytest.raises(
            ParseError, match="Failed to get response from OpenAI: Request timed out"
        ):
            provider.complete("system", "user", 60)

    def test_api_error_handling(self, provider, mock_openai_client):
        """Test handling of general API errors."""

        # Create custom exception that mimics APIError behavior
        class MockAPIError(Exception):
            pass

        mock_openai_client.chat.completions.create.side_effect = MockAPIError("API error")

        with pytest.raises(ParseError, match="Failed to get response from OpenAI: API error"):
            provider.complete("system", "user", 60)

    def test_generic_error_handling(self, provider, mock_openai_client):
        """Test handling of unexpected errors."""
        mock_openai_client.chat.completions.create.side_effect = Exception("Unknown error")

        with pytest.raises(ParseError, match="Failed to get response from OpenAI: Unknown error"):
            provider.complete("system", "user", 60)

    @pytest.mark.parametrize(
        "prompt,expected_action,expected_attributes",
        [
            (
                '{"prompt": "convert video.mp4 to 720p"}',
                "convert",
                {"scale": "1280:720", "video_codec": "libx264", "audio_codec": "aac"},
            ),
            (
                '{"prompt": "extract audio from video.mp4"}',
                "extract_audio",
                {"inputs": ["test.mp4"]},
            ),
            (
                '{"prompt": "trim video.mp4"}',
                "trim",
                {"start": "00:00:00", "duration": 30.0},
            ),
            (
                '{"prompt": "create thumbnail from video.mp4"}',
                "thumbnail",
                {"start": "00:00:10"},
            ),
            ('{"prompt": "compress video.mp4"}', "compress", {"crf": 28}),
        ],
    )
    def test_mock_response_generation(self, provider, prompt, expected_action, expected_attributes):
        """Test mock response generation for different operations."""
        result = provider._get_mock_response("system", prompt)
        data = json.loads(result)

        assert data["action"] == expected_action
        for key, value in expected_attributes.items():
            assert data[key] == value

    def test_mock_response_unknown_operation(self, provider):
        """Test mock response for unknown operations."""
        result = provider._get_mock_response("system", '{"prompt": "unknown operation"}')
        data = json.loads(result)

        assert data["action"] == "convert"
        assert data["video_codec"] == "libx264"
        assert data["audio_codec"] == "aac"

    def test_mock_response_invalid_json(self, provider):
        """Test mock response with malformed input."""
        result = provider._get_mock_response("system", "invalid json")
        data = json.loads(result)

        assert data["action"] == "convert"
        assert data["video_codec"] == "libx264"


class TestLLMClient:
    """Test the main LLM client functionality."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock LLM provider."""
        return Mock(spec=LLMProvider)

    @pytest.fixture
    def client(self, mock_provider):
        """Create an LLM client with mock provider."""
        return LLMClient(mock_provider)

    def test_initialization(self, mock_provider):
        """Test client initialization."""
        client = LLMClient(mock_provider)
        assert client.provider == mock_provider

    @patch("ai_ffmpeg_cli.io_utils.sanitize_user_input")
    def test_successful_parsing(self, mock_sanitize, client, mock_provider):
        """Test successful natural language parsing."""
        # Setup mocks
        mock_sanitize.return_value = "convert test.mp4"
        mock_provider.complete.return_value = '{"action": "convert", "inputs": ["test.mp4"]}'

        # Test parsing
        result = client.parse("convert test.mp4", {}, timeout=60)

        # Verify results
        assert isinstance(result, FfmpegIntent)
        assert result.action == Action.convert
        assert str(result.inputs[0]) == "test.mp4"

    @pytest.mark.parametrize(
        "invalid_input,expected_error",
        [
            ("", "Empty or invalid prompt"),
            ("   ", "Empty or invalid prompt"),
        ],
    )
    @patch("ai_ffmpeg_cli.io_utils.sanitize_user_input")
    def test_empty_input_handling(
        self, mock_sanitize, client, mock_provider, invalid_input, expected_error
    ):
        """Test handling of empty or whitespace-only input."""
        mock_sanitize.return_value = invalid_input

        with pytest.raises(ParseError, match=expected_error):
            client.parse(invalid_input, {}, timeout=60)

    @patch("ai_ffmpeg_cli.io_utils.sanitize_user_input")
    def test_json_parsing_failure(self, mock_sanitize, client, mock_provider):
        """Test handling of invalid JSON from LLM."""
        mock_sanitize.return_value = "convert test.mp4"
        mock_provider.complete.return_value = "invalid json"

        with pytest.raises(ParseError, match="Failed to parse LLM response as JSON"):
            client.parse("convert test.mp4", {}, timeout=60)

    @patch("ai_ffmpeg_cli.io_utils.sanitize_user_input")
    def test_validation_failure(self, mock_sanitize, client, mock_provider):
        """Test handling of schema validation errors."""
        mock_sanitize.return_value = "convert test.mp4"
        mock_provider.complete.return_value = '{"invalid": "schema"}'

        with pytest.raises(ParseError, match="Failed to validate parsed intent"):
            client.parse("convert test.mp4", {}, timeout=60)

    @patch("ai_ffmpeg_cli.io_utils.sanitize_user_input")
    def test_retry_mechanism_success(self, mock_sanitize, client, mock_provider):
        """Test successful retry after initial failure."""
        mock_sanitize.return_value = "convert test.mp4"
        # First call fails, second succeeds
        mock_provider.complete.side_effect = [
            "invalid json",
            '{"action": "convert", "inputs": ["test.mp4"]}',
        ]

        result = client.parse("convert test.mp4", {}, timeout=60)

        assert isinstance(result, FfmpegIntent)
        assert result.action == Action.convert
        assert mock_provider.complete.call_count == 2

    @pytest.mark.parametrize(
        "retry_exception,expected_error",
        [
            (
                json.JSONDecodeError("Invalid", "", 0),
                "Failed to parse LLM response as JSON",
            ),
            (
                ValidationError.from_exception_data("test", []),
                "Failed to validate parsed intent",
            ),
            (ParseError("Provider error"), "Provider error"),
            (OSError("Network error"), "Network error"),
        ],
    )
    @patch("ai_ffmpeg_cli.io_utils.sanitize_user_input")
    def test_retry_failure_scenarios(
        self, mock_sanitize, client, mock_provider, retry_exception, expected_error
    ):
        """Test various retry failure scenarios."""
        mock_sanitize.return_value = "convert test.mp4"
        mock_provider.complete.side_effect = ["invalid json", retry_exception]

        with pytest.raises(ParseError, match=expected_error):
            client.parse("convert test.mp4", {}, timeout=60)

    @pytest.mark.parametrize(
        "timeout_value,expected_timeout",
        [
            (None, 60),  # Default timeout
            (120, 120),  # Custom timeout
        ],
    )
    @patch("ai_ffmpeg_cli.io_utils.sanitize_user_input")
    def test_timeout_handling(
        self, mock_sanitize, client, mock_provider, timeout_value, expected_timeout
    ):
        """Test timeout parameter handling."""
        mock_sanitize.return_value = "convert test.mp4"
        mock_provider.complete.return_value = '{"action": "convert", "inputs": ["test.mp4"]}'

        client.parse("convert test.mp4", {}, timeout=timeout_value)

        # Verify timeout was passed correctly
        call_args = mock_provider.complete.call_args
        assert call_args.kwargs["timeout"] == expected_timeout


class TestIntegrationScenarios:
    """Test realistic integration scenarios with mocked OpenAI provider."""

    @pytest.fixture
    def integration_client(self):
        """Create a client with mocked OpenAI provider for integration testing."""
        with patch("ai_ffmpeg_cli.llm_client.OpenAIProvider") as mock_provider_class:
            mock_provider = mock_provider_class.return_value
            # Mock successful responses for different actions
            mock_responses = {
                "convert video.mp4 to 720p": '{"action": "convert", "inputs": ["video.mp4"], "scale": "1280:720"}',
                "extract audio from video.mp4": '{"action": "extract_audio", "inputs": ["video.mp4"]}',
                "trim video.mp4": '{"action": "trim", "inputs": ["video.mp4"], "start": "00:00:00", "duration": 30.0}',
            }

            def mock_complete(system, user, timeout):
                # Extract prompt from user payload
                import json

                user_data = json.loads(user)
                prompt = user_data.get("prompt", "")
                return mock_responses.get(prompt, '{"action": "convert", "inputs": ["test.mp4"]}')

            mock_provider.complete.side_effect = mock_complete
            return LLMClient(mock_provider)

    @pytest.mark.parametrize(
        "prompt,expected_action",
        [
            ("convert video.mp4 to 720p", Action.convert),
            ("extract audio from video.mp4", Action.extract_audio),
            ("trim video.mp4", Action.trim),
        ],
    )
    @pytest.mark.e2e
    def test_end_to_end_parsing(self, integration_client, prompt, expected_action):
        """Test end-to-end parsing with mocked responses."""
        result = integration_client.parse(prompt, {})

        assert isinstance(result, FfmpegIntent)
        assert result.action == expected_action
