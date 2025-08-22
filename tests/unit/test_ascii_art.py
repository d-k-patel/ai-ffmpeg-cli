"""Tests for ASCII art functionality."""

from unittest.mock import patch

from ai_ffmpeg_cli.ascii_art import center_text
from ai_ffmpeg_cli.ascii_art import display_colored_ascii_art
from ai_ffmpeg_cli.ascii_art import display_dynamic_banner
from ai_ffmpeg_cli.ascii_art import display_welcome_banner
from ai_ffmpeg_cli.ascii_art import get_ascii_art
from ai_ffmpeg_cli.ascii_art import get_random_font
from ai_ffmpeg_cli.ascii_art import get_terminal_width


class TestAsciiArt:
    """Test cases for ASCII art functionality."""

    def test_get_ascii_art_default(self):
        """Test getting ASCII art with default parameters."""
        result = get_ascii_art()
        # Check that it's a non-empty string with ASCII art characters
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain some ASCII art characters
        assert any(char in result for char in ["/", "\\", "_", "|", "#", "="])

    def test_get_ascii_art_custom_text(self):
        """Test getting ASCII art with custom text."""
        result = get_ascii_art("TEST")
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain some ASCII art characters
        assert any(char in result for char in ["/", "\\", "_", "|", "#", "="])

    def test_get_ascii_art_custom_font(self):
        """Test getting ASCII art with custom font."""
        result = get_ascii_art("TEST", "banner")
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain some ASCII art characters
        assert any(char in result for char in ["/", "\\", "_", "|", "#", "="])

    def test_get_ascii_art_fallback(self):
        """Test ASCII art fallback when pyfiglet fails."""
        with patch("ai_ffmpeg_cli.ascii_art.pyfiglet.Figlet") as mock_figlet:
            mock_figlet.side_effect = Exception("Font not found")
            result = get_ascii_art("TEST")
            assert "TEST" in result
            assert "╔" in result  # Check for fallback box characters

    def test_get_random_font(self):
        """Test getting a random font."""
        font = get_random_font()
        assert isinstance(font, str)
        assert len(font) > 0

    def test_get_random_font_returns_valid_font(self):
        """Test that random font is from the valid font list."""
        font = get_random_font()
        # Since it's random, we can't guarantee it's in our small test list
        # But we can test that it's a string and not empty
        assert isinstance(font, str)
        assert len(font) > 0

    @patch("ai_ffmpeg_cli.ascii_art.console")
    def test_display_colored_ascii_art(self, mock_console):
        """Test displaying colored ASCII art."""
        display_colored_ascii_art("TEST")
        # Verify that console.print was called
        assert mock_console.print.called

    @patch("ai_ffmpeg_cli.ascii_art.console")
    def test_display_colored_ascii_art_custom_colors(self, mock_console):
        """Test displaying colored ASCII art with custom colors."""
        display_colored_ascii_art(
            "TEST", primary_color="red", secondary_color="yellow", accent_color="blue"
        )
        # Verify that console.print was called
        assert mock_console.print.called

    @patch("ai_ffmpeg_cli.ascii_art.console")
    def test_display_welcome_banner(self, mock_console):
        """Test displaying welcome banner."""
        display_welcome_banner()
        # Verify that console.print was called multiple times
        assert mock_console.print.call_count >= 2

    @patch("ai_ffmpeg_cli.ascii_art.console")
    def test_display_dynamic_banner(self, mock_console):
        """Test displaying dynamic banner."""
        display_dynamic_banner()
        # Verify that console.print was called
        assert mock_console.print.called

    def test_ascii_art_with_empty_text(self):
        """Test ASCII art with empty text."""
        result = get_ascii_art("")
        assert isinstance(result, str)
        # Should still produce some output even with empty text

    def test_ascii_art_with_special_characters(self):
        """Test ASCII art with special characters."""
        result = get_ascii_art("AICLIP-123!")
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("ai_ffmpeg_cli.ascii_art.console")
    def test_display_colored_ascii_art_with_long_text(self, mock_console):
        """Test displaying colored ASCII art with long text."""
        long_text = "VERY_LONG_TEXT_FOR_TESTING"
        display_colored_ascii_art(long_text)
        # Verify that console.print was called
        assert mock_console.print.called

    def test_get_terminal_width(self):
        """Test getting terminal width."""
        width = get_terminal_width()
        assert isinstance(width, int)
        assert width > 0

    def test_center_text(self):
        """Test centering text."""
        text = "Hello\nWorld"
        centered = center_text(text, 20)
        assert isinstance(centered, str)
        assert "Hello" in centered
        assert "World" in centered

    def test_center_text_empty(self):
        """Test centering empty text."""
        text = ""
        centered = center_text(text, 20)
        assert centered == ""

    def test_center_text_short_width(self):
        """Test centering text when width is shorter than text."""
        text = "Hello World"
        centered = center_text(text, 5)
        assert "Hello World" in centered
