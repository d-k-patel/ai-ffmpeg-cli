from __future__ import annotations

from enum import Enum
from pathlib import Path  # noqa: TC003  # Path needed at runtime for Pydantic models

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


def _seconds_to_timestamp(value: float | int | str) -> str:
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
    convert = "convert"
    extract_audio = "extract_audio"
    remove_audio = "remove_audio"
    trim = "trim"
    segment = "segment"
    thumbnail = "thumbnail"
    frames = "frames"
    compress = "compress"
    overlay = "overlay"


class FfmpegIntent(BaseModel):
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
        if not isinstance(values, dict):
            return values
        # inputs: allow scalar -> [scalar]
        inputs = values.get("inputs")
        if inputs is not None and not isinstance(inputs, list):
            values["inputs"] = [inputs]
        # filters: allow scalar -> [str(scalar)]
        filters = values.get("filters")
        if filters is not None and not isinstance(filters, list):
            values["filters"] = [str(filters)]
        # extra_flags: allow scalar -> [str(scalar)]
        extra_flags = values.get("extra_flags")
        if extra_flags is not None and not isinstance(extra_flags, list):
            values["extra_flags"] = [str(extra_flags)]

        # start/end: allow numeric seconds -> HH:MM:SS[.ms]
        if "start" in values and not isinstance(values.get("start"), str):
            values["start"] = _seconds_to_timestamp(values["start"])
        if "end" in values and not isinstance(values.get("end"), str):
            values["end"] = _seconds_to_timestamp(values["end"])
        return values

    @model_validator(mode="after")
    def _validate(self) -> FfmpegIntent:
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
    input: Path
    output: Path
    args: list[str] = Field(default_factory=list)
    extra_inputs: list[Path] = Field(default_factory=list)


class CommandPlan(BaseModel):
    summary: str
    entries: list[CommandEntry]
