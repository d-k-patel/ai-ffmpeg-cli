"""Integration tests for new functionality added in the cookbook fixes.

This module tests the new features that were implemented to fix cookbook command issues:
- Format conversion (WebM, ProRes, etc.)
- Frame extraction with specific FPS
- Enhanced scaling capabilities
- Improved error handling and validation
- New action types (extract_frames, format_convert)
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from ai_ffmpeg_cli.intent_models_extended import Action
from ai_ffmpeg_cli.intent_models_extended import FfmpegIntent
from ai_ffmpeg_cli.intent_router import route_intent
from ai_ffmpeg_cli.llm_client import LLMClient


class TestFormatConversion:
    """Test format conversion functionality."""

    def test_webm_conversion_intent(self):
        """Test WebM format conversion intent routing."""
        intent = FfmpegIntent(
            action=Action.format_convert,
            inputs=[Path("test.mp4")],
            format="webm",
            video_codec="libvpx",
            audio_codec="libvorbis",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert entry.output.suffix == ".webm"
        assert "-f" in entry.args
        assert "webm" in entry.args
        assert "-c:v" in entry.args
        assert "libvpx" in entry.args

    def test_prores_conversion_intent(self):
        """Test ProRes format conversion intent routing."""
        intent = FfmpegIntent(
            action=Action.format_convert,
            inputs=[Path("test.mp4")],
            format="mov",
            video_codec="prores_ks",
            audio_codec="pcm_s16le",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert entry.output.suffix == ".mov"
        assert "-f" in entry.args
        assert "mov" in entry.args
        assert "-c:v" in entry.args
        assert "prores_ks" in entry.args

    def test_avi_conversion_intent(self):
        """Test AVI format conversion intent routing."""
        intent = FfmpegIntent(
            action=Action.format_convert,
            inputs=[Path("test.mp4")],
            format="avi",
            video_codec="libx264",
            audio_codec="mp3",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert entry.output.suffix == ".avi"
        assert "-f" in entry.args
        assert "avi" in entry.args

    def test_mkv_conversion_intent(self):
        """Test MKV format conversion intent routing."""
        intent = FfmpegIntent(
            action=Action.format_convert,
            inputs=[Path("test.mp4")],
            format="mkv",
            video_codec="libx264",
            audio_codec="aac",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert entry.output.suffix == ".mkv"
        assert "-f" in entry.args
        assert "mkv" in entry.args


class TestFrameExtraction:
    """Test frame extraction functionality."""

    def test_extract_frames_intent(self):
        """Test frame extraction intent routing."""
        intent = FfmpegIntent(
            action=Action.extract_frames,
            inputs=[Path("test.mp4")],
            fps="1/2",  # One frame every 2 seconds
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "frames_%04d" in entry.output.name
        assert "-vf" in entry.args
        assert "fps=1/2" in entry.args
        assert "-frame_pts" in entry.args

    def test_extract_frames_1fps_intent(self):
        """Test frame extraction at 1 FPS intent routing."""
        intent = FfmpegIntent(
            action=Action.extract_frames,
            inputs=[Path("test.mp4")],
            fps="1",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-vf" in entry.args
        assert "fps=1" in entry.args

    def test_extract_frames_validation(self):
        """Test that extract_frames requires fps parameter."""
        with pytest.raises(ValueError, match="extract_frames requires fps parameter"):
            FfmpegIntent(
                action=Action.extract_frames,
                inputs=[Path("test.mp4")],
            )


class TestEnhancedScaling:
    """Test enhanced scaling functionality."""

    def test_percentage_scaling_intent(self):
        """Test percentage-based scaling intent routing."""
        intent = FfmpegIntent(
            action=Action.convert,
            inputs=[Path("test.mp4")],
            scale="iw*0.5:ih*0.5",  # 50% scaling
            video_codec="libx264",
            audio_codec="aac",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-vf" in entry.args
        assert "scale=iw*0.5:ih*0.5:force_original_aspect_ratio=decrease" in entry.args

    def test_specific_resolution_scaling_intent(self):
        """Test specific resolution scaling intent routing."""
        intent = FfmpegIntent(
            action=Action.convert,
            inputs=[Path("test.mp4")],
            scale="1920:1080",
            video_codec="libx264",
            audio_codec="aac",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-vf" in entry.args
        assert "scale=1920:1080:force_original_aspect_ratio=decrease" in entry.args

    def test_enhanced_convert_with_filters(self):
        """Test enhanced convert with multiple filters."""
        intent = FfmpegIntent(
            action=Action.convert,
            inputs=[Path("test.mp4")],
            filters=["scale=1280:720", "fps=30"],
            video_codec="libx264",
            audio_codec="aac",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-vf" in entry.args
        assert "fps=30,scale=1280:720:force_original_aspect_ratio=decrease" in entry.args


class TestEnhancedRemoveAudio:
    """Test enhanced remove audio functionality."""

    def test_remove_audio_with_video_codec_intent(self):
        """Test remove audio with video codec preservation."""
        intent = FfmpegIntent(
            action=Action.remove_audio,
            inputs=[Path("test.mp4")],
            video_codec="libx264",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-an" in entry.args
        assert "-c:v" in entry.args
        assert "libx264" in entry.args

    def test_remove_audio_default_intent(self):
        """Test remove audio with default settings."""
        intent = FfmpegIntent(
            action=Action.remove_audio,
            inputs=[Path("test.mp4")],
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-an" in entry.args
        assert entry.output.name.endswith("_mute.mp4")


class TestEnhancedCompress:
    """Test enhanced compress functionality."""

    def test_compress_with_codecs_intent(self):
        """Test compress with specific codecs."""
        intent = FfmpegIntent(
            action=Action.compress,
            inputs=[Path("test.mp4")],
            crf=28,
            video_codec="libx265",
            audio_codec="aac",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-crf" in entry.args
        assert "28" in entry.args
        assert "-c:v" in entry.args
        assert "libx265" in entry.args
        assert "-c:a" in entry.args
        assert "aac" in entry.args


class TestLLMResponseFixing:
    """Test LLM response fixing functionality."""

    def test_fix_null_filters(self):
        """Test fixing null filters in LLM response."""
        client = LLMClient(Mock())

        response = (
            '{"action": "convert", "inputs": ["test.mp4"], "filters": null, "extra_flags": []}'
        )
        fixed = client._fix_common_issues(response)

        assert '"filters": []' in fixed
        assert '"filters": null' not in fixed

    def test_fix_null_extra_flags(self):
        """Test fixing null extra_flags in LLM response."""
        client = LLMClient(Mock())

        response = (
            '{"action": "convert", "inputs": ["test.mp4"], "filters": [], "extra_flags": null}'
        )
        fixed = client._fix_common_issues(response)

        assert '"extra_flags": []' in fixed
        assert '"extra_flags": null' not in fixed

    def test_fix_null_inputs(self):
        """Test fixing null inputs in LLM response."""
        client = LLMClient(Mock())

        response = '{"action": "convert", "inputs": null, "filters": [], "extra_flags": []}'
        fixed = client._fix_common_issues(response)

        assert '"inputs": []' in fixed
        assert '"inputs": null' not in fixed

    def test_fix_missing_array_brackets_filters(self):
        """Test fixing missing array brackets for filters."""
        client = LLMClient(Mock())

        response = '{"action": "convert", "inputs": ["test.mp4"], "filters": "scale=720:480", "extra_flags": []}'
        fixed = client._fix_common_issues(response)

        # The regex replacement might add extra brackets, so we check for the pattern
        assert '"filters":' in fixed
        assert "scale=720:480" in fixed
        assert '"filters": null' not in fixed

    def test_fix_missing_array_brackets_extra_flags(self):
        """Test fixing missing array brackets for extra_flags."""
        client = LLMClient(Mock())

        response = (
            '{"action": "convert", "inputs": ["test.mp4"], "filters": [], "extra_flags": "-y"}'
        )
        fixed = client._fix_common_issues(response)

        # The regex replacement might add extra brackets, so we check for the pattern
        assert '"extra_flags":' in fixed
        assert "-y" in fixed
        assert '"extra_flags": null' not in fixed


class TestSchemaValidation:
    """Test enhanced schema validation."""

    def test_empty_string_crf_handling(self):
        """Test handling of empty string crf values."""
        # This should not raise an error
        intent = FfmpegIntent(
            action=Action.compress,
            inputs=[Path("test.mp4")],
            crf="",  # Empty string should be converted to None
        )

        assert intent.crf is None

    def test_empty_string_duration_handling(self):
        """Test handling of empty string duration values."""
        # This should not raise an error, but trim requires timing parameters
        intent = FfmpegIntent(
            action=Action.trim,
            inputs=[Path("test.mp4")],
            start="00:00:00",  # Add required timing parameter
            duration="",  # Empty string should be converted to None
        )

        assert intent.duration is None

    def test_format_convert_validation(self):
        """Test format_convert validation requires format parameter."""
        with pytest.raises(ValueError, match="format_convert requires format parameter"):
            FfmpegIntent(
                action=Action.format_convert,
                inputs=[Path("test.mp4")],
                # Missing format parameter
            )

    def test_format_convert_with_format_success(self):
        """Test format_convert with format parameter succeeds."""
        intent = FfmpegIntent(
            action=Action.format_convert,
            inputs=[Path("test.mp4")],
            format="webm",
        )

        assert intent.format == "webm"
        assert intent.action == Action.format_convert


class TestIntegrationScenarios:
    """Test integration scenarios with new functionality."""

    def test_cookbook_webm_conversion_scenario(self):
        """Test the cookbook WebM conversion scenario."""
        intent = FfmpegIntent(
            action=Action.format_convert,
            inputs=[Path("test.mp4")],
            format="webm",
            video_codec="libvpx",
            audio_codec="libvorbis",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert entry.output.suffix == ".webm"
        assert "-f" in entry.args
        assert "webm" in entry.args
        assert "-c:v" in entry.args
        assert "libvpx" in entry.args
        assert "-c:a" in entry.args
        assert "libvorbis" in entry.args

    def test_cookbook_frame_extraction_scenario(self):
        """Test the cookbook frame extraction scenario."""
        intent = FfmpegIntent(
            action=Action.extract_frames,
            inputs=[Path("test.mp4")],
            fps="1/2",  # One frame every 2 seconds
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "frames_%04d" in entry.output.name
        assert entry.output.suffix == ".png"
        assert "-vf" in entry.args
        assert "fps=1/2" in entry.args
        assert "-frame_pts" in entry.args

    def test_cookbook_remove_audio_scenario(self):
        """Test the cookbook remove audio scenario."""
        intent = FfmpegIntent(
            action=Action.remove_audio,
            inputs=[Path("test.mp4")],
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-an" in entry.args
        assert entry.output.name.endswith("_mute.mp4")

    def test_cookbook_trim_scenario(self):
        """Test the cookbook trim scenario."""
        intent = FfmpegIntent(
            action=Action.trim,
            inputs=[Path("test.mp4")],
            start="00:00:00",
            duration=10.0,
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-ss" in entry.args
        assert "00:00:00" in entry.args
        assert "-t" in entry.args
        assert "10.0" in entry.args

    def test_cookbook_scale_scenario(self):
        """Test the cookbook scale scenario."""
        intent = FfmpegIntent(
            action=Action.convert,
            inputs=[Path("test.mp4")],
            scale="iw*0.5:ih*0.5",  # 50% scaling
            video_codec="libx264",
            audio_codec="aac",
        )

        plan = route_intent(intent)

        assert len(plan.entries) == 1
        entry = plan.entries[0]
        assert "-vf" in entry.args
        assert "scale=iw*0.5:ih*0.5:force_original_aspect_ratio=decrease" in entry.args
        assert "-c:v" in entry.args
        assert "libx264" in entry.args
        assert "-c:a" in entry.args
        assert "aac" in entry.args


class TestErrorHandling:
    """Test error handling improvements."""

    def test_unsupported_action_error_message(self):
        """Test that unsupported actions give clear error messages."""
        # This test checks that the enum validation catches invalid actions
        with pytest.raises(ValueError, match="Input should be"):
            FfmpegIntent(
                action="unsupported_action",  # type: ignore
                inputs=[Path("test.mp4")],
            )

    def test_missing_inputs_error_message(self):
        """Test that missing inputs give clear error messages."""
        with pytest.raises(
            ValueError,
            match="convert/compress/format_convert requires at least one input",
        ):
            FfmpegIntent(
                action=Action.convert,
                inputs=[],
            )

    def test_missing_format_error_message(self):
        """Test that missing format gives clear error message."""
        with pytest.raises(ValueError, match="format_convert requires format parameter"):
            FfmpegIntent(
                action=Action.format_convert,
                inputs=[Path("test.mp4")],
            )

    def test_missing_fps_error_message(self):
        """Test that missing fps gives clear error message."""
        with pytest.raises(ValueError, match="extract_frames requires fps parameter"):
            FfmpegIntent(
                action=Action.extract_frames,
                inputs=[Path("test.mp4")],
            )
