"""Command execution module for ai-ffmpeg-cli.

This module handles the execution of ffmpeg commands with comprehensive
safety checks, user confirmation, and error handling. It provides both
preview and execution modes with proper validation.

Key features:
- Command preview with formatted table display
- Overwrite protection with user confirmation
- Comprehensive security validation
- Detailed error reporting and guidance
- Support for dry-run mode
- Executable availability checking

Security measures:
- Command validation before execution
- Executable path verification
- Subprocess execution without shell
- Comprehensive error handling
"""

from __future__ import annotations

import logging
import shutil
import subprocess  # nosec B404: subprocess used with explicit list args, no shell
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .confirm import confirm_prompt
from .errors import ExecError

logger = logging.getLogger(__name__)


def _format_command(cmd: list[str]) -> str:
    """Format command list as readable string for display.

    Args:
        cmd: Command arguments list

    Returns:
        str: Space-separated command string for display
    """
    return " ".join(cmd)


def _extract_output_path(cmd: list[str]) -> Path | None:
    """Extract the output file path from an ffmpeg command.

    Parses the command to find the output file path, which is typically
    the last argument in ffmpeg commands.

    Args:
        cmd: ffmpeg command arguments list

    Returns:
        Path: Output file path, or None if not found
    """
    if len(cmd) < 2:
        return None
    # Output file is typically the last argument in ffmpeg commands
    return Path(cmd[-1])


def _check_overwrite_protection(commands: list[list[str]], assume_yes: bool = False) -> bool:
    """Check for existing output files and prompt for overwrite confirmation.

    Scans all commands for existing output files and prompts the user
    for confirmation before overwriting. Provides clear feedback about
    which files will be affected.

    Args:
        commands: List of ffmpeg command argument lists
        assume_yes: Whether to skip confirmation and assume yes

    Returns:
        bool: True if operation should proceed, False if cancelled
    """
    existing_files = []

    # Scan all commands for existing output files
    for cmd in commands:
        output_path = _extract_output_path(cmd)
        if output_path and output_path.exists():
            existing_files.append(output_path)

    if not existing_files:
        return True  # No conflicts, proceed

    if assume_yes:
        return True  # Skip confirmation

    # Show which files would be overwritten
    console = Console()
    console.print(
        "\n[yellow]Warning: The following files already exist and will be overwritten:[/yellow]"
    )
    for file_path in existing_files:
        console.print(f"  • {file_path}")
    console.print()

    return confirm_prompt(
        "Continue and overwrite these files?", default_yes=False, assume_yes=assume_yes
    )


def preview(commands: list[list[str]]) -> None:
    """Display a formatted preview of planned ffmpeg commands.

    Creates a rich table showing all commands that would be executed,
    numbered for easy reference.

    Args:
        commands: List of ffmpeg command argument lists to preview
    """
    console = Console()
    table = Table(title="Planned ffmpeg Commands")
    table.add_column("#", justify="right")
    table.add_column("Command", overflow="fold")

    for idx, cmd in enumerate(commands, start=1):
        table.add_row(str(idx), _format_command(cmd))

    console.print(table)


def run(
    commands: list[list[str]],
    confirm: bool,
    dry_run: bool,
    show_preview: bool = True,
    assume_yes: bool = False,
) -> int:
    """Execute ffmpeg commands with comprehensive safety checks.

    Main execution function that handles command validation, user confirmation,
    and actual execution with detailed error reporting.

    Args:
        commands: List of ffmpeg command argument lists to execute
        confirm: Whether to require user confirmation before execution
        dry_run: Whether to only preview commands without execution
        show_preview: Whether to display command preview
        assume_yes: Whether to skip confirmation prompts

    Returns:
        int: Exit code (0 for success, 1 for failure)

    Raises:
        ExecError: For execution failures, missing executables, or validation errors
    """
    if show_preview:
        preview(commands)
    if dry_run:
        return 0
    if not confirm:
        return 0

    # Check for overwrite conflicts before execution
    if not _check_overwrite_protection(commands, assume_yes):
        logger.info("Operation cancelled by user due to file conflicts")
        return 1

    # Execute each command with comprehensive validation
    for cmd in commands:
        # Validate command is not empty
        if not cmd:
            raise ExecError("Empty command received for execution.")

        # Validate executable exists to avoid PATH surprises
        ffmpeg_exec = cmd[0]
        resolved = shutil.which(ffmpeg_exec)
        if resolved is None:
            raise ExecError(
                f"Executable not found: {ffmpeg_exec}. Ensure it is installed and on PATH."
            )

        # Final security validation of the command
        from .io_utils import validate_ffmpeg_command

        if not validate_ffmpeg_command(cmd):
            logger.error(f"Command failed security validation: {' '.join(cmd[:3])}...")
            raise ExecError(
                "Command failed security validation. This could be due to: "
                "(1) unsafe file paths or arguments, "
                "(2) unsupported ffmpeg flags, "
                "or (3) potential security risks. "
                "Please check your input and try a simpler operation."
            )

        # Execute the command with comprehensive error handling
        try:
            result = subprocess.run(cmd, check=True)  # nosec B603: fixed binary, no shell, args vetted
            if result.returncode != 0:
                raise ExecError(
                    f"ffmpeg command failed with exit code {result.returncode}. "
                    f"Common causes: (1) input file not found or corrupted, "
                    f"(2) invalid output format or codec, "
                    f"(3) insufficient disk space, "
                    f"(4) permission issues. Check file paths and try again."
                )
        except subprocess.CalledProcessError as exc:
            logger.error("ffmpeg execution failed: %s", exc)
            raise ExecError(
                f"ffmpeg execution failed with error: {exc}. "
                f"Please verify: (1) input files exist and are readable, "
                f"(2) output directory is writable, "
                f"(3) ffmpeg is properly installed (try 'ffmpeg -version'), "
                f"(4) file formats are supported. "
                f"Use --verbose for detailed logging."
            ) from exc
    return 0
