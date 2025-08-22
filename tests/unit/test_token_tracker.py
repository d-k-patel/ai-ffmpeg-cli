"""Tests for token tracking functionality."""

from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

from ai_ffmpeg_cli.token_tracker import SessionTokenTracker
from ai_ffmpeg_cli.token_tracker import TokenTracker
from ai_ffmpeg_cli.token_tracker import TokenUsage


class TestTokenUsage:
    """Test cases for TokenUsage class."""

    def test_token_usage_creation(self):
        """Test creating a TokenUsage instance."""
        usage = TokenUsage(
            operation="test_operation",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        )

        assert usage.operation == "test_operation"
        assert usage.model == "gpt-4o"
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cost_estimate is None

    def test_token_usage_with_cost(self):
        """Test TokenUsage with cost estimate."""
        usage = TokenUsage(
            operation="test_operation",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_estimate=0.0025,
        )

        assert usage.total_cost_estimate == 0.0025

    def test_token_usage_timestamp(self):
        """Test that TokenUsage has a timestamp."""
        usage = TokenUsage(
            operation="test_operation",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        )

        assert isinstance(usage.timestamp, datetime)


class TestSessionTokenTracker:
    """Test cases for SessionTokenTracker class."""

    def test_session_creation(self):
        """Test creating a session tracker."""
        session = SessionTokenTracker(session_id="test123", model="gpt-4o")

        assert session.session_id == "test123"
        assert session.model == "gpt-4o"
        assert len(session.operations) == 0
        assert isinstance(session.start_time, datetime)

    def test_add_operation(self):
        """Test adding operations to session."""
        session = SessionTokenTracker(session_id="test123")
        usage = TokenUsage(
            operation="test_op",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        )

        session.add_operation(usage)
        assert len(session.operations) == 1
        assert session.operations[0] == usage

    def test_total_tokens_calculation(self):
        """Test total token calculations."""
        session = SessionTokenTracker(session_id="test123")

        # Add multiple operations
        session.add_operation(TokenUsage("op1", "gpt-4o", 100, 50, 150))
        session.add_operation(TokenUsage("op2", "gpt-4o", 200, 100, 300))

        assert session.total_input_tokens == 300
        assert session.total_output_tokens == 150
        assert session.total_tokens == 450

    def test_cost_calculation(self):
        """Test cost calculation with multiple operations."""
        session = SessionTokenTracker(session_id="test123")

        # Add operations with costs
        op1 = TokenUsage("op1", "gpt-4o", 100, 50, 150, cost_estimate=0.001)
        op2 = TokenUsage("op2", "gpt-4o", 200, 100, 300, cost_estimate=0.002)
        session.add_operation(op1)
        session.add_operation(op2)

        assert session.total_cost_estimate == 0.003

    def test_session_duration(self):
        """Test session duration calculation."""
        session = SessionTokenTracker(session_id="test123")

        # Duration should be a positive number
        assert session.session_duration >= 0


class TestTokenTracker:
    """Test cases for TokenTracker class."""

    def test_token_tracker_initialization(self):
        """Test TokenTracker initialization."""
        tracker = TokenTracker()

        assert tracker.current_session is None
        assert isinstance(tracker.encoding_cache, dict)
        assert len(tracker.encoding_cache) == 0

    def test_start_session(self):
        """Test starting a new session."""
        tracker = TokenTracker()
        tracker.start_session("test123", "gpt-4o")

        assert tracker.current_session is not None
        assert tracker.current_session.session_id == "test123"
        assert tracker.current_session.model == "gpt-4o"

    @patch("ai_ffmpeg_cli.token_tracker.tiktoken.get_encoding")
    def test_get_encoding_gpt4(self, mock_get_encoding):
        """Test getting encoding for GPT-4 model."""
        mock_encoding = MagicMock()
        mock_get_encoding.return_value = mock_encoding

        tracker = TokenTracker()
        encoding = tracker.get_encoding("gpt-4o")

        assert encoding == mock_encoding
        mock_get_encoding.assert_called_with("cl100k_base")

    @patch("ai_ffmpeg_cli.token_tracker.tiktoken.get_encoding")
    def test_get_encoding_gpt3(self, mock_get_encoding):
        """Test getting encoding for GPT-3 model."""
        mock_encoding = MagicMock()
        mock_get_encoding.return_value = mock_encoding

        tracker = TokenTracker()
        encoding = tracker.get_encoding("gpt-3")

        assert encoding == mock_encoding
        mock_get_encoding.assert_called_with("r50k_base")

    @patch("ai_ffmpeg_cli.token_tracker.tiktoken.get_encoding")
    def test_get_encoding_caching(self, mock_get_encoding):
        """Test that encodings are cached."""
        mock_encoding = MagicMock()
        mock_get_encoding.return_value = mock_encoding

        tracker = TokenTracker()

        # First call
        encoding1 = tracker.get_encoding("gpt-4o")
        # Second call should use cache
        encoding2 = tracker.get_encoding("gpt-4o")

        assert encoding1 == encoding2
        # Should only be called once due to caching
        mock_get_encoding.assert_called_once_with("cl100k_base")

    def test_count_tokens_empty(self):
        """Test counting tokens in empty text."""
        tracker = TokenTracker()
        count = tracker.count_tokens("", "gpt-4o")
        assert count == 0

    def test_count_tokens_with_text(self):
        """Test counting tokens in text."""
        tracker = TokenTracker()
        # Mock the encoding to return a known token count
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        tracker.encoding_cache["gpt-4o"] = mock_encoding

        count = tracker.count_tokens("Hello world", "gpt-4o")
        assert count == 5

    def test_track_operation(self):
        """Test tracking an operation."""
        tracker = TokenTracker()
        tracker.start_session("test123", "gpt-4o")

        # Mock encoding for token counting
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3]  # 3 tokens for input
        tracker.encoding_cache["gpt-4o"] = mock_encoding

        usage = tracker.track_operation(
            operation="test_op",
            model="gpt-4o",
            input_text="Hello",
            output_text="World",
            cost_estimate=0.001,
        )

        assert usage.operation == "test_op"
        assert usage.model == "gpt-4o"
        assert usage.input_tokens == 3
        assert usage.output_tokens == 3  # "World" also has 3 tokens
        assert usage.total_tokens == 6
        assert usage.cost_estimate == 0.001

        # Check that it was added to the session
        assert len(tracker.current_session.operations) == 1

    def test_track_operation_no_session(self):
        """Test tracking operation when no session exists."""
        tracker = TokenTracker()

        # Mock encoding
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2]
        tracker.encoding_cache["gpt-4o"] = mock_encoding

        tracker.track_operation(
            operation="test_op", model="gpt-4o", input_text="Hello", output_text="World"
        )

        # Should create a default session
        assert tracker.current_session is not None
        assert tracker.current_session.session_id == "default"
        assert len(tracker.current_session.operations) == 1

    def test_get_cost_estimate_gpt4o(self):
        """Test cost estimation for GPT-4o."""
        tracker = TokenTracker()
        cost = tracker.get_cost_estimate("gpt-4o", 1000, 500)

        # GPT-4o pricing: input $0.0025/1K, output $0.01/1K
        expected_cost = (1000 / 1000) * 0.0025 + (500 / 1000) * 0.01
        assert cost == expected_cost

    def test_get_cost_estimate_gpt35(self):
        """Test cost estimation for GPT-3.5-turbo."""
        tracker = TokenTracker()
        cost = tracker.get_cost_estimate("gpt-3.5-turbo", 1000, 500)

        # GPT-3.5-turbo pricing: input $0.0005/1K, output $0.0015/1K
        expected_cost = (1000 / 1000) * 0.0005 + (500 / 1000) * 0.0015
        assert cost == expected_cost

    def test_get_cost_estimate_unknown_model(self):
        """Test cost estimation for unknown model."""
        tracker = TokenTracker()
        cost = tracker.get_cost_estimate("unknown-model", 1000, 500)
        assert cost is None

    @patch("ai_ffmpeg_cli.token_tracker.console")
    def test_display_session_summary(self, mock_console):
        """Test displaying session summary."""
        tracker = TokenTracker()
        tracker.start_session("test123", "gpt-4o")

        # Add some operations
        tracker.track_operation("op1", "gpt-4o", "input1", "output1", 0.001)
        tracker.track_operation("op2", "gpt-4o", "input2", "output2", 0.002)

        tracker.display_session_summary()

        # Verify that console.print was called
        assert mock_console.print.called

    @patch("ai_ffmpeg_cli.token_tracker.console")
    def test_display_detailed_usage(self, mock_console):
        """Test displaying detailed usage."""
        tracker = TokenTracker()
        tracker.start_session("test123", "gpt-4o")

        # Add some operations
        tracker.track_operation("op1", "gpt-4o", "input1", "output1")
        tracker.track_operation("op2", "gpt-4o", "input2", "output2")

        tracker.display_detailed_usage()

        # Verify that console.print was called
        assert mock_console.print.called

    @patch("ai_ffmpeg_cli.token_tracker.console")
    def test_display_realtime_usage(self, mock_console):
        """Test displaying real-time usage."""
        tracker = TokenTracker()
        usage = TokenUsage(
            operation="test_op",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_estimate=0.001,
        )

        tracker.display_realtime_usage(usage)

        # Verify that console.print was called
        assert mock_console.print.called


# Note: get_terminal_width and center_text functions are tested in test_ascii_art.py
# since they are part of the ascii_art module
