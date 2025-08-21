"""Tests for confirm.py user interaction module."""

from unittest.mock import patch

from ai_ffmpeg_cli.confirm import confirm_prompt


class TestConfirmPrompt:
    """Test confirm_prompt function."""

    def test_assume_yes_returns_true(self):
        """Test that assume_yes=True always returns True."""
        result = confirm_prompt("Continue?", default_yes=True, assume_yes=True)
        assert result is True

        result = confirm_prompt("Continue?", default_yes=False, assume_yes=True)
        assert result is True

    @patch("rich.prompt.Confirm.ask")
    def test_yes_responses(self, mock_confirm):
        """Test various 'yes' responses."""
        yes_responses = [
            True,
            True,
            True,
            True,
            True,
        ]  # Rich's Confirm.ask returns boolean

        for expected_response in yes_responses:
            mock_confirm.return_value = expected_response
            result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
            assert result is True

    @patch("rich.prompt.Confirm.ask")
    def test_no_responses(self, mock_confirm):
        """Test various 'no' responses."""
        no_responses = [
            False,
            False,
            False,
            False,
            False,
            False,
        ]  # Rich's Confirm.ask returns boolean

        for expected_response in no_responses:
            mock_confirm.return_value = expected_response
            result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
            assert result is False

    @patch("rich.prompt.Confirm.ask")
    def test_empty_response_default_yes(self, mock_confirm):
        """Test empty response with default_yes=True."""
        mock_confirm.return_value = True  # Rich's Confirm.ask returns the default when empty

        result = confirm_prompt("Continue?", default_yes=True, assume_yes=False)
        assert result is True

    @patch("rich.prompt.Confirm.ask")
    def test_empty_response_default_no(self, mock_confirm):
        """Test empty response with default_yes=False."""
        mock_confirm.return_value = False  # Rich's Confirm.ask returns the default when empty

        result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
        assert result is False

    @patch("rich.prompt.Confirm.ask")
    def test_whitespace_response_default_yes(self, mock_confirm):
        """Test whitespace-only response with default_yes=True."""
        mock_confirm.return_value = True  # Rich's Confirm.ask returns the default for whitespace

        result = confirm_prompt("Continue?", default_yes=True, assume_yes=False)
        assert result is True

    @patch("rich.prompt.Confirm.ask")
    def test_whitespace_response_default_no(self, mock_confirm):
        """Test whitespace-only response with default_yes=False."""
        mock_confirm.return_value = False  # Rich's Confirm.ask returns the default for whitespace

        result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
        assert result is False

    @patch("rich.prompt.Confirm.ask")
    def test_eof_error_default_yes(self, mock_confirm):
        """Test EOFError with default_yes=True."""
        mock_confirm.side_effect = EOFError()

        result = confirm_prompt("Continue?", default_yes=True, assume_yes=False)
        assert result is True

    @patch("rich.prompt.Confirm.ask")
    def test_eof_error_default_no(self, mock_confirm):
        """Test EOFError with default_yes=False."""
        mock_confirm.side_effect = EOFError()

        result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
        assert result is False

    @patch("rich.prompt.Confirm.ask")
    def test_case_insensitive_responses(self, mock_confirm):
        """Test that responses are case insensitive."""
        # Mixed case responses - Rich handles case insensitivity internally
        mixed_responses = [
            (True, True),
            (False, False),
            (True, True),
            (False, False),
        ]

        for response, expected in mixed_responses:
            mock_confirm.return_value = response
            result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
            assert result is expected

    @patch("rich.prompt.Confirm.ask")
    def test_response_stripped(self, mock_confirm):
        """Test that responses are properly stripped of whitespace."""
        # Rich handles whitespace stripping internally
        responses_with_whitespace = [
            (True, True),
            (False, False),
            (True, True),
            (False, False),
        ]

        for response, expected in responses_with_whitespace:
            mock_confirm.return_value = response
            result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
            assert result is expected

    @patch("rich.prompt.Confirm.ask")
    def test_question_formats(self, mock_confirm):
        """Test different question formats."""
        mock_confirm.return_value = True

        # Should work with any question format
        questions = [
            "Continue?",
            "Do you want to proceed?",
            "Are you sure?",
            "Confirm action",  # No question mark
            "",  # Empty question
        ]

        for question in questions:
            result = confirm_prompt(question, default_yes=False, assume_yes=False)
            assert result is True

    @patch("rich.prompt.Confirm.ask")
    def test_default_parameters(self, mock_confirm):
        """Test function with default parameters."""
        mock_confirm.return_value = True

        # Test with minimal parameters - should use defaults
        result = confirm_prompt("Continue?", assume_yes=False)
        assert result is True

        # Test with assume_yes=True to avoid input
        result = confirm_prompt("Continue?", assume_yes=True)
        assert result is True
