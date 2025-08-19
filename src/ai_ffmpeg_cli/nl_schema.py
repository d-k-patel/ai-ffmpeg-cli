"""Natural language schema definitions for ai-ffmpeg-cli.

This module defines the core data structures used for parsing and representing
user intents in natural language form. It provides Pydantic models for type
safety and validation, along with automatic data coercion for common patterns.

Key components:
- Action enum: Supported ffmpeg operations
- FfmpegIntent: Main intent representation with validation
- CommandEntry/CommandPlan: Execution plan structures
- Automatic timestamp conversion and list coercion
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path  # noqa: TC003  # Path needed at runtime for Pydantic models

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


def _seconds_to_timestamp(value: float | int | str) -> str:
    """Convert numeric seconds to HH:MM:SS[.ms] timestamp format.

    Handles conversion from various numeric formats to ffmpeg-compatible
    timestamp strings. Supports milliseconds precision for precise seeking.

    Args:
        value: Seconds as float, int, or string representation

    Returns:
        str: Timestamp in HH:MM:SS or HH:MM:SS.mmm format

    Examples:
        >>> _seconds_to_timestamp(65.5)
        '00:01:05.500'
        >>> _seconds_to_timestamp(3661)
        '01:01:01'
    """
    try:
        seconds_float = float(value)
    except Exception:
        return str(value)
    total_ms = int(round(seconds_float * 1000))
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    if ms:
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    return f"{h:02d}:{m:02d}:{s:02d}"


class Action(str, Enum):
    """Supported ffmpeg operations for natural language processing.

    Each action corresponds to a specific ffmpeg operation with predefined
    argument patterns and output file handling.
    """

    convert = "convert"  # General format conversion
    extract_audio = "extract_audio"  # Extract audio track to separate file
    remove_audio = "remove_audio"  # Remove audio track from video
    trim = "trim"  # Cut video to specific time range
    segment = "segment"  # Extract segment (alias for trim)
    thumbnail = "thumbnail"  # Extract single frame as image
    frames = "frames"  # Extract multiple frames at specified FPS
    compress = "compress"  # Compress with quality settings
    overlay = "overlay"  # Overlay image/video on top of video


class FfmpegIntent(BaseModel):
    """Parsed user intent for ffmpeg operations.

    Represents a complete user request after natural language processing.
    Includes action type, input files, parameters, and validation rules.

    Key features:
    - Automatic list coercion for single inputs/filters
    - Timestamp conversion for start/end times
    - Action-specific validation rules
    - Support for glob patterns and extra flags
    """

    action: Action
    inputs: list[Path] = Field(default_factory=list)
    output: Path | None = None
    video_codec: str | None = None
    audio_codec: str | None = None
    filters: list[str] = Field(default_factory=list)
    start: str | None = None
    end: str | None = None
    duration: float | None = None
    scale: str | None = None
    bitrate: str | None = None
    crf: int | None = None
    overlay_path: Path | None = None
    overlay_xy: str | None = None
    fps: str | None = None
    glob: str | None = None
    extra_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_lists(cls, values: object) -> object:
        """Pre-validate data coercion for common patterns.

        Converts single values to lists and numeric timestamps to strings
        before Pydantic validation. This allows flexible input formats
        while maintaining type safety.

        Args:
            values: Raw input values before validation

        Returns:
            object: Coerced values ready for validation
        """
        if not isinstance(values, dict):
            return values
        # inputs: allow scalar -> [scalar] for single file operations
        inputs = values.get("inputs")
        if inputs is not None and not isinstance(inputs, list):
            values["inputs"] = [inputs]
        # filters: allow scalar -> [str(scalar)] for single filter
        filters = values.get("filters")
        if filters is not None and not isinstance(filters, list):
            values["filters"] = [str(filters)]
        # extra_flags: allow scalar -> [str(scalar)] for single flag
        extra_flags = values.get("extra_flags")
        if extra_flags is not None and not isinstance(extra_flags, list):
            values["extra_flags"] = [str(extra_flags)]

        # start/end: allow numeric seconds -> HH:MM:SS[.ms] for convenience
        if "start" in values and not isinstance(values.get("start"), str):
            values["start"] = _seconds_to_timestamp(values["start"])
        if "end" in values and not isinstance(values.get("end"), str):
            values["end"] = _seconds_to_timestamp(values["end"])
        return values

    @model_validator(mode="after")
    def _validate(self) -> FfmpegIntent:
        """Post-validation checks for action-specific requirements.

        Ensures that required parameters are present for each action type
        and that incompatible combinations are caught early.

        Returns:
            FfmpegIntent: Validated intent object

        Raises:
            ValueError: If validation rules are violated
        """
        if self.action == Action.overlay and not self.overlay_path:
            raise ValueError("overlay requires overlay_path")

        if self.action in {Action.trim, Action.segment} and not (
            self.duration or self.end or self.start
        ):
            raise ValueError("trim/segment requires start+end or duration")

        if self.action in {Action.convert, Action.compress} and not self.inputs:
            raise ValueError("convert/compress requires at least one input")

        if self.action == Action.extract_audio and not self.inputs:
            raise ValueError("extract_audio requires an input file")

        # Ensure incompatible combos are caught
        if self.action == Action.thumbnail and self.fps:
            raise ValueError("thumbnail is incompatible with fps; use frames action")

        return self


class CommandEntry(BaseModel):
    """Single ffmpeg command execution unit.

    Represents one ffmpeg command with its input, output, and arguments.
    Supports multiple input files for operations like overlay.
    """

    input: Path
    output: Path
    args: list[str] = Field(default_factory=list)
    extra_inputs: list[Path] = Field(default_factory=list)


class CommandPlan(BaseModel):
    """Complete execution plan for ffmpeg operations.

    Contains a human-readable summary and list of commands to execute.
    Used for preview, confirmation, and batch execution.
    """

    summary: str
    entries: list[CommandEntry]
