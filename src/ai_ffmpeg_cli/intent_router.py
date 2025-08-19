"""Intent routing and command plan generation for ai-ffmpeg-cli.

This module translates parsed user intents (FfmpegIntent) into executable
command plans (CommandPlan) with security validation and output path derivation.

Key responsibilities:
- Security validation of input paths and glob patterns
- Automatic output filename generation based on action type
- ffmpeg argument construction for different operations
- Command plan assembly with proper input/output mapping

Security features:
- Path traversal prevention
- Directory restriction for glob expansion
- Unsafe path rejection with logging
"""

from __future__ import annotations

from pathlib import Path

from .errors import BuildError
from .io_utils import expand_globs
from .nl_schema import Action
from .nl_schema import CommandEntry
from .nl_schema import CommandPlan
from .nl_schema import FfmpegIntent


def _derive_output_name(input_path: Path, intent: FfmpegIntent) -> Path:
    """Derive output filename based on input path and action type.

    Generates appropriate output filenames for different ffmpeg operations.
    Uses explicit output path if provided, otherwise creates action-specific names.

    Args:
        input_path: Path to the input file
        intent: Parsed user intent containing action and optional output

    Returns:
        Path: Output file path with appropriate extension and naming
    """
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


def route_intent(intent: FfmpegIntent, allowed_dirs: list[Path] | None = None) -> CommandPlan:
    """Route FfmpegIntent to CommandPlan with security validation.

    Translates user intent into executable ffmpeg commands with comprehensive
    security checks. Handles glob expansion, path validation, and argument
    construction for all supported operations.

    Args:
        intent: Parsed user intent containing action, inputs, and parameters
        allowed_dirs: List of directories allowed for glob expansion (defaults to cwd)

    Returns:
        CommandPlan: Execution plan with validated commands and summary

    Raises:
        BuildError: If intent cannot be routed, contains unsafe operations,
                   or no valid input files are found
    """
    # Expand any glob patterns provided with security validation
    derived_inputs: list[Path] = list(intent.inputs)
    if intent.glob:
        # Use secure glob expansion with allowed directories
        if allowed_dirs is None:
            allowed_dirs = [Path.cwd()]  # Default to current directory
        globbed = expand_globs([intent.glob], allowed_dirs)
        derived_inputs.extend(globbed)

    # Validate all input paths for security
    from .io_utils import is_safe_path

    validated_inputs = []
    for input_path in derived_inputs:
        if is_safe_path(input_path, allowed_dirs):
            validated_inputs.append(input_path)
        else:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Unsafe path rejected: {input_path}")

    if not validated_inputs:
        raise BuildError(
            "No safe input files found. Please ensure: "
            "(1) input files exist in the current directory, "
            "(2) file paths are correct and safe, "
            "(3) no path traversal attempts (e.g., ../), "
            "and (4) glob patterns match existing files. "
            "Try 'ls' to check available files."
        )

    derived_inputs = validated_inputs

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
            # -to is more precise for seeking, -t is for duration limiting
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
    """Build human-readable summary of the command plan.

    Creates a concise description of what the command plan will do,
    including action type, file count, and key parameters.

    Args:
        intent: Original user intent with action and parameters
        entries: List of command entries to be executed

    Returns:
        str: Human-readable summary of the operation
    """
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
