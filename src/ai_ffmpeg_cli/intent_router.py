"""Intent routing and command plan generation for ai-ffmpeg-cli.

This module handles the conversion of parsed ffmpeg intents into executable
command plans, including security validation and filter optimization.
"""

from __future__ import annotations

from pathlib import Path

from .custom_exceptions import BuildError
from .file_operations import expand_globs
from .intent_models import Action
from .intent_models import CommandEntry
from .intent_models import CommandPlan
from .intent_models import FfmpegIntent


def _validate_and_fix_scale_filter(scale_filter: str | None) -> str | None:
    """Validate and fix scale filter to ensure even dimensions for H.264/H.265 compatibility.

    H.264 and H.265 codecs require even dimensions for proper encoding.
    This function ensures scale filters produce even width and height values.

    Args:
        scale_filter: The scale filter string (e.g., "scale=iw*9/16:ih")

    Returns:
        Fixed scale filter that ensures even dimensions, or original if no fixes needed
    """
    if not scale_filter or not scale_filter.startswith("scale="):
        return scale_filter

    # Extract the scale parameters (remove "scale=" prefix)
    scale_params = scale_filter[6:]

    # Check if it's a simple width:height format
    if ":" in scale_params and not any(op in scale_params for op in ["*", "/", "+", "-"]):
        # Simple format like "1280:720" - ensure even numbers
        parts = scale_params.split(":")
        if len(parts) >= 2:
            try:
                width = int(parts[0])
                height = int(parts[1])
                # Make sure both dimensions are even for codec compatibility
                if width % 2 != 0:
                    width -= 1
                if height % 2 != 0:
                    height -= 1
                # Reconstruct the scale filter with additional parameters if any
                result = f"scale={width}:{height}"
                if len(parts) > 2:
                    result += ":" + ":".join(parts[2:])
                # Add force_original_aspect_ratio=decrease if not already present
                if "force_original_aspect_ratio" not in result:
                    result += ":force_original_aspect_ratio=decrease"
                return result
            except ValueError:
                # If parsing fails, return original filter
                pass

    # For aspect ratio changes that might result in odd dimensions,
    # use a more robust approach that ensures even dimensions
    if "9/16" in scale_params or "16/9" in scale_params:
        # For 9:16 aspect ratio conversions, use a safer approach
        if "ih*9/16:ih" in scale_params:
            # Instead of calculating width from height, calculate height from width
            # This is more likely to result in even dimensions
            return "scale=iw:iw*16/9:force_original_aspect_ratio=decrease"
        elif "iw*16/9:iw" in scale_params:
            # For 16:9 aspect ratio
            return "scale=iw:iw*9/16:force_original_aspect_ratio=decrease"

    # For other complex expressions, add force_original_aspect_ratio=decrease to help FFmpeg
    # handle dimension calculations more safely, but only if not already present
    if "force_original_aspect_ratio" not in scale_params:
        return f"scale={scale_params}:force_original_aspect_ratio=decrease"

    return scale_filter


def _validate_and_fix_filter_chain(filter_chain: list[str]) -> list[str]:
    """Validate and fix a chain of filters, ensuring proper handling of scale filters.

    Applies validation specifically to scale filters while preserving
    other filters without modification.

    Args:
        filter_chain: List of filter strings to validate

    Returns:
        Fixed filter chain with validated scale filters
    """
    validated_filters = []

    for filter_item in filter_chain:
        if filter_item.startswith("scale="):
            # Apply scale filter validation for even dimensions
            fixed_filter = _validate_and_fix_scale_filter(filter_item)
            if fixed_filter:
                validated_filters.append(fixed_filter)
        else:
            # For non-scale filters, don't add force_original_aspect_ratio=decrease
            # as it's not supported by most filters
            validated_filters.append(filter_item)

    return validated_filters


def _derive_output_name(
    input_path: Path, intent: FfmpegIntent, output_dir: Path | None = None
) -> Path:
    """Derive output filename based on intent and input file.

    Generates appropriate output filenames based on the action type,
    ensuring descriptive names that avoid overwriting input files.

    Args:
        input_path: Input file path
        intent: Parsed ffmpeg intent
        output_dir: Output directory path (optional, defaults to input directory)

    Returns:
        Output file path with appropriate name and extension
    """
    if intent.output and intent.output != input_path:
        # If output is specified, use it but potentially move to output directory
        if output_dir:
            return output_dir / intent.output.name
        return intent.output

    stem = input_path.stem
    suffix = input_path.suffix

    # Determine output directory
    target_dir = output_dir if output_dir else input_path.parent

    # Generate action-specific output names
    if intent.action == Action.extract_audio:
        return target_dir / f"{stem}.mp3"
    if intent.action == Action.thumbnail:
        return target_dir / "thumbnail.png"
    if intent.action == Action.frames:
        return target_dir / f"{stem}_frame_%04d.png"
    if intent.action == Action.extract_frames:
        return target_dir / f"{stem}_frames_%04d.png"
    if intent.action == Action.trim:
        return target_dir / "clip.mp4"
    if intent.action == Action.remove_audio:
        return target_dir / f"{stem}_mute.mp4"
    if intent.action == Action.overlay:
        return target_dir / f"{stem}_overlay.mp4"
    if intent.action in {Action.convert, Action.compress}:
        # Generate a descriptive output name to avoid overwriting input
        return target_dir / f"{stem}_converted.mp4"
    if intent.action == Action.format_convert:
        # Use the format from the intent to determine the extension
        if intent.format:
            # Map common formats to extensions
            format_extensions = {
                "webm": ".webm",
                "avi": ".avi",
                "mkv": ".mkv",
                "mov": ".mov",
                "mp4": ".mp4",
            }
            extension = format_extensions.get(intent.format, f".{intent.format}")
            return target_dir / f"{stem}{extension}"
        return target_dir / f"{stem}{suffix}"
    return target_dir / f"{stem}{suffix}"


def route_intent(
    intent: FfmpegIntent, allowed_dirs: list[Path] | None = None, output_dir: Path | None = None
) -> CommandPlan:
    """Route FfmpegIntent to CommandPlan with security validation.

    Converts a parsed intent into an executable command plan, including
    security validation, glob expansion, and command argument generation.

    Args:
        intent: Parsed user intent to route
        allowed_dirs: List of allowed directories for file operations
        output_dir: Output directory for generated files (optional)

    Returns:
        CommandPlan: Execution plan with validated commands

    Raises:
        BuildError: If intent cannot be routed or contains unsafe operations
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
    from .file_operations import is_safe_path

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
        output = _derive_output_name(inp, intent, output_dir)
        args: list[str] = []

        if intent.action == Action.convert:
            # Collect all filters to combine into a single -vf flag
            all_filters = []

            if intent.scale:
                # Validate and fix scale filter to ensure even dimensions
                fixed_scale = _validate_and_fix_scale_filter(f"scale={intent.scale}")
                if fixed_scale:
                    all_filters.append(fixed_scale)

            if intent.filters:
                # Validate all filters in the filters list
                validated_filters = _validate_and_fix_filter_chain(intent.filters)
                all_filters.extend(validated_filters)

            # Remove duplicate scale filters (keep the last one)
            scale_filters = [f for f in all_filters if f.startswith("scale=")]
            non_scale_filters = [f for f in all_filters if not f.startswith("scale=")]

            # If there are multiple scale filters, keep only the last one
            if len(scale_filters) > 1:
                scale_filters = [scale_filters[-1]]

            # Reconstruct the filter chain
            final_filters = non_scale_filters + scale_filters

            # Add single -vf flag with all filters combined
            if final_filters:
                filter_str = ",".join(final_filters)
                args.extend(["-vf", filter_str])

            if intent.video_codec:
                args.extend(["-c:v", intent.video_codec])
            if intent.audio_codec:
                args.extend(["-c:a", intent.audio_codec])
        elif intent.action == Action.extract_audio:
            # Extract audio with high quality settings
            args.extend(["-q:a", "0", "-map", "a"])
        elif intent.action == Action.remove_audio:
            # Remove audio track
            args.extend(["-an"])
            if intent.video_codec:
                args.extend(["-c:v", intent.video_codec])
        elif intent.action == Action.trim:
            # Handle trimming with start/end/duration
            if intent.start:
                args.extend(["-ss", intent.start])
            # If end is provided, prefer -to; otherwise use duration if present
            if intent.end:
                args.extend(["-to", intent.end])
            elif intent.duration is not None:
                args.extend(["-t", str(intent.duration)])
        elif intent.action == Action.segment:
            # Simplified segmenting: use start/end if provided, else duration
            if intent.start:
                args.extend(["-ss", intent.start])
            if intent.end:
                args.extend(["-to", intent.end])
            elif intent.duration is not None:
                args.extend(["-t", str(intent.duration)])
        elif intent.action == Action.thumbnail:
            # Extract single frame for thumbnail
            if intent.start:
                args.extend(["-ss", intent.start])
            args.extend(["-vframes", "1"])
        elif intent.action == Action.frames:
            # Extract frames with specified FPS
            if intent.fps:
                args.extend(["-vf", f"fps={intent.fps}"])
        elif intent.action == Action.compress:
            # Apply compression settings with defaults
            if intent.crf is not None:
                args.extend(["-crf", str(intent.crf)])
            if intent.video_codec:
                args.extend(["-c:v", intent.video_codec])
            if intent.audio_codec:
                args.extend(["-c:a", intent.audio_codec])
        elif intent.action == Action.overlay:
            # Handle overlay operations with additional input
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
        elif intent.action == Action.format_convert:
            # Handle format conversion with specific codecs
            if intent.format:
                args.extend(["-f", intent.format])
            if intent.video_codec:
                args.extend(["-c:v", intent.video_codec])
            if intent.audio_codec:
                args.extend(["-c:a", intent.audio_codec])
        elif intent.action == Action.extract_frames:
            # Handle frame extraction with FPS
            if intent.fps:
                args.extend(["-vf", f"fps={intent.fps}"])
            else:
                # Default to 1 frame per 5 seconds
                args.extend(["-vf", "fps=1/5"])
            # Add frame_pts for better frame naming
            args.extend(["-frame_pts", "1"])
        else:
            raise BuildError(
                f"Unsupported action: {intent.action}. "
                f"Supported actions are: convert, extract_audio, remove_audio, "
                f"trim, segment, thumbnail, frames, compress, overlay, format_convert, extract_frames. "
                f"Please rephrase your request using supported operations."
            )

        entries.append(CommandEntry(input=inp, output=output, args=args))

    summary = _build_summary(intent, entries)
    return CommandPlan(summary=summary, entries=entries)


def _build_summary(intent: FfmpegIntent, entries: list[CommandEntry]) -> str:
    """Build a human-readable summary of the command plan.

    Creates a descriptive summary of what the command plan will do,
    including action type, file count, and key parameters.

    Args:
        intent: The parsed intent
        entries: List of command entries in the plan

    Returns:
        Human-readable summary string
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
    if intent.action == Action.format_convert:
        format_info = f"format={intent.format}" if intent.format else "default format"
        video_info = f"video={intent.video_codec}" if intent.video_codec else "default video"
        audio_info = f"audio={intent.audio_codec}" if intent.audio_codec else "default audio"
        return f"Convert {len(entries)} file(s) to {format_info} with {video_info} and {audio_info}"
    if intent.action == Action.extract_frames:
        fps_info = f"fps={intent.fps}" if intent.fps else "fps=1/5"
        return f"Extract frames from {len(entries)} file(s) with {fps_info}"
    return f"Action {intent.action} on {len(entries)} file(s)"
