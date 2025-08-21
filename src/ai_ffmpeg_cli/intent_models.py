"""Intent models for ai-ffmpeg-cli.

This module defines the data models for representing ffmpeg intents
and command plans, including validation and type conversion logic.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path  # noqa: TC003  # Path needed at runtime for Pydantic models

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


def _seconds_to_timestamp(value: float | int | str) -> str:
    """Convert seconds to HH:MM:SS[.ms] timestamp format.

    Converts numeric seconds to ffmpeg-compatible timestamp format,
    handling both integer and float inputs.

    Args:
        value: Seconds as number or string

    Returns:
        Timestamp string in HH:MM:SS[.ms] format
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
    """Supported ffmpeg actions for intent processing."""

    convert = "convert"
    extract_audio = "extract_audio"
    remove_audio = "remove_audio"
    trim = "trim"
    segment = "segment"
    thumbnail = "thumbnail"
    frames = "frames"
    extract_frames = "extract_frames"
    compress = "compress"
    overlay = "overlay"
    format_convert = "format_convert"


class FfmpegIntent(BaseModel):
    """Represents a parsed ffmpeg intent with all parameters.

    This model captures the user's intent for ffmpeg operations,
    including action type, input/output files, and processing parameters.
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
    quality: str | None = None  # For quality settings
    format: str | None = None  # For format conversion

    @model_validator(mode="before")
    @classmethod
    def _coerce_lists(cls, values: object) -> object:
        """Pre-validate and coerce input values to proper types.

        Handles type conversion for lists and timestamp formatting
        before model validation.

        Args:
            values: Raw input values

        Returns:
            Processed values with proper types
        """
        if not isinstance(values, dict):
            return values
        # inputs: allow scalar -> [scalar] or None -> []
        inputs = values.get("inputs")
        if inputs is None:
            values["inputs"] = []
        elif not isinstance(inputs, list):
            values["inputs"] = [inputs]
        # filters: allow scalar -> [str(scalar)] or None -> []
        filters = values.get("filters")
        if filters is None:
            values["filters"] = []
        elif not isinstance(filters, list):
            values["filters"] = [str(filters)]
        # extra_flags: allow scalar -> [str(scalar)] or None -> []
        extra_flags = values.get("extra_flags")
        if extra_flags is None:
            values["extra_flags"] = []
        elif not isinstance(extra_flags, list):
            values["extra_flags"] = [str(extra_flags)]

        # start/end: allow numeric seconds -> HH:MM:SS[.ms]
        if "start" in values and not isinstance(values.get("start"), str):
            values["start"] = _seconds_to_timestamp(values["start"])
        if "end" in values and not isinstance(values.get("end"), str):
            values["end"] = _seconds_to_timestamp(values["end"])

        # fps: allow numeric values -> string
        if "fps" in values and not isinstance(values.get("fps"), str):
            values["fps"] = str(values["fps"])

        # glob: allow any value -> string or None
        if "glob" in values and values.get("glob") is not None:
            values["glob"] = str(values["glob"])

        return values

    @model_validator(mode="after")
    def _validate(self) -> FfmpegIntent:
        """Post-validate the intent for logical consistency.

        Ensures that required fields are present for each action type
        and that incompatible combinations are caught.

        Returns:
            Self if validation passes

        Raises:
            ValueError: When validation fails
        """
        if self.action == Action.overlay and not self.overlay_path:
            raise ValueError("overlay requires overlay_path")

        if self.action in {Action.trim, Action.segment} and not (
            self.duration or self.end or self.start
        ):
            raise ValueError("trim/segment requires start+end or duration")

        if (
            self.action in {Action.convert, Action.compress, Action.format_convert}
            and not self.inputs
        ):
            raise ValueError("convert/compress/format_convert requires at least one input")

        if self.action == Action.extract_audio and not self.inputs:
            raise ValueError("extract_audio requires an input file")

        # Add validation for new actions
        if self.action == Action.extract_frames and not self.fps:
            raise ValueError("extract_frames requires fps parameter")

        if self.action == Action.format_convert and not self.format:
            raise ValueError("format_convert requires format parameter")

        # Ensure incompatible combos are caught
        if self.action == Action.thumbnail and self.fps:
            raise ValueError("thumbnail is incompatible with fps; use frames action")

        return self


class CommandEntry(BaseModel):
    """Represents a single ffmpeg command with its parameters.

    Contains all information needed to execute a single ffmpeg command,
    including input/output files and command arguments.
    """

    input: Path
    output: Path
    args: list[str] = Field(default_factory=list)
    extra_inputs: list[Path] = Field(default_factory=list)


class CommandPlan(BaseModel):
    """Represents a complete plan of ffmpeg commands to execute.

    Contains a human-readable summary and a list of command entries
    that will be executed in sequence.
    """

    summary: str
    entries: list[CommandEntry]
