"""Comprehensive tests for nl_schema.py data models and validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_ffmpeg_cli.nl_schema import (
    Action,
    CommandEntry,
    CommandPlan,
    FfmpegIntent,
    _seconds_to_timestamp,
)


class TestSecondsToTimestamp:
    """Test timestamp conversion function."""

    def test_convert_integer_seconds(self):
        """Test converting integer seconds."""
        assert _seconds_to_timestamp(0) == "00:00:00"
        assert _seconds_to_timestamp(30) == "00:00:30"
        assert _seconds_to_timestamp(90) == "00:01:30"
        assert _seconds_to_timestamp(3661) == "01:01:01"

    def test_convert_float_seconds(self):
        """Test converting float seconds."""
        assert _seconds_to_timestamp(30.5) == "00:00:30.500"
        assert _seconds_to_timestamp(90.123) == "00:01:30.123"
        assert _seconds_to_timestamp(0.001) == "00:00:00.001"
        assert _seconds_to_timestamp(3661.999) == "01:01:01.999"

    def test_convert_string_seconds(self):
        """Test converting string seconds."""
        assert _seconds_to_timestamp("30") == "00:00:30"
        assert _seconds_to_timestamp("30.5") == "00:00:30.500"
        assert _seconds_to_timestamp("90") == "00:01:30"

    def test_convert_invalid_string(self):
        """Test converting invalid string."""
        # Should return the string as-is if can't convert
        assert _seconds_to_timestamp("invalid") == "invalid"
        assert _seconds_to_timestamp("00:30:00") == "00:30:00"  # Already formatted

    def test_convert_large_values(self):
        """Test converting large time values."""
        # 25 hours, 30 minutes, 45 seconds
        large_seconds = 25 * 3600 + 30 * 60 + 45
        assert _seconds_to_timestamp(large_seconds) == "25:30:45"

    def test_convert_edge_cases(self):
        """Test edge cases."""
        assert _seconds_to_timestamp(0.0) == "00:00:00"
        assert _seconds_to_timestamp(59.999) == "00:00:59.999"
        assert _seconds_to_timestamp(60) == "00:01:00"


class TestAction:
    """Test Action enum."""

    def test_action_values(self):
        """Test all action values."""
        expected_actions = {
            "convert",
            "extract_audio",
            "remove_audio",
            "trim",
            "segment",
            "thumbnail",
            "frames",
            "compress",
            "overlay",
        }
        actual_actions = {action.value for action in Action}
        assert actual_actions == expected_actions

    def test_action_string_representation(self):
        """Test action string representation."""
        assert Action.convert.value == "convert"
        assert Action.extract_audio.value == "extract_audio"
        assert Action.overlay.value == "overlay"


class TestFfmpegIntent:
    """Test FfmpegIntent model validation."""

    def test_basic_intent_creation(self):
        """Test creating basic intent."""
        intent = FfmpegIntent(action=Action.convert, inputs=[Path("input.mp4")])

        assert intent.action == Action.convert
        assert len(intent.inputs) == 1
        assert intent.inputs[0] == Path("input.mp4")
        assert intent.output is None
        assert intent.filters == []
        assert intent.extra_flags == []

    def test_intent_with_all_fields(self):
        """Test creating intent with all fields."""
        intent = FfmpegIntent(
            action=Action.convert,
            inputs=[Path("input.mp4")],
            output=Path("output.mp4"),
            video_codec="libx264",
            audio_codec="aac",
            filters=["scale=720:480"],
            start="00:00:10",
            end="00:01:00",
            duration=50.0,
            scale="1280:720",
            bitrate="2000k",
            crf=23,
            overlay_path=Path("logo.png"),
            overlay_xy="10:10",
            fps="30",
            glob="*.mp4",
            extra_flags=["-y"],
        )

        assert intent.action == Action.convert
        assert intent.video_codec == "libx264"
        assert intent.audio_codec == "aac"
        assert intent.filters == ["scale=720:480"]
        assert intent.start == "00:00:10"
        assert intent.end == "00:01:00"
        assert intent.duration == 50.0
        assert intent.scale == "1280:720"
        assert intent.bitrate == "2000k"
        assert intent.crf == 23
        assert intent.overlay_path == Path("logo.png")
        assert intent.overlay_xy == "10:10"
        assert intent.fps == "30"
        assert intent.glob == "*.mp4"
        assert intent.extra_flags == ["-y"]

    def test_input_coercion_scalar_to_list(self):
        """Test that scalar inputs are coerced to list."""
        intent = FfmpegIntent(
            action=Action.convert,
            inputs=Path("single_input.mp4"),  # Single Path, not list
        )

        assert isinstance(intent.inputs, list)
        assert len(intent.inputs) == 1
        assert intent.inputs[0] == Path("single_input.mp4")

    def test_filters_coercion_scalar_to_list(self):
        """Test that scalar filters are coerced to list."""
        intent = FfmpegIntent(
            action=Action.convert,
            inputs=[Path("input.mp4")],
            filters="scale=720:480",  # Single string, not list
        )

        assert isinstance(intent.filters, list)
        assert intent.filters == ["scale=720:480"]

    def test_extra_flags_coercion_scalar_to_list(self):
        """Test that scalar extra_flags are coerced to list."""
        intent = FfmpegIntent(
            action=Action.convert,
            inputs=[Path("input.mp4")],
            extra_flags="-y",  # Single string, not list
        )

        assert isinstance(intent.extra_flags, list)
        assert intent.extra_flags == ["-y"]

    def test_timestamp_coercion_start(self):
        """Test that numeric start times are converted to timestamps."""
        intent = FfmpegIntent(
            action=Action.trim,
            inputs=[Path("input.mp4")],
            start=30.5,  # Numeric seconds
        )

        assert intent.start == "00:00:30.500"

    def test_timestamp_coercion_end(self):
        """Test that numeric end times are converted to timestamps."""
        intent = FfmpegIntent(
            action=Action.trim, inputs=[Path("input.mp4")], end=90  # Numeric seconds
        )

        assert intent.end == "00:01:30"

    def test_overlay_validation_success(self):
        """Test successful overlay validation."""
        intent = FfmpegIntent(
            action=Action.overlay,
            inputs=[Path("video.mp4")],
            overlay_path=Path("logo.png"),
        )

        assert intent.action == Action.overlay
        assert intent.overlay_path == Path("logo.png")

    def test_overlay_validation_missing_path(self):
        """Test overlay validation fails without overlay_path."""
        with pytest.raises(ValidationError, match="overlay requires overlay_path"):
            FfmpegIntent(
                action=Action.overlay,
                inputs=[Path("video.mp4")],
                # Missing overlay_path
            )

    def test_trim_validation_with_duration(self):
        """Test trim validation with duration."""
        intent = FfmpegIntent(
            action=Action.trim, inputs=[Path("input.mp4")], duration=30.0
        )

        assert intent.duration == 30.0

    def test_trim_validation_with_start_end(self):
        """Test trim validation with start and end."""
        intent = FfmpegIntent(
            action=Action.trim,
            inputs=[Path("input.mp4")],
            start="00:00:10",
            end="00:01:00",
        )

        assert intent.start == "00:00:10"
        assert intent.end == "00:01:00"

    def test_trim_validation_missing_timing(self):
        """Test trim validation fails without timing information."""
        with pytest.raises(ValidationError, match="trim/segment requires"):
            FfmpegIntent(
                action=Action.trim,
                inputs=[Path("input.mp4")],
                # Missing duration, start, and end
            )

    def test_segment_validation_success(self):
        """Test successful segment validation."""
        intent = FfmpegIntent(
            action=Action.segment,
            inputs=[Path("input.mp4")],
            start="00:00:10",
            duration=30.0,
        )

        assert intent.action == Action.segment
        assert intent.start == "00:00:10"
        assert intent.duration == 30.0

    def test_segment_validation_missing_timing(self):
        """Test segment validation fails without timing."""
        with pytest.raises(ValidationError, match="trim/segment requires"):
            FfmpegIntent(action=Action.segment, inputs=[Path("input.mp4")])

    def test_convert_validation_success(self):
        """Test successful convert validation."""
        intent = FfmpegIntent(action=Action.convert, inputs=[Path("input.mp4")])

        assert intent.action == Action.convert
        assert len(intent.inputs) == 1

    def test_convert_validation_no_inputs(self):
        """Test convert validation fails without inputs."""
        with pytest.raises(
            ValidationError, match="convert/compress requires at least one input"
        ):
            FfmpegIntent(action=Action.convert, inputs=[])

    def test_compress_validation_success(self):
        """Test successful compress validation."""
        intent = FfmpegIntent(
            action=Action.compress, inputs=[Path("input.mp4")], crf=28
        )

        assert intent.action == Action.compress
        assert intent.crf == 28

    def test_compress_validation_no_inputs(self):
        """Test compress validation fails without inputs."""
        with pytest.raises(
            ValidationError, match="convert/compress requires at least one input"
        ):
            FfmpegIntent(action=Action.compress, inputs=[])

    def test_extract_audio_validation_success(self):
        """Test successful extract_audio validation."""
        intent = FfmpegIntent(action=Action.extract_audio, inputs=[Path("input.mp4")])

        assert intent.action == Action.extract_audio

    def test_extract_audio_validation_no_inputs(self):
        """Test extract_audio validation fails without inputs."""
        with pytest.raises(
            ValidationError, match="extract_audio requires an input file"
        ):
            FfmpegIntent(action=Action.extract_audio, inputs=[])

    def test_thumbnail_fps_incompatibility(self):
        """Test that thumbnail and fps are incompatible."""
        with pytest.raises(ValidationError, match="thumbnail is incompatible with fps"):
            FfmpegIntent(action=Action.thumbnail, inputs=[Path("input.mp4")], fps="30")

    def test_intent_with_glob_pattern(self):
        """Test intent with glob pattern."""
        # For convert action, we need at least one input, so let's use a different action
        intent = FfmpegIntent(
            action=Action.thumbnail,  # This doesn't require inputs validation
            inputs=[Path("video.mp4")],
            glob="*.mov",
        )

        assert intent.glob == "*.mov"
        assert len(intent.inputs) == 1


class TestCommandEntry:
    """Test CommandEntry model."""

    def test_basic_command_entry(self):
        """Test creating basic command entry."""
        entry = CommandEntry(input=Path("input.mp4"), output=Path("output.mp4"))

        assert entry.input == Path("input.mp4")
        assert entry.output == Path("output.mp4")
        assert entry.args == []
        assert entry.extra_inputs == []

    def test_command_entry_with_args(self):
        """Test command entry with arguments."""
        entry = CommandEntry(
            input=Path("input.mp4"),
            output=Path("output.mp4"),
            args=["-c:v", "libx264", "-c:a", "aac"],
        )

        assert entry.args == ["-c:v", "libx264", "-c:a", "aac"]

    def test_command_entry_with_extra_inputs(self):
        """Test command entry with extra inputs."""
        entry = CommandEntry(
            input=Path("video.mp4"),
            output=Path("output.mp4"),
            extra_inputs=[Path("logo.png"), Path("audio.mp3")],
        )

        assert len(entry.extra_inputs) == 2
        assert Path("logo.png") in entry.extra_inputs
        assert Path("audio.mp3") in entry.extra_inputs


class TestCommandPlan:
    """Test CommandPlan model."""

    def test_basic_command_plan(self):
        """Test creating basic command plan."""
        entry = CommandEntry(
            input=Path("input.mp4"), output=Path("output.mp4"), args=["-c:v", "libx264"]
        )

        plan = CommandPlan(summary="Convert 1 file to MP4 H264", entries=[entry])

        assert plan.summary == "Convert 1 file to MP4 H264"
        assert len(plan.entries) == 1
        assert plan.entries[0] == entry

    def test_command_plan_multiple_entries(self):
        """Test command plan with multiple entries."""
        entries = [
            CommandEntry(input=Path("input1.mp4"), output=Path("output1.mp4")),
            CommandEntry(input=Path("input2.mp4"), output=Path("output2.mp4")),
        ]

        plan = CommandPlan(summary="Convert 2 files to MP4", entries=entries)

        assert len(plan.entries) == 2
        assert plan.entries[0].input == Path("input1.mp4")
        assert plan.entries[1].input == Path("input2.mp4")

    def test_empty_command_plan(self):
        """Test command plan with no entries."""
        plan = CommandPlan(summary="No operations", entries=[])

        assert plan.summary == "No operations"
        assert plan.entries == []


class TestModelIntegration:
    """Test integration between models."""

    def test_full_workflow_models(self):
        """Test complete workflow with all models."""
        # Create intent
        intent = FfmpegIntent(
            action=Action.overlay,
            inputs=[Path("video.mp4")],
            overlay_path=Path("logo.png"),
            overlay_xy="10:10",
        )

        # Create command entry
        entry = CommandEntry(
            input=Path("video.mp4"),
            output=Path("output.mp4"),
            args=["-filter_complex", "overlay=10:10"],
            extra_inputs=[Path("logo.png")],
        )

        # Create plan
        plan = CommandPlan(summary="Overlay logo.png on 1 file(s)", entries=[entry])

        # Verify all models work together
        assert intent.action == Action.overlay
        assert entry.extra_inputs[0] == intent.overlay_path
        assert len(plan.entries) == 1
        assert plan.entries[0] == entry
