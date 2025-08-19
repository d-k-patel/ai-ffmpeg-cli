"""Tests for confirm.py user interaction module."""

from unittest.mock import patch

import pytest

from ai_ffmpeg_cli.confirm import confirm_prompt


class TestConfirmPrompt:
    """Test confirm_prompt function."""

    def test_assume_yes_returns_true(self):
        """Test that assume_yes=True always returns True."""
        result = confirm_prompt("Continue?", default_yes=True, assume_yes=True)
        assert result is True

        result = confirm_prompt("Continue?", default_yes=False, assume_yes=True)
        assert result is True

    @patch("builtins.input")
    def test_yes_responses(self, mock_input):
        """Test various 'yes' responses."""
        yes_responses = ["y", "yes", "Y", "YES", "Yes"]

        for response in yes_responses:
            mock_input.return_value = response
            result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
            assert result is True

    @patch("builtins.input")
    def test_no_responses(self, mock_input):
        """Test various 'no' responses."""
        no_responses = ["n", "no", "N", "NO", "No", "anything_else"]

        for response in no_responses:
            mock_input.return_value = response
            result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
            assert result is False

    @patch("builtins.input")
    def test_empty_response_default_yes(self, mock_input):
        """Test empty response with default_yes=True."""
        mock_input.return_value = ""

        result = confirm_prompt("Continue?", default_yes=True, assume_yes=False)
        assert result is True

    @patch("builtins.input")
    def test_empty_response_default_no(self, mock_input):
        """Test empty response with default_yes=False."""
        mock_input.return_value = ""

        result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
        assert result is False

    @patch("builtins.input")
    def test_whitespace_response_default_yes(self, mock_input):
        """Test whitespace-only response with default_yes=True."""
        mock_input.return_value = "   "

        result = confirm_prompt("Continue?", default_yes=True, assume_yes=False)
        assert result is True

    @patch("builtins.input")
    def test_whitespace_response_default_no(self, mock_input):
        """Test whitespace-only response with default_yes=False."""
        mock_input.return_value = "   "

        result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
        assert result is False

    @patch("builtins.input")
    def test_eof_error_default_yes(self, mock_input):
        """Test EOFError with default_yes=True."""
        mock_input.side_effect = EOFError()

        result = confirm_prompt("Continue?", default_yes=True, assume_yes=False)
        assert result is True

    @patch("builtins.input")
    def test_eof_error_default_no(self, mock_input):
        """Test EOFError with default_yes=False."""
        mock_input.side_effect = EOFError()

        result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
        assert result is False

    @patch("builtins.input")
    def test_case_insensitive_responses(self, mock_input):
        """Test that responses are case insensitive."""
        # Mixed case responses
        mixed_responses = [
            ("yEs", True),
            ("nO", False),
            ("Y", True),
            ("n", False),
        ]

        for response, expected in mixed_responses:
            mock_input.return_value = response
            result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
            assert result is expected

    @patch("builtins.input")
    def test_response_stripped(self, mock_input):
        """Test that responses are properly stripped of whitespace."""
        responses_with_whitespace = [
            ("  yes  ", True),
            ("\tn\t", False),
            (" Y ", True),
            ("  no  ", False),
        ]

        for response, expected in responses_with_whitespace:
            mock_input.return_value = response
            result = confirm_prompt("Continue?", default_yes=False, assume_yes=False)
            assert result is expected

    @patch("builtins.input")
    def test_question_formats(self, mock_input):
        """Test different question formats."""
        mock_input.return_value = "yes"

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

    @patch("builtins.input")
    def test_default_parameters(self, mock_input):
        """Test function with default parameters."""
        mock_input.return_value = "yes"

        # Test with minimal parameters - should use defaults
        result = confirm_prompt("Continue?", assume_yes=False)
        assert result is True

        # Test with assume_yes=True to avoid input
        result = confirm_prompt("Continue?", assume_yes=True)
        assert result is True
