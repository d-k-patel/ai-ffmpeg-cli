"""Tests for output directory functionality."""

import os
from pathlib import Path
from unittest.mock import patch

from ai_ffmpeg_cli.config import AppConfig
from ai_ffmpeg_cli.intent_models import Action
from ai_ffmpeg_cli.intent_models import FfmpegIntent
from ai_ffmpeg_cli.intent_router import _derive_output_name


class TestOutputDirectory:
    """Test output directory configuration and functionality."""

    def test_output_directory_default(self):
        """Test that output directory defaults to 'aiclip'."""
        config = AppConfig()
        assert config.output_directory == "aiclip"

    def test_output_directory_from_env(self, tmp_path):
        """Test that output directory can be set from environment variable."""
        custom_output = tmp_path / "custom_output"
        with patch.dict(os.environ, {"AICLIP_OUTPUT_DIR": str(custom_output)}):
            from ai_ffmpeg_cli.config import load_config

            config = load_config()
            assert config.output_directory == str(custom_output.absolute())
            assert custom_output.exists()

    def test_output_directory_validation_creates_directory(self, tmp_path):
        """Test that output directory validation creates directory if it doesn't exist."""
        output_dir = tmp_path / "new_output"
        _ = AppConfig(output_directory=str(output_dir))

        # Directory should be created
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_output_directory_validation_existing_directory(self, tmp_path):
        """Test that output directory validation works with existing directory."""
        output_dir = tmp_path / "existing_output"
        output_dir.mkdir()

        config = AppConfig(output_directory=str(output_dir))
        assert config.output_directory == str(output_dir.absolute())

    def test_output_directory_fallback(self):
        """Test that output directory falls back to current directory if invalid."""
        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            config = AppConfig(output_directory="/invalid/path")
            # Should fall back to current directory
            assert config.output_directory == os.getcwd()


class TestDeriveOutputName:
    """Test output name derivation with output directory."""

    def test_derive_output_name_with_output_dir(self, tmp_path):
        """Test that output names are placed in the specified output directory."""
        input_path = Path("input.mp4")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        intent = FfmpegIntent(inputs=[input_path], action=Action.convert, scale="1280:720")

        output_path = _derive_output_name(input_path, intent, output_dir)

        assert output_path.parent == output_dir
        assert output_path.name == "input_converted.mp4"

    def test_derive_output_name_without_output_dir(self, tmp_path):
        """Test that output names use input directory when no output dir specified."""
        input_path = tmp_path / "input.mp4"
        input_path.touch()

        intent = FfmpegIntent(inputs=[input_path], action=Action.extract_audio)

        output_path = _derive_output_name(input_path, intent)

        assert output_path.parent == input_path.parent
        assert output_path.name == "input.mp3"

    def test_derive_output_name_with_specified_output(self, tmp_path):
        """Test that specified output paths are respected but moved to output directory."""
        input_path = Path("input.mp4")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        intent = FfmpegIntent(
            inputs=[input_path], action=Action.convert, output=Path("custom_output.mp4")
        )

        output_path = _derive_output_name(input_path, intent, output_dir)

        assert output_path.parent == output_dir
        assert output_path.name == "custom_output.mp4"

    def test_derive_output_name_various_actions(self, tmp_path):
        """Test output name derivation for various actions with output directory."""
        input_path = Path("video.mp4")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        test_cases = [
            (Action.extract_audio, "video.mp3"),
            (Action.thumbnail, "thumbnail.png"),
            (Action.frames, "video_frame_%04d.png"),
            (Action.remove_audio, "video_mute.mp4"),
            (Action.compress, "video_converted.mp4"),
        ]

        for action, expected_name in test_cases:
            intent = FfmpegIntent(inputs=[input_path], action=action)
            output_path = _derive_output_name(input_path, intent, output_dir)

            assert output_path.parent == output_dir
            assert output_path.name == expected_name

    def test_derive_output_name_trim_action(self, tmp_path):
        """Test output name derivation for trim action with required parameters."""
        input_path = Path("video.mp4")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        intent = FfmpegIntent(
            inputs=[input_path], action=Action.trim, start="00:00:10", end="00:00:20"
        )

        output_path = _derive_output_name(input_path, intent, output_dir)
        assert output_path.parent == output_dir
        assert output_path.name == "clip.mp4"

    def test_derive_output_name_overlay_action(self, tmp_path):
        """Test output name derivation for overlay action with required parameters."""
        input_path = Path("video.mp4")
        overlay_path = Path("overlay.png")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        intent = FfmpegIntent(inputs=[input_path], action=Action.overlay, overlay_path=overlay_path)

        output_path = _derive_output_name(input_path, intent, output_dir)
        assert output_path.parent == output_dir
        assert output_path.name == "video_overlay.mp4"
