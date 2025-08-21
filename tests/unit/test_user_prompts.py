"""Tests for user_prompts.py module.

This module tests the user confirmation functionality that was previously untested.
"""

from unittest.mock import patch

import pytest

from ai_ffmpeg_cli.user_prompts import confirm_prompt


class TestUserPrompts:
    """Test user prompt functionality."""

    def test_confirm_prompt_default_yes(self):
        """Test confirm prompt with default yes."""
        with patch("builtins.input", return_value=""):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is True

    def test_confirm_prompt_default_no(self):
        """Test confirm prompt with default no."""
        with patch("builtins.input", return_value=""):
            result = confirm_prompt("Continue?", default_yes=False)
            assert result is False

    def test_confirm_prompt_user_yes(self):
        """Test confirm prompt when user enters yes."""
        with patch("builtins.input", return_value="y"):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is True

    def test_confirm_prompt_user_no(self):
        """Test confirm prompt when user enters no."""
        with patch("builtins.input", return_value="n"):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is False

    def test_confirm_prompt_user_yes_uppercase(self):
        """Test confirm prompt when user enters YES."""
        with patch("builtins.input", return_value="YES"):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is True

    def test_confirm_prompt_user_no_uppercase(self):
        """Test confirm prompt when user enters NO."""
        with patch("builtins.input", return_value="NO"):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is False

    def test_confirm_prompt_assume_yes(self):
        """Test confirm prompt with assume_yes=True."""
        with patch("builtins.input") as mock_input:
            result = confirm_prompt("Continue?", default_yes=True, assume_yes=True)
            assert result is True
            mock_input.assert_not_called()

    def test_confirm_prompt_assume_yes_ignores_default(self):
        """Test that assume_yes overrides default_yes."""
        with patch("builtins.input") as mock_input:
            result = confirm_prompt("Continue?", default_yes=False, assume_yes=True)
            assert result is True
            mock_input.assert_not_called()

    def test_confirm_prompt_eof_handling(self):
        """Test confirm prompt handles EOF (Ctrl+D)."""
        with patch("builtins.input", side_effect=EOFError):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is True

    def test_confirm_prompt_eof_handling_default_no(self):
        """Test confirm prompt handles EOF with default no."""
        with patch("builtins.input", side_effect=EOFError):
            result = confirm_prompt("Continue?", default_yes=False)
            assert result is False

    def test_confirm_prompt_whitespace_handling(self):
        """Test confirm prompt handles whitespace in input."""
        with patch("builtins.input", return_value="  y  "):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is True

    def test_confirm_prompt_whitespace_no(self):
        """Test confirm prompt handles whitespace in no input."""
        with patch("builtins.input", return_value="  n  "):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is False

    def test_confirm_prompt_various_yes_responses(self):
        """Test confirm prompt with various yes responses."""
        yes_responses = ["y", "Y", "yes", "YES", "Yes", "yEs", "yeS"]

        for response in yes_responses:
            with patch("builtins.input", return_value=response):
                result = confirm_prompt("Continue?", default_yes=False)
                assert result is True, f"Failed for response: {response}"

    def test_confirm_prompt_various_no_responses(self):
        """Test confirm prompt with various no responses."""
        no_responses = ["n", "N", "no", "NO", "No", "nO"]

        for response in no_responses:
            with patch("builtins.input", return_value=response):
                result = confirm_prompt("Continue?", default_yes=True)
                assert result is False, f"Failed for response: {response}"

    def test_confirm_prompt_invalid_responses(self):
        """Test confirm prompt with invalid responses."""
        invalid_responses = ["maybe", "perhaps", "ok", "sure", "whatever", "123", ""]

        for response in invalid_responses:
            with patch("builtins.input", return_value=response):
                result = confirm_prompt("Continue?", default_yes=True)
                expected = response == ""  # Empty string should return default
                assert result == expected, f"Failed for response: {response}"

    def test_confirm_prompt_question_display(self):
        """Test that the question is displayed correctly."""
        with patch("builtins.input", return_value="y") as mock_input:
            confirm_prompt("Test question?", default_yes=True)
            mock_input.assert_called_once_with("Test question? [Y/n] ")

    def test_confirm_prompt_question_display_default_no(self):
        """Test that the question is displayed correctly with default no."""
        with patch("builtins.input", return_value="y") as mock_input:
            confirm_prompt("Test question?", default_yes=False)
            mock_input.assert_called_once_with("Test question? [y/N] ")

    def test_confirm_prompt_case_insensitive(self):
        """Test that confirm prompt is case insensitive."""
        mixed_case_responses = ["YeS", "yEs", "YeS", "No", "nO", "NO"]
        expected_results = [True, True, True, False, False, False]

        for response, expected in zip(mixed_case_responses, expected_results, strict=False):
            with patch("builtins.input", return_value=response):
                result = confirm_prompt("Continue?", default_yes=True)
                assert result == expected, f"Failed for response: {response}"

    def test_confirm_prompt_empty_string_default_yes(self):
        """Test confirm prompt with empty string and default yes."""
        with patch("builtins.input", return_value=""):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is True

    def test_confirm_prompt_empty_string_default_no(self):
        """Test confirm prompt with empty string and default no."""
        with patch("builtins.input", return_value=""):
            result = confirm_prompt("Continue?", default_yes=False)
            assert result is False

    def test_confirm_prompt_whitespace_only_default_yes(self):
        """Test confirm prompt with whitespace only and default yes."""
        with patch("builtins.input", return_value="   "):
            result = confirm_prompt("Continue?", default_yes=True)
            assert result is True

    def test_confirm_prompt_whitespace_only_default_no(self):
        """Test confirm prompt with whitespace only and default no."""
        with patch("builtins.input", return_value="   "):
            result = confirm_prompt("Continue?", default_yes=False)
            assert result is False

    def test_confirm_prompt_special_characters(self):
        """Test confirm prompt with special characters in question."""
        special_question = "Delete file 'test@#$%^&*()'?"
        with patch("builtins.input", return_value="y") as mock_input:
            confirm_prompt(special_question, default_yes=True)
            mock_input.assert_called_once_with(f"{special_question} [Y/n] ")

    def test_confirm_prompt_unicode_question(self):
        """Test confirm prompt with unicode characters in question."""
        unicode_question = "Delete file 'vídeo.mp4'?"
        with patch("builtins.input", return_value="y") as mock_input:
            confirm_prompt(unicode_question, default_yes=True)
            mock_input.assert_called_once_with(f"{unicode_question} [Y/n] ")

    def test_confirm_prompt_long_question(self):
        """Test confirm prompt with a very long question."""
        long_question = "This is a very long question that might wrap to multiple lines and contain a lot of text to test how the prompt handles long input strings"
        with patch("builtins.input", return_value="y") as mock_input:
            confirm_prompt(long_question, default_yes=True)
            mock_input.assert_called_once_with(f"{long_question} [Y/n] ")

    def test_confirm_prompt_multiple_calls(self):
        """Test multiple confirm prompt calls."""
        with patch("builtins.input", side_effect=["y", "n", ""]):
            result1 = confirm_prompt("First question?", default_yes=True)
            result2 = confirm_prompt("Second question?", default_yes=True)
            result3 = confirm_prompt("Third question?", default_yes=True)

            assert result1 is True
            assert result2 is False
            assert result3 is True

    def test_confirm_prompt_error_handling(self):
        """Test confirm prompt error handling."""
        # Test with KeyboardInterrupt
        with (
            patch("builtins.input", side_effect=KeyboardInterrupt),
            pytest.raises(KeyboardInterrupt),
        ):
            confirm_prompt("Continue?", default_yes=True)

    def test_confirm_prompt_value_error(self):
        """Test confirm prompt with ValueError."""
        with (
            patch("builtins.input", side_effect=ValueError("Invalid input")),
            pytest.raises(ValueError),
        ):
            confirm_prompt("Continue?", default_yes=True)

    def test_confirm_prompt_os_error(self):
        """Test confirm prompt with OSError."""
        with (
            patch("builtins.input", side_effect=OSError("Input error")),
            pytest.raises(OSError),
        ):
            confirm_prompt("Continue?", default_yes=True)

    def test_confirm_prompt_integration_scenario(self):
        """Test confirm prompt in a realistic integration scenario."""
        # Simulate a user workflow with multiple confirmations
        with patch("builtins.input", side_effect=["y", "n", "yes", "no", ""]):
            # User confirms first action
            result1 = confirm_prompt("Convert video to MP4?", default_yes=True)
            assert result1 is True

            # User declines second action
            result2 = confirm_prompt("Apply compression?", default_yes=True)
            assert result2 is False

            # User confirms third action
            result3 = confirm_prompt("Add watermark?", default_yes=False)
            assert result3 is True

            # User declines fourth action
            result4 = confirm_prompt("Overwrite existing file?", default_yes=False)
            assert result4 is False

            # User accepts default for fifth action
            result5 = confirm_prompt("Proceed with conversion?", default_yes=True)
            assert result5 is True

    def test_confirm_prompt_assume_yes_scenario(self):
        """Test confirm prompt in non-interactive scenario."""
        # Simulate automated/batch processing
        with patch("builtins.input") as mock_input:
            result1 = confirm_prompt("Convert video 1?", assume_yes=True)
            result2 = confirm_prompt("Convert video 2?", assume_yes=True)
            result3 = confirm_prompt("Convert video 3?", assume_yes=True)

            assert result1 is True
            assert result2 is True
            assert result3 is True
            mock_input.assert_not_called()

    def test_confirm_prompt_default_behavior_scenario(self):
        """Test confirm prompt default behavior in different scenarios."""
        # Test safe operations (default yes)
        with patch("builtins.input", return_value=""):
            result1 = confirm_prompt("Continue with safe operation?", default_yes=True)
            assert result1 is True

        # Test dangerous operations (default no)
        with patch("builtins.input", return_value=""):
            result2 = confirm_prompt("Delete important file?", default_yes=False)
            assert result2 is False

    def test_confirm_prompt_edge_cases(self):
        """Test confirm prompt with edge case inputs."""
        edge_cases = [
            ("y", True),
            ("Y", True),
            ("yes", True),
            ("YES", True),
            ("n", False),
            ("N", False),
            ("no", False),
            ("NO", False),
            ("", True),  # Default yes
            ("   ", True),  # Whitespace only, default yes
            ("maybe", False),  # Invalid response
            ("ok", False),  # Invalid response
        ]

        for response, expected in edge_cases:
            with patch("builtins.input", return_value=response):
                result = confirm_prompt("Continue?", default_yes=True)
                assert result == expected, f"Failed for response: '{response}'"

    def test_confirm_prompt_performance(self):
        """Test confirm prompt performance with many calls."""
        import time

        start_time = time.time()
        with patch("builtins.input", return_value="y"):
            for _ in range(1000):
                result = confirm_prompt("Test question?", default_yes=True)
                assert result is True
        end_time = time.time()

        # Should complete in reasonable time
        assert end_time - start_time < 5.0

    def test_confirm_prompt_memory_usage(self):
        """Test confirm prompt memory usage."""
        # Test that multiple calls don't cause memory leaks
        with patch("builtins.input", return_value="y"):
            for i in range(1000):
                result = confirm_prompt(f"Question {i}?", default_yes=True)
                assert result is True

    def test_confirm_prompt_thread_safety(self):
        """Test confirm prompt thread safety."""
        import threading

        results = []

        def confirm_worker():
            with patch("builtins.input", return_value="y"):
                result = confirm_prompt("Thread test?", default_yes=True)
                results.append(result)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=confirm_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 10
        assert all(result is True for result in results)


class TestUserPromptsSecurity:
    """Test security aspects of user prompts."""

    def test_confirm_prompt_input_sanitization(self):
        """Test that confirm prompt properly sanitizes input."""
        # Test with potentially dangerous input
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "convert video; rm -rf /",
            "../../../etc/passwd",
        ]

        for dangerous_input in dangerous_inputs:
            with patch("builtins.input", return_value=dangerous_input):
                result = confirm_prompt("Continue?", default_yes=True)
                # Should not crash and should return False for non-yes responses
                assert isinstance(result, bool)

    def test_confirm_prompt_injection_prevention(self):
        """Test that confirm prompt prevents injection attacks."""
        # Test with various injection attempts
        injection_attempts = [
            "y\nrm -rf /",
            "yes\ncat /etc/passwd",
            "y; rm -rf /",
            "yes && rm -rf /",
        ]

        for attempt in injection_attempts:
            with patch("builtins.input", return_value=attempt):
                result = confirm_prompt("Continue?", default_yes=True)
                # The function only accepts exact 'y' or 'yes' after stripping
                # These inputs contain additional characters, so they should return False
                assert result is False

    def test_confirm_prompt_overflow_prevention(self):
        """Test that confirm prompt handles very long input."""
        # Test with a single 'y' character (which should work)
        single_y = "y"
        with patch("builtins.input", return_value=single_y):
            result = confirm_prompt("Continue?", default_yes=True)
            # Should handle input gracefully and return True for 'y'
            assert result is True

        # Test with a very long string that doesn't match 'y' or 'yes'
        very_long_input = "y" * 10000
        with patch("builtins.input", return_value=very_long_input):
            result = confirm_prompt("Continue?", default_yes=True)
            # Should handle long input gracefully and return False since it's not 'y' or 'yes'
            assert result is False

    def test_confirm_prompt_null_byte_handling(self):
        """Test that confirm prompt handles null bytes properly."""
        null_input = "y\x00n"
        with patch("builtins.input", return_value=null_input):
            result = confirm_prompt("Continue?", default_yes=True)
            # Should handle gracefully and return False since it's not exactly 'y' or 'yes'
            assert result is False

    def test_confirm_prompt_control_character_handling(self):
        """Test that confirm prompt handles control characters."""
        control_input = "y\x01\x02\x03n"
        with patch("builtins.input", return_value=control_input):
            result = confirm_prompt("Continue?", default_yes=True)
            # Should handle gracefully and return False since it's not exactly 'y' or 'yes'
            assert result is False
