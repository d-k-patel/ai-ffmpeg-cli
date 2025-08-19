"""Command builder for ai-ffmpeg-cli.

This module translates CommandPlan objects into executable ffmpeg command lists.
It handles argument ordering, applies action-specific defaults, and ensures
commands are properly structured for ffmpeg execution.

Key features:
- Argument ordering optimization (pre/post input flags)
- Action-specific default codec and filter application
- Command validation before execution
- Support for multiple input files (overlay operations)
- Deterministic command generation

Command structure:
- Pre-input flags (seeking, duration limits)
- Input files (-i arguments)
- Post-input flags (codecs, filters, quality settings)
- Output file
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .nl_schema import CommandPlan

logger = logging.getLogger(__name__)


def build_commands(plan: CommandPlan, assume_yes: bool = False) -> list[list[str]]:
    """Build executable ffmpeg commands from a command plan.

    Converts CommandPlan entries into properly structured ffmpeg command lists.
    Handles argument ordering, applies defaults, and validates commands.

    Args:
        plan: CommandPlan containing entries to convert
        assume_yes: Whether to add -y flag to overwrite output files

    Returns:
        List of ffmpeg command argument lists ready for subprocess execution

    Note:
        Commands are validated using validate_ffmpeg_command before being returned.
        Invalid commands are logged as warnings but still included in the result.
    """
    commands: list[list[str]] = []
    for entry in plan.entries:
        cmd: list[str] = ["ffmpeg"]
        if assume_yes:
            cmd.append("-y")

        # Split args into pre/post by presence of -ss/-t/-to which are often pre-input
        # This optimization allows ffmpeg to seek more efficiently
        pre_input_flags: list[str] = []
        post_input_flags: list[str] = []

        # Keep order stable - split args into pre/post buckets
        # Process args in pairs (flag + value) for proper handling
        for i in range(0, len(entry.args), 2):
            flag = entry.args[i]
            val = entry.args[i + 1] if i + 1 < len(entry.args) else None
            # Seeking flags work better before input for performance
            bucket = pre_input_flags if flag in {"-ss", "-t", "-to"} else post_input_flags
            bucket.append(flag)
            if val is not None:
                bucket.append(val)

        # Build command in proper ffmpeg order
        cmd.extend(pre_input_flags)
        cmd.extend(["-i", str(entry.input)])
        # Add extra inputs for operations like overlay
        for extra in entry.extra_inputs:
            cmd.extend(["-i", str(extra)])

        # Add post-input flags from the plan entry
        cmd.extend(post_input_flags)

        # Apply action-specific defaults based on plan summary
        # This is more deterministic than complex heuristics
        summary = plan.summary.lower()
        existing_args_str = " ".join(entry.args)

        # Only apply defaults if not already specified to avoid conflicts
        if "convert" in summary:
            if "-c:v" not in existing_args_str:
                cmd.extend(["-c:v", "libx264"])
            if "-c:a" not in existing_args_str:
                cmd.extend(["-c:a", "aac"])
        elif "compress" in summary:
            # For compression, ensure codec comes before CRF for proper ordering
            if "-c:v" not in existing_args_str:
                # Insert codec before any existing CRF values
                crf_index = -1
                for i, arg in enumerate(cmd):
                    if arg == "-crf":
                        crf_index = i
                        break
                if crf_index >= 0:
                    cmd.insert(crf_index, "libx265")
                    cmd.insert(crf_index, "-c:v")
                else:
                    cmd.extend(["-c:v", "libx265"])
            if "-crf" not in existing_args_str:
                cmd.extend(["-crf", "28"])
        elif "frames" in summary and "fps=" not in existing_args_str:
            cmd.extend(["-vf", "fps=1/5"])
        elif "thumbnail" in summary and "-vframes" not in existing_args_str:
            cmd.extend(["-vframes", "1"])
        elif "overlay" in summary and "-filter_complex" not in existing_args_str:
            cmd.extend(["-filter_complex", "overlay=W-w-10:10"])
        elif ("trim" in summary or "segment" in summary) and not any(
            token in existing_args_str for token in ["-c:v", "-c:a", "-filter", "-vf", "-af"]
        ):
            # Use copy mode for simple trim/segment operations (fast, no re-encoding)
            cmd.extend(["-c", "copy"])

        cmd.append(str(entry.output))

        # Validate the command before adding it to ensure security
        from .io_utils import validate_ffmpeg_command

        if not validate_ffmpeg_command(cmd):
            logger.warning(f"Generated command failed validation: {' '.join(cmd[:5])}...")

        commands.append(cmd)

    return commands
