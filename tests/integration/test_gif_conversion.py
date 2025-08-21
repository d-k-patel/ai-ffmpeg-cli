"""Integration tests for GIF conversion functionality."""

import pytest

from ai_ffmpeg_cli.intent_models import Action
from ai_ffmpeg_cli.intent_models import FfmpegIntent
from ai_ffmpeg_cli.intent_router import route_intent


class TestGifConversion:
    """Test GIF conversion functionality."""

    def test_gif_conversion_intent_creation(self):
        """Test that GIF conversion creates the correct intent."""
        intent_data = {
            "action": "convert",
            "inputs": ["/path/to/test.mp4"],
            "filters": "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        }

        intent = FfmpegIntent(**intent_data)

        assert intent.action == Action.convert
        assert intent.filters == [
            "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        ]
        assert len(intent.inputs) == 1
        assert str(intent.inputs[0]) == "/path/to/test.mp4"

    def test_format_convert_requires_format_parameter(self):
        """Test that format_convert action requires format parameter."""
        # This should fail
        intent_data = {
            "action": "format_convert",
            "inputs": ["/path/to/test.mp4"],
            # Missing format parameter
        }

        with pytest.raises(ValueError, match="format_convert requires format parameter"):
            FfmpegIntent(**intent_data)

    def test_format_convert_with_format_parameter(self):
        """Test that format_convert works with format parameter."""
        intent_data = {
            "action": "format_convert",
            "inputs": ["/path/to/test.mp4"],
            "format": "gif",
        }

        intent = FfmpegIntent(**intent_data)
        assert intent.action == Action.format_convert
        assert intent.format == "gif"

    def test_convert_action_does_not_require_format(self):
        """Test that convert action works without format parameter."""
        intent_data = {
            "action": "convert",
            "inputs": ["/path/to/test.mp4"],
            "filters": "fps=10,scale=320:-1:flags=lanczos",
        }

        intent = FfmpegIntent(**intent_data)
        assert intent.action == Action.convert
        assert intent.filters == ["fps=10,scale=320:-1:flags=lanczos"]

    def test_gif_conversion_routing(self, tmp_path):
        """Test that GIF conversion routes correctly."""
        input_path = tmp_path / "test.mp4"
        input_path.touch()

        intent = FfmpegIntent(
            action=Action.convert,
            inputs=[input_path],
            filters="fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        )

        plan = route_intent(intent, allowed_dirs=[tmp_path])

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert entry.input == input_path

        # Check that the filter chain contains the expected components
        filter_chain = " ".join(entry.args)
        assert "fps=10" in filter_chain
        assert "scale=320:-1" in filter_chain
        assert "palettegen" in filter_chain
        assert "paletteuse" in filter_chain

    def test_gif_conversion_with_output_directory(self, tmp_path):
        """Test GIF conversion with output directory."""
        input_path = tmp_path / "test.mp4"
        input_path.touch()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        intent = FfmpegIntent(
            action=Action.convert,
            inputs=[input_path],
            filters="fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        )

        plan = route_intent(intent, allowed_dirs=[tmp_path], output_dir=output_dir)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert entry.input == input_path
        assert entry.output.parent == output_dir
        assert entry.output.suffix == ".mp4"  # Default extension for convert action

    def test_gif_conversion_example_from_prompt(self):
        """Test the exact example from the updated system prompt."""
        intent_data = {
            "action": "convert",
            "inputs": ["/path/to/test.mp4"],
            "filters": "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        }

        intent = FfmpegIntent(**intent_data)

        assert intent.action == Action.convert
        assert "fps=10" in intent.filters[0]
        assert "scale=320:-1" in intent.filters[0]
        assert "palettegen" in intent.filters[0]
        assert "paletteuse" in intent.filters[0]
