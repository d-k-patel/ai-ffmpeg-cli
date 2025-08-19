from __future__ import annotations

from typing import TYPE_CHECKING

from .errors import BuildError
from .io_utils import expand_globs
from .nl_schema import Action
from .nl_schema import CommandEntry
from .nl_schema import CommandPlan
from .nl_schema import FfmpegIntent

if TYPE_CHECKING:
    from pathlib import Path


def _derive_output_name(input_path: Path, intent: FfmpegIntent) -> Path:
    if intent.output:
        return intent.output
    stem = input_path.stem
    suffix = input_path.suffix
    if intent.action == Action.extract_audio:
        return input_path.with_suffix(".mp3")
    if intent.action == Action.thumbnail:
        return input_path.with_name("thumbnail.png")
    if intent.action == Action.frames:
        return input_path.with_name(f"{stem}_frame_%04d.png")
    if intent.action == Action.trim:
        return input_path.with_name("clip.mp4")
    if intent.action == Action.remove_audio:
        return input_path.with_name(f"{stem}_mute.mp4")
    if intent.action == Action.overlay:
        return input_path.with_name(f"{stem}_overlay.mp4")
    if intent.action in {Action.convert, Action.compress}:
        return input_path.with_suffix(".mp4")
    return input_path.with_suffix(suffix)


def route_intent(intent: FfmpegIntent) -> CommandPlan:
    # Expand any glob patterns provided
    derived_inputs: list[Path] = list(intent.inputs)
    if intent.glob:
        globbed = expand_globs([intent.glob])
        derived_inputs.extend(globbed)
    if not derived_inputs:
        raise BuildError(
            "No input files found. Please ensure: "
            "(1) input files exist in the current directory, "
            "(2) file paths are correct, "
            "or (3) glob patterns match existing files. "
            "Try 'ls' to check available files."
        )

    entries: list[CommandEntry] = []

    for inp in derived_inputs:
        output = _derive_output_name(inp, intent)
        args: list[str] = []

        if intent.action == Action.convert:
            if intent.scale:
                args.extend(["-vf", f"scale={intent.scale}"])
        elif intent.action == Action.extract_audio:
            args.extend(["-q:a", "0", "-map", "a"])
        elif intent.action == Action.remove_audio:
            args.extend(["-an"])
        elif intent.action == Action.trim:
            if intent.start:
                args.extend(["-ss", intent.start])
            # If end is provided, prefer -to; otherwise use duration if present
            if intent.end:
                args.extend(["-to", intent.end])
            elif intent.duration is not None:
                args.extend(["-t", str(intent.duration)])
        elif intent.action == Action.segment:
            # simplified: use start/end if provided, else duration
            if intent.start:
                args.extend(["-ss", intent.start])
            if intent.end:
                args.extend(["-to", intent.end])
            elif intent.duration is not None:
                args.extend(["-t", str(intent.duration)])
        elif intent.action == Action.thumbnail:
            if intent.start:
                args.extend(["-ss", intent.start])
            args.extend(["-vframes", "1"])
        elif intent.action == Action.frames:
            if intent.fps:
                args.extend(["-vf", f"fps={intent.fps}"])
        elif intent.action == Action.compress:
            # defaults in command builder
            if intent.crf is not None:
                args.extend(["-crf", str(intent.crf)])
        elif intent.action == Action.overlay:
            # include overlay input and optional xy; filter added in builder if not present
            if intent.overlay_path:
                # When overlay_xy provided, include filter here to override builder default
                if intent.overlay_xy:
                    args.extend(["-filter_complex", f"overlay={intent.overlay_xy}"])
                entries.append(
                    CommandEntry(
                        input=inp,
                        output=output,
                        args=args,
                        extra_inputs=[intent.overlay_path],
                    )
                )
                continue
        else:
            raise BuildError(
                f"Unsupported action: {intent.action}. "
                f"Supported actions are: convert, extract_audio, remove_audio, "
                f"trim, segment, thumbnail, frames, compress, overlay. "
                f"Please rephrase your request using supported operations."
            )

        entries.append(CommandEntry(input=inp, output=output, args=args))

    summary = _build_summary(intent, entries)
    return CommandPlan(summary=summary, entries=entries)


def _build_summary(intent: FfmpegIntent, entries: list[CommandEntry]) -> str:
    if intent.action == Action.convert:
        return f"Convert {len(entries)} file(s) to mp4 h264+aac with optional scale {intent.scale or '-'}"
    if intent.action == Action.extract_audio:
        return f"Extract audio from {len(entries)} file(s) to mp3"
    if intent.action == Action.trim:
        end_or_duration = (
            f"end={intent.end}" if intent.end else f"duration={intent.duration or '-'}"
        )
        return f"Trim {len(entries)} file(s) start={intent.start or '0'} {end_or_duration}"
    if intent.action == Action.thumbnail:
        return f"Thumbnail from {len(entries)} file(s) at {intent.start or '00:00:10'}"
    if intent.action == Action.overlay:
        return f"Overlay {intent.overlay_path} on {len(entries)} file(s)"
    if intent.action == Action.compress:
        return f"Compress {len(entries)} file(s) with libx265 CRF {intent.crf or 28}"
    if intent.action == Action.frames:
        return f"Extract frames from {len(entries)} file(s) with fps {intent.fps or '1/5'}"
    return f"Action {intent.action} on {len(entries)} file(s)"
